#!/usr/bin/env python3
"""
DSAR Telemetry Export Tool

This tool exports user telemetry data in compliance with GDPR Article 15 (Right of Access)
and Article 20 (Right to Data Portability). It creates signed bundles with manifest files
for secure data delivery.

Features:
- Secure data export with cryptographic signing
- Manifest generation with checksums
- Differential privacy protection for aggregated data
- Audit trail generation
- Support for multiple export formats (JSON, CSV)
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from common.security.crypto_utils import generate_secure_token
    from common.observability.logger import setup_structured_logging
except ImportError as e:
    print(f"Warning: Could not import all modules: {e}")
    print("Running in standalone mode with limited functionality")
    
    # Fallback implementations
    def generate_secure_token(length=16):
        import secrets
        return secrets.token_hex(length)
    
    def setup_structured_logging(*args, **kwargs):
        import logging
        return logging.getLogger()


class DSARExporter:
    """
    DSAR Export Manager for secure telemetry data export
    """

    def __init__(self, signing_key: str | None = None):
        """Initialize the DSAR exporter with optional signing key"""
        self.signing_key = signing_key or os.getenv("DSAR_SIGNING_KEY") or generate_secure_token(64)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Setup structured logger for audit trail"""
        try:
            return setup_structured_logging("dsar-exporter", level="INFO")
        except Exception:
            # Fallback logging with structured info method
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger("dsar-exporter")

            # Store original info method to avoid recursion
            original_info = logger.info

            # Add structured logging method for compatibility
            def structured_info(message, **kwargs):
                extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
                original_info(f"{message} {extra_info}")

            logger.info = structured_info
            return logger

    def _sign_data(self, data: str) -> str:
        """Generate HMAC signature for data integrity"""
        return hmac.new(
            self.signing_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _calculate_checksum(self, data: str | bytes) -> str:
        """Calculate SHA-256 checksum for data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def _apply_differential_privacy(self, data: dict[str, Any], epsilon: float = 1.0) -> dict[str, Any]:
        """
        Apply differential privacy to aggregated data
        
        This is a simplified implementation. In production, use proper DP libraries.
        """
        import random

        protected_data = data.copy()

        # Add noise to numerical values
        for key, value in protected_data.items():
            if isinstance(value, int | float) and key in ['total_steps', 'avg_heart_rate', 'activity_duration']:
                # Laplace noise for differential privacy
                noise = random.laplace(0, 1/epsilon)
                protected_data[key] = max(0, value + noise)

        return protected_data

    def create_export_manifest(self, export_data: dict[str, Any], request_id: str) -> dict[str, Any]:
        """Create a manifest file for the export bundle"""
        export_json = json.dumps(export_data, sort_keys=True, separators=(',', ':'))

        manifest = {
            "manifest_version": "1.0",
            "request_id": request_id,
            "created_at": datetime.now(UTC).isoformat(),
            "export_type": "dsar_telemetry",
            "data_subjects": export_data.get("user_ids", []),
            "retention_policy": {
                "expires_at": None,  # Set by caller based on retention policy
                "auto_delete": False
            },
            "privacy_protection": {
                "differential_privacy_applied": True,
                "epsilon_budget_used": export_data.get("dp_epsilon", 1.0),
                "anonymization_level": "aggregated"
            },
            "data_integrity": {
                "checksum": self._calculate_checksum(export_json),
                "signature": self._sign_data(export_json),
                "algorithm": "HMAC-SHA256"
            },
            "export_metadata": {
                "total_records": export_data.get("total_records", 0),
                "date_range": export_data.get("date_range", {}),
                "data_types": export_data.get("data_types", []),
                "format_version": "1.0"
            }
        }

        return manifest

    def export_user_telemetry(
        self,
        user_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        include_raw: bool = False,
        apply_dp: bool = True
    ) -> dict[str, Any]:
        """
        Export telemetry data for a specific user
        
        Args:
            user_id: User identifier
            start_date: ISO format start date (optional)
            end_date: ISO format end date (optional)
            include_raw: Whether to include raw sensor data
            apply_dp: Whether to apply differential privacy
        """
        request_id = generate_secure_token(16)

        self.logger.info(
            "Starting DSAR export",
            user_id=user_id,
            request_id=request_id,
            include_raw=include_raw,
            apply_dp=apply_dp
        )

        # Mock data structure - in production, this would query actual databases
        export_data = {
            "user_ids": [user_id],
            "request_id": request_id,
            "export_timestamp": datetime.now(UTC).isoformat(),
            "date_range": {
                "start": start_date or "2023-01-01T00:00:00Z",
                "end": end_date or datetime.now(UTC).isoformat()
            },
            "data_types": ["behavioral_events", "sensor_metrics", "location_data"],
            "total_records": 1250,  # Mock count
            "dp_epsilon": 1.0 if apply_dp else None,
            "data": {
                "behavioral_events": [
                    {
                        "event_id": f"evt_{i:04d}",
                        "timestamp": f"2024-01-{(i%28)+1:02d}T{(i%24):02d}:00:00Z",
                        "event_type": ["resting", "playing", "walking"][i % 3],
                        "confidence": 0.85 + (i % 10) * 0.01,
                        "location": {"lat": 37.7749, "lng": -122.4194},
                        "duration_minutes": 15 + (i % 30)
                    }
                    for i in range(10)  # Mock data
                ],
                "sensor_metrics": {
                    "heart_rate": {
                        "avg": 75.2,
                        "min": 65,
                        "max": 95,
                        "readings_count": 2400
                    },
                    "activity_level": {
                        "daily_steps": 8500,
                        "active_minutes": 120,
                        "calories_burned": 450
                    }
                },
                "privacy_summary": {
                    "data_retention_days": 730,
                    "anonymization_applied": apply_dp,
                    "third_party_sharing": False
                }
            }
        }

        # Apply differential privacy if requested
        if apply_dp:
            export_data["data"]["sensor_metrics"] = self._apply_differential_privacy(
                export_data["data"]["sensor_metrics"]
            )

        self.logger.info(
            "DSAR export completed",
            user_id=user_id,
            request_id=request_id,
            total_records=export_data["total_records"]
        )

        return export_data

    def create_signed_bundle(
        self,
        export_data: dict[str, Any],
        output_path: str | None = None
    ) -> str:
        """
        Create a signed ZIP bundle containing export data and manifest
        
        Returns:
            Path to the created bundle
        """
        request_id = export_data.get("request_id", generate_secure_token(16))

        if output_path is None:
            output_path = f"/tmp/dsar_export_{request_id}.zip"

        # Create manifest
        manifest = self.create_export_manifest(export_data, request_id)

        # Create signed bundle
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add data file
            data_json = json.dumps(export_data, indent=2, sort_keys=True)
            zipf.writestr("telemetry_data.json", data_json)

            # Add manifest
            manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
            zipf.writestr("manifest.json", manifest_json)

            # Add README
            readme_content = self._generate_readme(export_data, manifest)
            zipf.writestr("README.txt", readme_content)

        self.logger.info(
            "Signed bundle created",
            request_id=request_id,
            output_path=output_path,
            bundle_size=os.path.getsize(output_path)
        )

        return output_path

    def _generate_readme(self, export_data: dict[str, Any], manifest: dict[str, Any]) -> str:
        """Generate a README file for the export bundle"""
        return f"""
PETTY DSAR DATA EXPORT
======================

Request ID: {manifest['request_id']}
Created: {manifest['created_at']}
Export Type: {manifest['export_type']}

CONTENTS
--------
- telemetry_data.json: Your pet telemetry data
- manifest.json: Export metadata and integrity information
- README.txt: This file

DATA SUMMARY
------------
Total Records: {export_data.get('total_records', 0)}
Date Range: {export_data.get('date_range', {}).get('start')} to {export_data.get('date_range', {}).get('end')}
Data Types: {', '.join(export_data.get('data_types', []))}

PRIVACY PROTECTION
------------------
Differential Privacy: {'Applied' if manifest.get('privacy_protection', {}).get('differential_privacy_applied') else 'Not Applied'}
Anonymization Level: {manifest.get('privacy_protection', {}).get('anonymization_level', 'None')}

DATA INTEGRITY
--------------
Checksum (SHA-256): {manifest['data_integrity']['checksum']}
Signature (HMAC-SHA256): {manifest['data_integrity']['signature']}

To verify data integrity, you can:
1. Calculate SHA-256 hash of telemetry_data.json
2. Compare with the checksum in manifest.json

For support or questions about this export, contact: privacy@petty.ai
"""


def main():
    """Command line interface for DSAR export tool"""
    parser = argparse.ArgumentParser(description="DSAR Telemetry Export Tool")
    parser.add_argument("--user-id", required=True, help="User ID to export data for")
    parser.add_argument("--start-date", help="Start date (ISO format)")
    parser.add_argument("--end-date", help="End date (ISO format)")
    parser.add_argument("--output", "-o", help="Output bundle path")
    parser.add_argument("--include-raw", action="store_true", help="Include raw sensor data")
    parser.add_argument("--no-dp", action="store_true", help="Disable differential privacy")
    parser.add_argument("--signing-key", help="HMAC signing key")

    args = parser.parse_args()

    # Initialize exporter
    exporter = DSARExporter(signing_key=args.signing_key)

    try:
        # Export user data
        export_data = exporter.export_user_telemetry(
            user_id=args.user_id,
            start_date=args.start_date,
            end_date=args.end_date,
            include_raw=args.include_raw,
            apply_dp=not args.no_dp
        )

        # Create signed bundle
        bundle_path = exporter.create_signed_bundle(export_data, args.output)

        print("DSAR export completed successfully")
        print(f"Bundle created: {bundle_path}")
        print(f"Request ID: {export_data['request_id']}")

    except Exception as e:
        print(f"Error during DSAR export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
