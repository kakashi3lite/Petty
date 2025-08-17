#!/usr/bin/env python3
"""
Privacy Export Tool for Petty - User Data Ownership Demonstration

This script allows users to export their telemetry data from S3 storage,
demonstrating transparent data ownership and GDPR compliance.

Usage:
    python tools/export_telemetry.py --user-id USER_123 --output-dir ./exports
    python tools/export_telemetry.py --list-users
    python tools/export_telemetry.py --user-id USER_123 --format csv
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class TelemetryExporter:
    """Exports user telemetry data from S3 with privacy controls."""
    
    def __init__(
        self,
        bucket_name: str,
        aws_profile: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize S3 client
        session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self.s3_client = session.client('s3', endpoint_url=endpoint_url)
        
    def list_users(self) -> List[str]:
        """List all user IDs that have telemetry data."""
        users = set()
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix='telemetry/'):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    # Extract user ID from key pattern: telemetry/user_id/...
                    key_parts = obj['Key'].split('/')
                    if len(key_parts) >= 2 and key_parts[0] == 'telemetry':
                        users.add(key_parts[1])
                        
        except ClientError as e:
            self.logger.error(f"Failed to list users: {e}")
            raise
            
        return sorted(list(users))
    
    def get_user_objects(self, user_id: str) -> List[Dict]:
        """Get all telemetry objects for a specific user."""
        objects = []
        prefix = f'telemetry/{user_id}/'
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"')
                    })
                    
        except ClientError as e:
            self.logger.error(f"Failed to list objects for user {user_id}: {e}")
            raise
            
        return objects
    
    def export_user_data(
        self,
        user_id: str,
        output_dir: Path,
        format_type: str = 'jsonl'
    ) -> Dict[str, Union[int, str]]:
        """Export all telemetry data for a user to local files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        objects = self.get_user_objects(user_id)
        if not objects:
            self.logger.warning(f"No telemetry data found for user: {user_id}")
            return {'exported_count': 0, 'total_size': 0, 'output_path': str(output_dir)}
        
        exported_count = 0
        total_size = 0
        
        if format_type == 'jsonl':
            output_file = output_dir / f'{user_id}_telemetry.jsonl'
            exported_count, total_size = self._export_jsonl(user_id, objects, output_file)
        elif format_type == 'csv':
            output_file = output_dir / f'{user_id}_telemetry.csv'
            exported_count, total_size = self._export_csv(user_id, objects, output_file)
        elif format_type == 'json':
            output_file = output_dir / f'{user_id}_telemetry.json'
            exported_count, total_size = self._export_json(user_id, objects, output_file)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Create metadata file
        metadata = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'exported_objects': exported_count,
            'total_size_bytes': total_size,
            'format': format_type,
            'source_bucket': self.bucket_name,
            'objects': objects
        }
        
        metadata_file = output_dir / f'{user_id}_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Exported {exported_count} objects ({total_size} bytes) for user {user_id}")
        return {
            'exported_count': exported_count,
            'total_size': total_size,
            'output_path': str(output_file),
            'metadata_path': str(metadata_file)
        }
    
    def _export_jsonl(self, user_id: str, objects: List[Dict], output_file: Path) -> tuple[int, int]:
        """Export data in JSON Lines format."""
        exported_count = 0
        total_size = 0
        
        with open(output_file, 'w') as f:
            for obj in objects:
                try:
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['key'])
                    content = response['Body'].read()
                    
                    # Try to parse as JSON, fall back to raw content
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = {
                            'raw_content': content.decode('utf-8', errors='replace'),
                            'content_type': response.get('ContentType', 'unknown')
                        }
                    
                    # Add metadata
                    data['_export_metadata'] = {
                        'source_key': obj['key'],
                        'size': obj['size'],
                        'last_modified': obj['last_modified'],
                        'etag': obj['etag']
                    }
                    
                    f.write(json.dumps(data) + '\n')
                    exported_count += 1
                    total_size += obj['size']
                    
                except ClientError as e:
                    self.logger.warning(f"Failed to download {obj['key']}: {e}")
                    continue
        
        return exported_count, total_size
    
    def _export_csv(self, user_id: str, objects: List[Dict], output_file: Path) -> tuple[int, int]:
        """Export data in CSV format (for structured telemetry data)."""
        import csv
        
        exported_count = 0
        total_size = 0
        csv_rows = []
        headers = set()
        
        # First pass: collect all data and determine headers
        for obj in objects:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['key'])
                content = response['Body'].read()
                
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        headers.update(data.keys())
                        data['_source_key'] = obj['key']
                        data['_last_modified'] = obj['last_modified']
                        csv_rows.append(data)
                        exported_count += 1
                        total_size += obj['size']
                except json.JSONDecodeError:
                    # Skip non-JSON data for CSV export
                    continue
                    
            except ClientError as e:
                self.logger.warning(f"Failed to download {obj['key']}: {e}")
                continue
        
        # Write CSV file
        if csv_rows:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(headers))
                writer.writeheader()
                writer.writerows(csv_rows)
        
        return exported_count, total_size
    
    def _export_json(self, user_id: str, objects: List[Dict], output_file: Path) -> tuple[int, int]:
        """Export data as a single JSON array."""
        exported_count = 0
        total_size = 0
        all_data = []
        
        for obj in objects:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['key'])
                content = response['Body'].read()
                
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {
                        'raw_content': content.decode('utf-8', errors='replace'),
                        'content_type': response.get('ContentType', 'unknown')
                    }
                
                data['_export_metadata'] = {
                    'source_key': obj['key'],
                    'size': obj['size'],
                    'last_modified': obj['last_modified'],
                    'etag': obj['etag']
                }
                
                all_data.append(data)
                exported_count += 1
                total_size += obj['size']
                
            except ClientError as e:
                self.logger.warning(f"Failed to download {obj['key']}: {e}")
                continue
        
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        return exported_count, total_size


