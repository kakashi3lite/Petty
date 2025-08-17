"""
Test runner that executes all security and performance tests
"""

import importlib.util
import sys
import time
from pathlib import Path


def import_test_module(file_path):
    """Import a test module from file path"""
    spec = importlib.util.spec_from_file_location("test_module", file_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Failed to import {file_path}: {e}")
        return None

def run_test_class(test_class, class_name):
    """Run all test methods in a test class"""
    print(f"\n=== {class_name} ===")
    instance = test_class()

    passed = 0
    failed = 0

    for method_name in dir(instance):
        if method_name.startswith('test_'):
            print(f"Running {method_name}...", end=" ")
            try:
                method = getattr(instance, method_name)
                start_time = time.time()
                method()
                end_time = time.time()
                print(f"✓ ({end_time - start_time:.2f}s)")
                passed += 1
            except Exception as e:
                print(f"❌ {e}")
                failed += 1

    return passed, failed

def main():
    """Main test runner"""
    print("=" * 60)
    print("Petty Production Security & Performance Test Suite")
    print("=" * 60)

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"

    total_passed = 0
    total_failed = 0

    # Security tests
    print("\n" + "=" * 40)
    print("SECURITY TESTS")
    print("=" * 40)

    security_tests = [
        tests_dir / "security" / "test_owasp_llm_mitigations.py",
        tests_dir / "security" / "test_ai_security.py"
    ]

    for test_file in security_tests:
        if test_file.exists():
            print(f"\nLoading {test_file.name}...")
            module = import_test_module(test_file)
            if module:
                # Find test classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        attr_name.startswith('Test') and
                        attr_name != 'TestCase'):
                        passed, failed = run_test_class(attr, attr_name)
                        total_passed += passed
                        total_failed += failed
        else:
            print(f"Test file not found: {test_file}")

    # Performance tests
    print("\n" + "=" * 40)
    print("PERFORMANCE TESTS")
    print("=" * 40)

    performance_test_file = tests_dir / "performance" / "test_performance.py"
    if performance_test_file.exists():
        print(f"\nLoading {performance_test_file.name}...")
        module = import_test_module(performance_test_file)
        if module:
            # Find test classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr_name.startswith('Test') and
                    attr_name != 'TestCase'):
                    passed, failed = run_test_class(attr, attr_name)
                    total_passed += passed
                    total_failed += failed
    else:
        print(f"Performance test file not found: {performance_test_file}")

    # Integration tests
    print("\n" + "=" * 40)
    print("INTEGRATION TESTS")
    print("=" * 40)

    integration_test_file = tests_dir / "integration" / "test_integration.py"
    if integration_test_file.exists():
        print(f"\nLoading {integration_test_file.name}...")
        module = import_test_module(integration_test_file)
        if module:
            # Find test classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr_name.startswith('Test') and
                    attr_name != 'TestCase'):
                    passed, failed = run_test_class(attr, attr_name)
                    total_passed += passed
                    total_failed += failed
    else:
        print(f"Integration test file not found: {integration_test_file}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed + total_failed)*100:.1f}%" if (total_passed + total_failed) > 0 else "No tests run")

    if total_failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {total_failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
