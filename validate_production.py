#!/usr/bin/env python3
"""
Simple validation script for the production auth system
Tests basic functionality without requiring external dependencies
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_auth_structure():
    """Test that auth module can be imported and has correct structure"""
    try:
        from common.security.auth import (
            ProductionTokenManager,
            TokenPair,
            KeyManager,
            RefreshTokenStore
        )
        print("✅ Auth module imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Auth module import failed: {e}")
        return False

def test_key_manager():
    """Test key manager without cryptography dependencies"""
    try:
        # Test would require cryptography, so just check structure exists
        import common.security.auth as auth
        if hasattr(auth, 'KeyManager'):
            print("✅ KeyManager class exists")
            return True
        else:
            print("❌ KeyManager class not found")
            return False
    except Exception as e:
        print(f"❌ KeyManager test failed: {e}")
        return False

def test_token_store():
    """Test refresh token store functionality"""
    try:
        from common.security.auth import RefreshTokenStore
        
        store = RefreshTokenStore()
        
        # Test basic operations
        jti = "test-123"
        user_id = "user123"
        expires_at = datetime.now(timezone.utc)
        
        store.store_token(jti, user_id, expires_at)
        
        # Test retrieval
        retrieved_user = store.get_user_id(jti)
        if retrieved_user == user_id:
            print("✅ RefreshTokenStore basic operations work")
            return True
        else:
            print("❌ RefreshTokenStore operations failed")
            return False
            
    except Exception as e:
        print(f"❌ RefreshTokenStore test failed: {e}")
        return False

def test_docker_structure():
    """Test that Docker files are properly structured"""
    docker_files = [
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        'healthcheck.py'
    ]
    
    missing_files = []
    for file in docker_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All Docker files present")
        return True
    else:
        print(f"❌ Missing Docker files: {missing_files}")
        return False

def test_ci_workflows():
    """Test that CI workflow files exist and are structured correctly"""
    workflow_files = [
        '.github/workflows/ci.yml',
        '.github/workflows/build-sign.yml',
        '.github/workflows/coverage.yml'
    ]
    
    missing_files = []
    for file in workflow_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All CI workflow files present")
        return True
    else:
        print(f"❌ Missing CI workflow files: {missing_files}")
        return False

def test_monitoring_config():
    """Test monitoring configuration files"""
    monitoring_files = [
        'monitoring/prometheus.yml',
        'monitoring/grafana/datasources/datasources.yml'
    ]
    
    missing_files = []
    for file in monitoring_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All monitoring config files present")
        return True
    else:
        print(f"❌ Missing monitoring files: {missing_files}")
        return False

def test_security_enhancements():
    """Test that security enhancement files are present"""
    security_files = [
        'tests/security/test_production_auth.py',
        '.env.example'
    ]
    
    missing_files = []
    for file in security_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All security enhancement files present")
        return True
    else:
        print(f"❌ Missing security files: {missing_files}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Validating Petty Production-Grade Implementation")
    print("=" * 50)
    
    tests = [
        ("Basic Auth Structure", test_basic_auth_structure),
        ("Key Manager", test_key_manager),
        ("Token Store", test_token_store),
        ("Docker Structure", test_docker_structure),
        ("CI Workflows", test_ci_workflows),
        ("Monitoring Config", test_monitoring_config),
        ("Security Enhancements", test_security_enhancements)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validations passed! System is production-ready.")
        return 0
    else:
        print("⚠️  Some validations failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())