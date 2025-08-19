#!/usr/bin/env python3
"""
Demo script to validate the complete canary mitigation workflow.
This script simulates alarm scenarios and demonstrates the automatic response.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚨 Petty Canary Mitigation System Demo")
    print("=" * 50)
    
    # Import components
    from behavioral_interpreter.config import BehavioralInterpreterConfig, SafeModeLevel
    from common.security.rate_limiter import safe_mode_rate_limit_decorator, is_heavy_route_throttled
    
    # Initialize configuration
    config = BehavioralInterpreterConfig()
    
    print("1. System Starting in NORMAL Mode")
    config.set_safe_mode(SafeModeLevel.NORMAL)
    print_system_status(config)
    
    # Define a sample heavy route function
    @safe_mode_rate_limit_decorator('timeline', tokens=1, heavy_route=True)
    def sample_timeline_endpoint():
        return {"statusCode": 200, "body": "Timeline generated successfully"}
    
    # Test normal operation
    print("\n2. Testing Normal Operation")
    result = sample_timeline_endpoint()
    print(f"   Timeline endpoint result: {result['statusCode']} - {result.get('body', 'Success')}")
    
    print("\n3. ⚠️  ALARM TRIGGERED: High Error Rate Detected")
    print("   Automatic Response: Setting SAFE_MODE to ELEVATED")
    config.set_safe_mode(SafeModeLevel.ELEVATED)
    print_system_status(config)
    
    # Test elevated mode
    print("\n4. Testing Heavy Route Throttling in ELEVATED Mode")
    result = sample_timeline_endpoint()
    if result['statusCode'] == 429:
        print(f"   ✅ Timeline endpoint throttled: {result['statusCode']} - {result['body']['error']}")
        print(f"   Safe mode: {result['headers']['X-Safe-Mode']}")
    else:
        print(f"   ❌ Unexpected result: {result}")
    
    print("\n5. 🚨 CRITICAL ALARM: Lambda Function Throttling Detected")
    print("   Automatic Response: Escalating to CRITICAL Mode")
    config.set_safe_mode(SafeModeLevel.CRITICAL)
    print_system_status(config)
    
    print("\n6. Testing Rate Limiting in CRITICAL Mode")
    from common.security.rate_limiter import RateLimiter
    rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
    
    # Show rate limiting effects
    max_tokens, refill_rate = rate_limiter._get_effective_limits()
    print(f"   Rate limits adjusted: {max_tokens} tokens, {refill_rate} refill rate")
    print(f"   (70% reduction from normal: 100 tokens, 10.0 refill rate)")
    
    print("\n7. 🔴 EMERGENCY SITUATION: Multiple Alarms")
    print("   Automatic Response: Setting to EMERGENCY Mode")
    config.set_safe_mode(SafeModeLevel.EMERGENCY)
    print_system_status(config)
    
    # Show emergency throttling
    max_tokens, refill_rate = rate_limiter._get_effective_limits()
    print(f"   Emergency rate limits: {max_tokens} tokens, {refill_rate} refill rate")
    print(f"   (90% reduction from normal)")
    
    print("\n8. 🟢 System Recovery: Metrics Improving")
    print("   Gradual Safe Mode Reduction:")
    
    recovery_steps = [
        (SafeModeLevel.CRITICAL, "Critical"),
        (SafeModeLevel.ELEVATED, "Elevated"),
        (SafeModeLevel.NORMAL, "Normal")
    ]
    
    for step, name in recovery_steps:
        print(f"   → Setting to {name} mode...")
        config.set_safe_mode(step)
        time.sleep(0.5)  # Simulate monitoring period
        
    print_system_status(config)
    
    print("\n9. Testing Normal Operation After Recovery")
    result = sample_timeline_endpoint()
    print(f"   Timeline endpoint result: {result['statusCode']} - {result.get('body', 'Success')}")
    
    print("\n✅ Canary Mitigation Demo Complete!")
    print("   The system successfully:")
    print("   • Detected alarms and automatically adjusted safe mode")
    print("   • Applied progressive throttling to protect resources")
    print("   • Would create GitHub issues (in production)")
    print("   • Recovered gracefully when metrics improved")


def print_system_status(config):
    """Print current system status"""
    safe_config = config.get_safe_mode_config()
    
    print(f"   Safe Mode: {safe_config.level.value.upper()}")
    print(f"   Rate Limit Multiplier: {safe_config.rate_limit_multiplier}")
    print(f"   Max Concurrent Requests: {safe_config.max_concurrent_requests}")
    print(f"   Heavy Route Throttling: {'✅ Enabled' if safe_config.enable_heavy_route_throttling else '❌ Disabled'}")
    print(f"   GitHub Issue Creation: {'✅ Enabled' if safe_config.github_issue_creation else '❌ Disabled'}")


if __name__ == "__main__":
    main()