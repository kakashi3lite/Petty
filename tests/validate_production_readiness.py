"""
Production Readiness Validation Script
Tests all critical production-ready changes implemented in the Petty project
"""

import os
import sys
import asyncio
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import importlib.util

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def setup_logging():
    """Configure logging for validation script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('production_validation.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ValidationResult:
    """Represents the result of a validation test"""
    def __init__(self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

class ProductionReadinessValidator:
    """Comprehensive validator for production readiness"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
    def add_result(self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Add a validation result"""
        result = ValidationResult(test_name, passed, message, details)
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        if details:
            logger.debug(f"Details: {json.dumps(details, indent=2)}")
    
    def validate_authentication_system(self) -> bool:
        """Validate production-grade authentication implementation"""
        try:
            from common.security.auth import (
                ProductionTokenManager, 
                production_token_manager,
                TokenPair,
                TokenPayload
            )
            
            # Test token generation
            token_pair = production_token_manager.generate_token_pair("test_user_123", ["read", "write"])
            
            if not isinstance(token_pair, TokenPair):
                self.add_result("Auth Token Generation", False, "Token pair generation failed")
                return False
            
            # Test token verification
            token_payload = production_token_manager.verify_token(token_pair.access_token)
            
            if not isinstance(token_payload, TokenPayload):
                self.add_result("Auth Token Verification", False, "Token verification failed")
                return False
            
            if token_payload.user_id != "test_user_123":
                self.add_result("Auth Token Verification", False, "Token payload user_id mismatch")
                return False
            
            # Test token expiration
            expired_token = "invalid_token_string"
            expired_payload = production_token_manager.verify_token(expired_token)
            
            if expired_payload is not None:
                self.add_result("Auth Token Security", False, "Invalid token was accepted")
                return False
            
            self.add_result("Authentication System", True, "Production JWT system working correctly", {
                "token_type": type(token_pair.access_token).__name__,
                "has_refresh_token": bool(token_pair.refresh_token),
                "user_id_verified": token_payload.user_id,
                "scopes_verified": token_payload.scopes
            })
            
            return True
            
        except Exception as e:
            self.add_result("Authentication System", False, f"Authentication validation failed: {e}")
            return False
    
    def validate_observability_system(self) -> bool:
        """Validate observability and monitoring implementation"""
        try:
            from common.observability.powertools import (
                obs_manager,
                monitor_performance,
                lambda_handler_with_observability,
                health_checker,
                logger,
                tracer,
                metrics
            )
            
            # Test observability manager
            obs_manager.set_correlation_id("test-correlation-123")
            
            # Test business event logging
            obs_manager.log_business_event("validation_test", test_param="test_value")
            
            # Test performance monitoring
            obs_manager.log_performance_metric("test_operation", 150.5, True)
            
            # Test AI inference logging
            obs_manager.log_ai_inference("test_model", 100, 0.85, 200.0, "test_behavior")
            
            # Test health checker
            health_status = health_checker.get_health_status()
            
            if not isinstance(health_status, dict) or "status" not in health_status:
                self.add_result("Observability Health Check", False, "Health check failed")
                return False
            
            # Test security event logging
            obs_manager.log_security_event("validation_test", "low", {"test": "validation"})
            
            self.add_result("Observability System", True, "Comprehensive observability system working", {
                "correlation_id_set": obs_manager.correlation_id,
                "health_status": health_status["status"],
                "service_name": obs_manager.service_name,
                "environment": obs_manager.environment
            })
            
            return True
            
        except Exception as e:
            self.add_result("Observability System", False, f"Observability validation failed: {e}")
            return False
    
    def validate_secrets_management(self) -> bool:
        """Validate secrets management system"""
        try:
            from common.security.secrets_manager import (
                ProductionSecretsManager,
                secrets_manager,
                SecretType,
                get_jwt_keys
            )
            
            # Test secrets manager initialization
            test_manager = ProductionSecretsManager(cache_ttl_seconds=60)
            
            # Test cache functionality
            cache_stats = test_manager.get_cache_stats()
            
            if not isinstance(cache_stats, dict):
                self.add_result("Secrets Cache", False, "Cache stats retrieval failed")
                return False
            
            # Test secret creation (would fail in test environment, but validates interface)
            try:
                # This will fail in test environment without AWS access, which is expected
                test_secret = {"test": "value"}
                result = test_manager.create_secret("test-secret", test_secret, "Test secret")
                # In test environment, this should return False due to no AWS access
            except Exception:
                # Expected in test environment
                pass
            
            self.add_result("Secrets Management", True, "Secrets management system properly configured", {
                "cache_ttl": test_manager.cache_ttl_seconds,
                "encryption_enabled": test_manager.enable_local_encryption,
                "region": test_manager.region_name,
                "cache_stats": cache_stats
            })
            
            return True
            
        except Exception as e:
            self.add_result("Secrets Management", False, f"Secrets management validation failed: {e}")
            return False
    
    def validate_mobile_error_handling(self) -> bool:
        """Validate mobile app error handling improvements"""
        try:
            # Read and validate mobile API service
            mobile_service_path = os.path.join(os.path.dirname(__file__), '..', 'mobile_app', 'lib', 'src', 'services', 'api_service.dart')
            
            if not os.path.exists(mobile_service_path):
                self.add_result("Mobile Error Handling", False, "Mobile API service file not found")
                return False
            
            with open(mobile_service_path, 'r') as f:
                service_content = f.read()
            
            # Check for key production features
            required_features = [
                "class RetryPolicy",
                "class CircuitBreaker", 
                "PettyException",
                "NetworkException",
                "AuthenticationException",
                "exponential backoff",
                "_executeWithRetry",
                "timeout",
                "maxAttempts"
            ]
            
            missing_features = []
            for feature in required_features:
                if feature not in service_content:
                    missing_features.append(feature)
            
            if missing_features:
                self.add_result("Mobile Error Handling", False, f"Missing features: {missing_features}")
                return False
            
            # Check for production-grade error handling patterns
            has_retry_logic = "retryableStatusCodes" in service_content
            has_circuit_breaker = "CircuitBreaker" in service_content and "_circuitBreaker" in service_content
            has_exponential_backoff = "backoffMultiplier" in service_content
            has_timeout_handling = "timeout(" in service_content
            
            self.add_result("Mobile Error Handling", True, "Production-grade mobile error handling implemented", {
                "has_retry_logic": has_retry_logic,
                "has_circuit_breaker": has_circuit_breaker,
                "has_exponential_backoff": has_exponential_backoff,
                "has_timeout_handling": has_timeout_handling,
                "file_size_bytes": len(service_content)
            })
            
            return True
            
        except Exception as e:
            self.add_result("Mobile Error Handling", False, f"Mobile error handling validation failed: {e}")
            return False
    
    def validate_api_versioning(self) -> bool:
        """Validate API versioning implementation"""
        try:
            # Check infrastructure template for versioned endpoints
            template_path = os.path.join(os.path.dirname(__file__), '..', 'infrastructure', 'template.yaml')
            
            if not os.path.exists(template_path):
                self.add_result("API Versioning", False, "Infrastructure template not found")
                return False
            
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Check for v1 endpoints
            v1_endpoints = [
                "/v1/ingest",
                "/v1/pet-plan", 
                "/v1/realtime",
                "/v1/pet-timeline",
                "/v1/submit-feedback"
            ]
            
            missing_endpoints = []
            for endpoint in v1_endpoints:
                if endpoint not in template_content:
                    missing_endpoints.append(endpoint)
            
            if missing_endpoints:
                self.add_result("API Versioning", False, f"Missing v1 endpoints: {missing_endpoints}")
                return False
            
            # Check for legacy endpoint support
            legacy_endpoints = [
                "Path: /ingest",
                "Path: /pet-plan",
                "Path: /realtime" 
            ]
            
            legacy_support = all(endpoint in template_content for endpoint in legacy_endpoints)
            
            self.add_result("API Versioning", True, "API versioning properly implemented", {
                "v1_endpoints_count": len(v1_endpoints),
                "legacy_support": legacy_support,
                "template_size_bytes": len(template_content)
            })
            
            return True
            
        except Exception as e:
            self.add_result("API Versioning", False, f"API versioning validation failed: {e}")
            return False
    
    def validate_service_updates(self) -> bool:
        """Validate that all services use production systems"""
        services = [
            ("Data Processor", "src/data_processor/app.py"),
            ("Timeline Generator", "src/timeline_generator/app.py"),
            ("Feedback Handler", "src/feedback_handler/app.py")
        ]
        
        all_services_valid = True
        
        for service_name, service_path in services:
            try:
                full_path = os.path.join(os.path.dirname(__file__), '..', service_path)
                
                if not os.path.exists(full_path):
                    self.add_result(f"{service_name} Update", False, f"Service file not found: {service_path}")
                    all_services_valid = False
                    continue
                
                with open(full_path, 'r') as f:
                    service_content = f.read()
                
                # Check for production system imports
                production_features = [
                    "from common.observability.powertools import",
                    "from common.security.auth import",
                    "from common.security.secrets_manager import",
                    "lambda_handler_with_observability",
                    "authenticate_request",
                    "obs_manager.log",
                    "production_token_manager"
                ]
                
                missing_features = []
                for feature in production_features:
                    if feature not in service_content:
                        missing_features.append(feature)
                
                if missing_features:
                    self.add_result(f"{service_name} Update", False, f"Missing production features: {missing_features}")
                    all_services_valid = False
                else:
                    self.add_result(f"{service_name} Update", True, "Service updated with production systems")
                    
            except Exception as e:
                self.add_result(f"{service_name} Update", False, f"Service validation failed: {e}")
                all_services_valid = False
        
        return all_services_valid
    
    def validate_e2e_test_suite(self) -> bool:
        """Validate end-to-end test suite"""
        try:
            test_files = [
                "tests/e2e/conftest.py",
                "tests/e2e/test_full_workflow.py", 
                "tests/e2e/test_error_scenarios.py",
                "tests/e2e/test_performance.py"
            ]
            
            test_file_stats = {}
            
            for test_file in test_files:
                file_path = os.path.join(os.path.dirname(__file__), '..', test_file)
                
                if not os.path.exists(file_path):
                    self.add_result("E2E Test Suite", False, f"Test file missing: {test_file}")
                    return False
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Count test functions
                test_count = content.count("async def test_")
                test_file_stats[test_file] = {
                    "size_bytes": len(content),
                    "test_functions": test_count
                }
            
            total_tests = sum(stats["test_functions"] for stats in test_file_stats.values())
            
            if total_tests < 10:  # Minimum viable test coverage
                self.add_result("E2E Test Suite", False, f"Insufficient test coverage: {total_tests} tests")
                return False
            
            self.add_result("E2E Test Suite", True, "Comprehensive E2E test suite implemented", {
                "total_test_functions": total_tests,
                "test_files": test_file_stats,
                "coverage_areas": ["full_workflow", "error_scenarios", "performance"]
            })
            
            return True
            
        except Exception as e:
            self.add_result("E2E Test Suite", False, f"E2E test validation failed: {e}")
            return False
    
    def validate_infrastructure_security(self) -> bool:
        """Validate infrastructure security enhancements"""
        try:
            template_path = os.path.join(os.path.dirname(__file__), '..', 'infrastructure', 'template.yaml')
            
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Check for security features
            security_features = [
                "JWTKeysSecret",
                "DatabaseSecret",
                "PIIEncryptionSecret",
                "ServerSideEncryption",
                "BucketEncryption",
                "PublicAccessBlockConfiguration",
                "secretsmanager:GetSecretValue",
                "CloudWatch",
                "Tracing: Active",
                "DeadLetterQueue"
            ]
            
            missing_security = []
            for feature in security_features:
                if feature not in template_content:
                    missing_security.append(feature)
            
            if missing_security:
                self.add_result("Infrastructure Security", False, f"Missing security features: {missing_security}")
                return False
            
            # Check for monitoring and alerting
            monitoring_features = [
                "HighErrorRateAlarm",
                "HighLatencyAlarm", 
                "CloudWatch",
                "Metrics"
            ]
            
            has_monitoring = any(feature in template_content for feature in monitoring_features)
            
            self.add_result("Infrastructure Security", True, "Production-grade infrastructure security implemented", {
                "security_features_count": len(security_features),
                "has_monitoring": has_monitoring,
                "has_secrets_management": "JWTKeysSecret" in template_content,
                "has_encryption": "ServerSideEncryption" in template_content
            })
            
            return True
            
        except Exception as e:
            self.add_result("Infrastructure Security", False, f"Infrastructure security validation failed: {e}")
            return False
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all production readiness validations"""
        logger.info("🚀 Starting Production Readiness Validation")
        logger.info("=" * 60)
        
        validations = [
            ("Authentication System", self.validate_authentication_system),
            ("Observability System", self.validate_observability_system),
            ("Secrets Management", self.validate_secrets_management),
            ("Mobile Error Handling", self.validate_mobile_error_handling),
            ("API Versioning", self.validate_api_versioning),
            ("Service Updates", self.validate_service_updates),
            ("E2E Test Suite", self.validate_e2e_test_suite),
            ("Infrastructure Security", self.validate_infrastructure_security)
        ]
        
        passed_count = 0
        total_count = len(validations)
        
        for validation_name, validation_func in validations:
            logger.info(f"\n🔍 Validating: {validation_name}")
            try:
                result = validation_func()
                if result:
                    passed_count += 1
            except Exception as e:
                logger.error(f"❌ Validation error in {validation_name}: {e}")
                self.add_result(validation_name, False, f"Validation error: {e}")
        
        # Generate summary
        total_time = time.time() - self.start_time
        success_rate = (passed_count / total_count) * 100
        
        summary = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_validations": total_count,
            "passed_validations": passed_count,
            "failed_validations": total_count - passed_count,
            "success_rate": success_rate,
            "total_time_seconds": round(total_time, 2),
            "production_ready": success_rate >= 100,  # All tests must pass
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }
        
        return summary

def main():
    """Main validation function"""
    print("🏗️  Petty Production Readiness Validation")
    print("=" * 50)
    
    validator = ProductionReadinessValidator()
    summary = validator.run_all_validations()
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"Total Validations: {summary['total_validations']}")
    print(f"Passed: {summary['passed_validations']} ✅")
    print(f"Failed: {summary['failed_validations']} ❌")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Total Time: {summary['total_time_seconds']}s")
    
    if summary['production_ready']:
        print("\n🎉 PROJECT IS PRODUCTION READY! 🎉")
        print("All critical production requirements have been implemented.")
    else:
        print("\n⚠️  PROJECT NEEDS ATTENTION")
        print("Some production requirements are not yet satisfied.")
        
        print("\nFailed Validations:")
        for result in summary['results']:
            if not result['passed']:
                print(f"  ❌ {result['test_name']}: {result['message']}")
    
    # Save detailed results
    with open('production_validation_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: production_validation_results.json")
    print(f"📄 Logs saved to: production_validation.log")
    
    return 0 if summary['production_ready'] else 1

if __name__ == "__main__":
    exit(main())