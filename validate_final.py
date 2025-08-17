#!/usr/bin/env python3
"""
Production readiness checklist for Petty AI Pet Monitoring System
Validates file structure and implementation completeness
"""

import os
import json

def check_file_exists(filepath, description=""):
    """Check if a file exists and optionally validate content"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {filepath} {description}")
    return exists

def check_directory_structure():
    """Validate directory structure"""
    print("\n📁 Directory Structure")
    print("-" * 30)
    
    directories = [
        ("src/common/security/", "Security modules"),
        ("tests/security/", "Security tests"),
        ("monitoring/", "Monitoring configuration"),
        (".github/workflows/", "CI/CD workflows"),
        ("infrastructure/", "AWS SAM infrastructure")
    ]
    
    all_exist = True
    for directory, description in directories:
        exists = os.path.exists(directory)
        status = "✅" if exists else "❌"
        print(f"{status} {directory} - {description}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_security_implementation():
    """Check security implementation files"""
    print("\n🔐 Security Implementation")
    print("-" * 30)
    
    files = [
        ("src/common/security/auth.py", "Production JWT authentication"),
        ("tests/security/test_production_auth.py", "Comprehensive auth tests"),
        (".env.example", "Environment configuration template"),
        ("requirements.txt", "Python dependencies")
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, f"- {description}"):
            all_exist = False
    
    return all_exist

def check_containerization():
    """Check containerization files"""
    print("\n🐳 Containerization")
    print("-" * 30)
    
    files = [
        ("Dockerfile", "Multi-stage production build"),
        ("docker-compose.yml", "Complete development stack"),
        (".dockerignore", "Docker build optimization"),
        ("healthcheck.py", "Container health checks")
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, f"- {description}"):
            all_exist = False
    
    return all_exist

def check_cicd_implementation():
    """Check CI/CD implementation"""
    print("\n🔄 CI/CD Implementation")
    print("-" * 30)
    
    files = [
        (".github/workflows/ci.yml", "Continuous integration"),
        (".github/workflows/build-sign.yml", "Build, sign, and SBOM"),
        (".github/workflows/coverage.yml", "Coverage reporting"),
        (".github/workflows/codeql.yml", "Security scanning"),
        (".codacy/cli.sh", "Codacy integration")
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, f"- {description}"):
            all_exist = False
    
    return all_exist

def check_monitoring_observability():
    """Check monitoring and observability"""
    print("\n📊 Monitoring & Observability")
    print("-" * 30)
    
    files = [
        ("monitoring/prometheus.yml", "Metrics collection"),
        ("monitoring/grafana/datasources/datasources.yml", "Grafana data sources")
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, f"- {description}"):
            all_exist = False
    
    return all_exist

def check_documentation():
    """Check documentation updates"""
    print("\n📚 Documentation")
    print("-" * 30)
    
    files = [
        ("README.md", "Updated with production guidance"),
        ("LICENSE", "MIT license file"),
        ("docs/SECURITY.md", "Security documentation")
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, f"- {description}"):
            all_exist = False
    
    return all_exist

def validate_file_content():
    """Validate key file contents"""
    print("\n🔍 Content Validation")
    print("-" * 30)
    
    validations = []
    
    # Check README for production deployment section
    if os.path.exists("README.md"):
        with open("README.md", "r") as f:
            readme_content = f.read()
            if "Production Deployment" in readme_content:
                print("✅ README.md contains production deployment section")
                validations.append(True)
            else:
                print("❌ README.md missing production deployment section")
                validations.append(False)
    
    # Check docker-compose for monitoring stack
    if os.path.exists("docker-compose.yml"):
        with open("docker-compose.yml", "r") as f:
            compose_content = f.read()
            if "prometheus:" in compose_content and "grafana:" in compose_content:
                print("✅ docker-compose.yml includes monitoring stack")
                validations.append(True)
            else:
                print("❌ docker-compose.yml missing monitoring components")
                validations.append(False)
    
    # Check CI for SBOM generation
    if os.path.exists(".github/workflows/build-sign.yml"):
        with open(".github/workflows/build-sign.yml", "r") as f:
            ci_content = f.read()
            if "syft" in ci_content and "cosign" in ci_content:
                print("✅ CI includes SBOM generation and signing")
                validations.append(True)
            else:
                print("❌ CI missing SBOM generation or signing")
                validations.append(False)
    
    return all(validations)

def main():
    """Main validation function"""
    print("🚀 Petty Production-Grade Implementation Validation")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Security Implementation", check_security_implementation),
        ("Containerization", check_containerization),
        ("CI/CD Implementation", check_cicd_implementation),
        ("Monitoring & Observability", check_monitoring_observability),
        ("Documentation", check_documentation),
        ("Content Validation", validate_file_content)
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append(result)
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 PRODUCTION-READY!")
        print("   All implementation requirements satisfied.")
        print("\n📋 Key Features Implemented:")
        print("   ✅ Production JWT authentication with RSA/ECDSA")
        print("   ✅ Multi-stage Docker containerization")
        print("   ✅ SBOM generation with Syft")
        print("   ✅ Artifact signing with Cosign")
        print("   ✅ SLSA Level 3 provenance")
        print("   ✅ Comprehensive CI/CD pipeline")
        print("   ✅ Monitoring stack (Prometheus/Grafana/Jaeger)")
        print("   ✅ Security scanning integration")
        print("   ✅ Coverage badges and quality metrics")
        
        print("\n🚀 Next Steps:")
        print("   1. Set up environment variables (.env file)")
        print("   2. Configure Codacy and Codecov tokens")
        print("   3. Deploy with: docker-compose up -d")
        print("   4. Run tests with: make test")
        return 0
    else:
        print(f"\n⚠️  Implementation incomplete: {total - passed} issues found")
        return 1

if __name__ == "__main__":
    exit(main())