#!/usr/bin/env python3
"""
Health check script for Docker container
"""

import sys
import subprocess
import json
import os

def check_python_modules():
    """Check that critical Python modules can be imported"""
    try:
        import src.common.observability.logger
        import src.common.security.auth
        return True
    except ImportError as e:
        print(f"Module import failed: {e}")
        return False

def check_environment():
    """Check critical environment variables"""
    required_env = ['PYTHONPATH']
    for env_var in required_env:
        if not os.getenv(env_var):
            print(f"Missing environment variable: {env_var}")
            return False
    return True

def check_file_permissions():
    """Check that critical files are accessible"""
    critical_files = [
        '/app/src',
        '/app/healthcheck.py'
    ]
    
    for file_path in critical_files:
        if not os.path.exists(file_path):
            print(f"Critical file missing: {file_path}")
            return False
    return True

def main():
    """Main health check function"""
    checks = [
        ("Environment Variables", check_environment),
        ("File Permissions", check_file_permissions),
        ("Python Modules", check_python_modules)
    ]
    
    all_passed = True
    results = {}
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = "PASS" if result else "FAIL"
            if not result:
                all_passed = False
        except Exception as e:
            results[check_name] = f"ERROR: {e}"
            all_passed = False
    
    # Print results
    print("Health Check Results:")
    for check, result in results.items():
        print(f"  {check}: {result}")
    
    if all_passed:
        print("Overall Status: HEALTHY")
        sys.exit(0)
    else:
        print("Overall Status: UNHEALTHY")
        sys.exit(1)

if __name__ == "__main__":
    main()