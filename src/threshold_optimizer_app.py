"""
AWS Lambda function for running threshold optimization.
Triggered by Step Functions schedule or manual invocation.
"""

import json
import logging
import os
import sys
import tempfile
from typing import Dict, Any

import boto3

# Add tools to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Run threshold optimization and return results.
    
    Expected input from Step Functions:
    {
        "s3_bucket": "petty-feedback-data",
        "feedback_prefix": "feedback/",
        "dry_run": false,
        "optimization_calls": 50,
        "min_improvement": 0.05
    }
    """
    try:
        # Import optimizer (needs to be done here due to Lambda constraints)
        from optimize_thresholds import ThresholdOptimizer
        from behavioral_interpreter.config import BehavioralInterpreterConfig
        
        # Extract parameters
        s3_bucket = event.get("s3_bucket", os.environ.get("FEEDBACK_BUCKET", "petty-feedback-data"))
        feedback_prefix = event.get("feedback_prefix", "feedback/")
        dry_run = event.get("dry_run", False)
        optimization_calls = event.get("optimization_calls", 50)
        min_improvement = event.get("min_improvement", 0.05)
        max_feedback_items = event.get("max_feedback_items", 1000)
        
        logger.info(f"Starting optimization: bucket={s3_bucket}, dry_run={dry_run}")
        
        # Initialize optimizer
        optimizer = ThresholdOptimizer(
            s3_bucket=s3_bucket,
            feedback_prefix=feedback_prefix,
            dry_run=dry_run
        )
        
        # Load feedback data
        feedback_count = optimizer.load_feedback_data(max_feedback_items)
        if feedback_count == 0:
            logger.warning("No feedback data found")
            return {
                "statusCode": 200,
                "optimization_report": {
                    "timestamp": optimizer.config.last_updated,
                    "feedback_data_count": 0,
                    "summary": {
                        "total_behaviors": 0,
                        "successful_optimizations": 0,
                        "applied_changes_count": 0
                    },
                    "message": "No feedback data available for optimization"
                },
                "config_content": None
            }
        
        logger.info(f"Loaded {feedback_count} feedback items")
        
        # Run optimization
        optimization_results = optimizer.optimize_all_behaviors(optimization_calls)
        
        # Apply results
        applied_changes = optimizer.apply_optimized_thresholds(
            optimization_results, min_improvement
        )
        
        # Generate report
        optimization_report = optimizer.generate_optimization_report(
            optimization_results, applied_changes
        )
        
        # Get updated configuration content
        config_content = None
        if any(applied_changes.values()) and not dry_run:
            config_content = optimizer.config.to_json()
        
        logger.info(f"Optimization completed: {optimization_report['summary']['applied_changes_count']} changes applied")
        
        return {
            "statusCode": 200,
            "optimization_report": optimization_report,
            "config_content": config_content,
            "dry_run": dry_run
        }
        
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e),
            "message": "Optimization failed"
        }

def validate_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and set default parameters"""
    validated = {}
    
    # Required parameters
    validated["s3_bucket"] = event.get("s3_bucket") or os.environ.get("FEEDBACK_BUCKET")
    if not validated["s3_bucket"]:
        raise ValueError("s3_bucket parameter or FEEDBACK_BUCKET environment variable required")
    
    # Optional parameters with defaults
    validated["feedback_prefix"] = event.get("feedback_prefix", "feedback/")
    validated["dry_run"] = bool(event.get("dry_run", False))
    validated["optimization_calls"] = min(max(int(event.get("optimization_calls", 50)), 10), 200)
    validated["min_improvement"] = max(float(event.get("min_improvement", 0.05)), 0.01)
    validated["max_feedback_items"] = min(max(int(event.get("max_feedback_items", 1000)), 100), 5000)
    
    return validated