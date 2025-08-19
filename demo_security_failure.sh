#!/bin/bash
# Demonstrate the red team workflow by running tests that will fail
set -e

echo "🚨 Red Team Security Test Failure Demonstration"
echo "==============================================="
echo ""
echo "This script demonstrates how the red team workflow detects security vulnerabilities"
echo "and would create GitHub issues with the 'security:auto' label in production."
echo ""

# Set up environment
export TEST_INTENSITY="normal"

echo "🎯 Running security tests designed to fail..."
echo ""

# Run a specific test that we know will fail to demonstrate issue creation
export TEST_ENDPOINT=ingest
echo "Testing oversized input handling on ingest endpoint..."

if pytest tests/security/test_llm_top10.py::TestLLMTop10Adversarial::test_ingest_oversized_inputs \
    --junitxml="demo-failure-results.xml" \
    --tb=short \
    --no-cov \
    -v; then
    echo "❌ Test unexpectedly passed (this was supposed to demonstrate a failure)"
else
    echo "✅ Test failed as expected - demonstrating vulnerability detection"
    echo ""
    
    # Show what the workflow would detect
    if [ -f "demo-failure-results.xml" ]; then
        echo "📋 Test Results Analysis:"
        echo "========================"
        
        if grep -q 'failures=' "demo-failure-results.xml" && ! grep -q 'failures="0"' "demo-failure-results.xml"; then
            echo "🚨 SECURITY ISSUE DETECTED!"
            echo ""
            echo "GitHub Issue that would be created:"
            echo "-----------------------------------"
            echo "Title: 🚨 Red Team Security Test Failure: llm-top10 on ingest endpoint"
            echo ""
            echo "Labels: security:auto, red-team, needs-triage, endpoint:ingest, suite:llm-top10"
            echo ""
            echo "Body:"
            echo "## Security Test Failure Alert"
            echo ""
            echo "**Test Suite:** llm-top10"
            echo "**Target Endpoint:** /ingest"
            echo "**Timestamp:** $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
            echo ""
            echo "### Summary"
            echo "Adversarial security testing has detected potential vulnerabilities in the ingest"
            echo "endpoint using llm-top10 test scenarios."
            echo ""
            echo "### Actions Required"
            echo "1. ✅ Review the test failure details in the workflow run"
            echo "2. ✅ Analyze the specific attack vector that succeeded"
            echo "3. ✅ Implement necessary security hardening"
            echo "4. ✅ Re-run tests to verify fixes"
            echo "5. ✅ Update security documentation if needed"
            echo ""
            echo "**This issue was automatically created by the Red Team Security Testing workflow.**"
            echo ""
            echo "-----------------------------------"
        else
            echo "No failures detected in XML file"
        fi
        
        # Show the actual test failure details
        echo ""
        echo "📊 Raw Test Results:"
        echo "==================="
        grep -E "(testcase|failure)" "demo-failure-results.xml" | head -5
        
    else
        echo "No test results file generated"
    fi
fi

echo ""
echo "🔒 Key Features Demonstrated:"
echo "============================"
echo "✅ Automated security vulnerability detection"
echo "✅ GitHub issue creation with appropriate labels"
echo "✅ Detailed failure analysis and remediation guidance"
echo "✅ Integration with existing CI/CD pipeline"
echo "✅ Support for multiple security frameworks (LLM Top 10, ATLAS)"
echo "✅ Endpoint-specific testing (/ingest, /pet-timeline, /submit-feedback)"
echo ""
echo "In production, this workflow would:"
echo "1. Run automatically on pushes and PRs"
echo "2. Execute all security test suites against all endpoints"
echo "3. Create GitHub issues for any detected vulnerabilities"
echo "4. Maintain security gates alongside CodeQL requirements"
echo ""

# Clean up
rm -f demo-failure-results.xml

echo "🎉 Demonstration complete!"