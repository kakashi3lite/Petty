#!/bin/bash
# Test script to simulate the red team workflow locally
set -e

echo "🔒 Red Team Security Testing Simulation"
echo "========================================"

# Set up environment
export TEST_INTENSITY="normal"
export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

echo "📊 Testing LLM Top 10 scenarios on each endpoint..."

# Test each endpoint with LLM Top 10 tests
for endpoint in ingest pet-timeline submit-feedback; do
    echo "  🎯 Testing endpoint: $endpoint"
    
    export TEST_ENDPOINT=$endpoint
    
    # Run the tests and capture exit code
    if pytest tests/security/test_llm_top10.py \
        -k "test_$endpoint" \
        --junitxml="llm-top10-$endpoint-results.xml" \
        --tb=short \
        --no-cov \
        -q; then
        echo "    ✅ LLM Top 10 tests passed for $endpoint"
    else
        echo "    ❌ LLM Top 10 tests failed for $endpoint (expected for demo)"
        
        # Simulate issue creation logic
        if [ -f "llm-top10-$endpoint-results.xml" ]; then
            if grep -q 'failures=' "llm-top10-$endpoint-results.xml" && ! grep -q 'failures="0"' "llm-top10-$endpoint-results.xml"; then
                echo "    🚨 Would create GitHub issue: 'Red Team Security Test Failure: llm-top10 on $endpoint endpoint'"
            fi
        fi
    fi
done

echo ""
echo "📊 Testing ATLAS scenarios on each endpoint..."

# Test each endpoint with ATLAS tests
for endpoint in ingest pet-timeline submit-feedback; do
    echo "  🎯 Testing endpoint: $endpoint"
    
    export TEST_ENDPOINT=$endpoint
    
    # Run the tests and capture exit code
    if pytest tests/security/test_atlas_cases.py \
        -k "test_$endpoint" \
        --junitxml="atlas-cases-$endpoint-results.xml" \
        --tb=short \
        --no-cov \
        -q; then
        echo "    ✅ ATLAS tests passed for $endpoint"
    else
        echo "    ❌ ATLAS tests failed for $endpoint (expected for demo)"
        
        # Simulate issue creation logic
        if [ -f "atlas-cases-$endpoint-results.xml" ]; then
            if grep -q 'failures=' "atlas-cases-$endpoint-results.xml" && ! grep -q 'failures="0"' "atlas-cases-$endpoint-results.xml"; then
                echo "    🚨 Would create GitHub issue: 'Red Team Security Test Failure: atlas-cases on $endpoint endpoint'"
            fi
        fi
    fi
done

echo ""
echo "🔍 Checking CodeQL workflow requirements..."

if [ -f ".github/workflows/codeql.yml" ]; then
    echo "  ✅ CodeQL workflow exists"
    
    if grep -q "pull_request:" .github/workflows/codeql.yml; then
        echo "  ✅ CodeQL runs on pull requests (required)"
    else
        echo "  ❌ CodeQL workflow must run on pull requests"
        exit 1
    fi
    
    if grep -q "schedule:" .github/workflows/codeql.yml; then
        echo "  ✅ CodeQL has scheduled runs"
    else
        echo "  ⚠️  CodeQL workflow should include scheduled runs"
    fi
else
    echo "  ❌ CodeQL workflow not found!"
    exit 1
fi

echo ""
echo "📋 Test Results Summary:"
echo "========================"

total_xml_files=$(find . -name "*-results.xml" | wc -l)
failed_files=$(find . -name "*-results.xml" -exec grep -l 'failures=' {} \; | wc -l)

echo "  📊 Total test result files: $total_xml_files"
echo "  ❌ Files with failures: $failed_files"

if [ $failed_files -gt 0 ]; then
    echo "  🚨 Security vulnerabilities detected!"
    echo "  💡 In production, this would create GitHub issues with 'security:auto' labels"
else
    echo "  ✅ No security vulnerabilities detected"
fi

echo ""
echo "🔒 Red Team Security Testing Complete!"
echo "✅ Workflow validation successful"

# Clean up test artifacts
rm -f *-results.xml

exit 0