def main():
    parser = argparse.ArgumentParser(
        description='Export user telemetry data from Petty S3 storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--bucket-name', '-b',
        default=os.getenv('PETTY_S3_BUCKET', 'petty-telemetry-bucket'),
        help='S3 bucket name (default: %(default)s)'
    )
    
    parser.add_argument(
        '--aws-profile', '-p',
        help='AWS profile to use'
    )
    
    parser.add_argument(
        '--endpoint-url', '-e',
        help='S3 endpoint URL (for local development)'
    )
    
    parser.add_argument(
        '--user-id', '-u',
        help='User ID to export data for'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path('./exports'),
        help='Output directory for exported files (default: %(default)s)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['jsonl', 'csv', 'json'],
        default='jsonl',
        help='Export format (default: %(default)s)'
    )
    
    parser.add_argument(
        '--list-users', '-l',
        action='store_true',
        help='List all user IDs with telemetry data'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        exporter = TelemetryExporter(
            bucket_name=args.bucket_name,
            aws_profile=args.aws_profile,
            endpoint_url=args.endpoint_url
        )
        
        if args.list_users:
            users = exporter.list_users()
            if users:
                print("Users with telemetry data:")
                for user in users:
                    print(f"  - {user}")
            else:
                print("No users found with telemetry data")
            return 0
        
        if not args.user_id:
            print("Error: --user-id is required (or use --list-users)", file=sys.stderr)
            return 1
        
        result = exporter.export_user_data(
            user_id=args.user_id,
            output_dir=args.output_dir,
            format_type=args.format
        )
        
        print(f"✅ Export completed successfully!")
        print(f"   Exported: {result['exported_count']} objects ({result['total_size']} bytes)")
        print(f"   Output: {result['output_path']}")
        print(f"   Metadata: {result['metadata_path']}")
        
        return 0
        
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your credentials.", file=sys.stderr)
        return 1
    except ClientError as e:
        print(f"Error: AWS operation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())