"""
Threshold optimization tool using Bayesian Optimization for behavioral interpreter.
Optimizes cross-validation F1 score using feedback data from S3.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

import boto3
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import KFold
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from behavioral_interpreter.config import (
    BehavioralInterpreterConfig, 
    BehaviorConfigType,
    ThresholdBounds
)
from behavioral_interpreter.interpreter import BehavioralInterpreter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThresholdOptimizer:
    """Bayesian optimization for behavioral interpreter thresholds"""
    
    def __init__(self, s3_bucket: str, feedback_prefix: str = "feedback/", 
                 dry_run: bool = False):
        self.s3_bucket = s3_bucket
        self.feedback_prefix = feedback_prefix
        self.dry_run = dry_run
        self.s3_client = boto3.client('s3')
        self.config = BehavioralInterpreterConfig()
        self.feedback_data = []
        
    def load_feedback_data(self, max_items: int = 1000) -> int:
        """Load feedback data from S3"""
        logger.info(f"Loading feedback data from s3://{self.s3_bucket}/{self.feedback_prefix}")
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.s3_bucket,
                Prefix=self.feedback_prefix,
                MaxKeys=max_items
            )
            
            feedback_count = 0
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    if obj['Key'].endswith('.json'):
                        try:
                            response = self.s3_client.get_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            feedback_item = json.loads(response['Body'].read())
                            
                            # Validate feedback format
                            if self._validate_feedback_item(feedback_item):
                                self.feedback_data.append(feedback_item)
                                feedback_count += 1
                                
                                if feedback_count >= max_items:
                                    break
                                    
                        except Exception as e:
                            logger.warning(f"Failed to load feedback item {obj['Key']}: {e}")
                            continue
                
                if feedback_count >= max_items:
                    break
            
            logger.info(f"Loaded {len(self.feedback_data)} feedback items")
            return len(self.feedback_data)
            
        except Exception as e:
            logger.error(f"Failed to load feedback data: {e}")
            return 0
    
    def _validate_feedback_item(self, item: Dict[str, Any]) -> bool:
        """Validate feedback item format"""
        required_fields = ['event_id', 'collar_id', 'user_feedback', 'ts']
        return all(field in item for field in required_fields) and \
               item['user_feedback'] in ['correct', 'incorrect']
    
    def prepare_training_data(self) -> List[Tuple[List[Dict], int]]:
        """Prepare training data from feedback for cross-validation"""
        training_data = []
        
        for feedback_item in self.feedback_data:
            # Convert feedback to binary label
            label = 1 if feedback_item['user_feedback'] == 'correct' else 0
            
            # Extract segment data if available
            segment = feedback_item.get('segment', {})
            if isinstance(segment, dict) and 'collar_data' in segment:
                collar_data = segment['collar_data']
                if isinstance(collar_data, list) and len(collar_data) > 0:
                    training_data.append((collar_data, label))
        
        logger.info(f"Prepared {len(training_data)} training samples")
        return training_data
    
    def evaluate_thresholds(self, behavior_type: str, confidence_threshold: float,
                          min_data_points: int, min_hr: int, max_hr: int,
                          training_data: List[Tuple[List[Dict], int]]) -> float:
        """Evaluate F1 score for given thresholds using cross-validation"""
        if len(training_data) < 10:  # Need minimum data for CV
            logger.warning("Insufficient training data for cross-validation")
            return 0.0
        
        # Update config with new thresholds
        temp_config = BehavioralInterpreterConfig()
        temp_config.update_thresholds(
            behavior_type,
            confidence_threshold=confidence_threshold,
            min_data_points=min_data_points,
            heart_rate_range=(min_hr, max_hr)
        )
        
        # Perform k-fold cross-validation
        kf = KFold(n_splits=min(5, len(training_data)), shuffle=True, random_state=42)
        f1_scores = []
        
        X = [item[0] for item in training_data]  # collar_data
        y = [item[1] for item in training_data]  # labels
        
        for train_idx, test_idx in kf.split(X):
            # Create interpreter with temporary config
            interpreter = BehavioralInterpreter()
            interpreter._config = temp_config
            interpreter.behavior_rules = interpreter._load_behavior_rules()
            
            # Test on fold
            y_pred = []
            for idx in test_idx:
                collar_data = X[idx]
                try:
                    events = interpreter.analyze_timeline(collar_data)
                    # Check if target behavior was detected
                    detected = any(
                        event.get('behavior') == temp_config.get_config(behavior_type).name 
                        for event in events
                    )
                    y_pred.append(1 if detected else 0)
                except Exception as e:
                    logger.warning(f"Analysis failed for sample {idx}: {e}")
                    y_pred.append(0)  # Default to no detection
            
            y_true_fold = [y[idx] for idx in test_idx]
            if len(set(y_true_fold)) > 1 and len(set(y_pred)) > 1:  # Need both classes
                f1 = f1_score(y_true_fold, y_pred, average='binary')
                f1_scores.append(f1)
        
        avg_f1 = np.mean(f1_scores) if f1_scores else 0.0
        logger.debug(f"F1 score for {behavior_type}: {avg_f1:.3f} "
                    f"(conf={confidence_threshold:.3f}, min_pts={min_data_points}, "
                    f"hr_range=({min_hr}, {max_hr}))")
        return avg_f1
    
    def optimize_behavior_thresholds(self, behavior_type: str, 
                                   training_data: List[Tuple[List[Dict], int]],
                                   n_calls: int = 50) -> Dict[str, Any]:
        """Optimize thresholds for a specific behavior type"""
        logger.info(f"Optimizing thresholds for {behavior_type}")
        
        config = self.config.get_config(behavior_type)
        if not config:
            raise ValueError(f"Unknown behavior type: {behavior_type}")
        
        # Define search space based on safety bounds
        dimensions = [
            Real(config.confidence_bounds.min_value, config.confidence_bounds.max_value, 
                 name='confidence_threshold'),
            Integer(int(config.min_data_points_bounds.min_value), 
                   int(config.min_data_points_bounds.max_value), 
                   name='min_data_points'),
            Integer(int(config.heart_rate_bounds[0].min_value), 
                   int(config.heart_rate_bounds[0].max_value), 
                   name='min_hr'),
            Integer(int(config.heart_rate_bounds[1].min_value), 
                   int(config.heart_rate_bounds[1].max_value), 
                   name='max_hr'),
        ]
        
        @use_named_args(dimensions)
        def objective(**params):
            """Objective function to minimize (negative F1 score)"""
            try:
                # Ensure heart rate range is valid
                if params['min_hr'] >= params['max_hr']:
                    return 1.0  # Bad score for invalid range
                
                f1 = self.evaluate_thresholds(
                    behavior_type=behavior_type,
                    confidence_threshold=params['confidence_threshold'],
                    min_data_points=params['min_data_points'],
                    min_hr=params['min_hr'],
                    max_hr=params['max_hr'],
                    training_data=training_data
                )
                return -f1  # Minimize negative F1 (maximize F1)
            except Exception as e:
                logger.warning(f"Objective evaluation failed: {e}")
                return 1.0  # Bad score for failed evaluation
        
        # Run Bayesian optimization
        logger.info(f"Running Bayesian optimization with {n_calls} calls")
        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_calls=n_calls,
            random_state=42,
            acq_func='EI',  # Expected Improvement
            n_initial_points=min(10, n_calls // 2)
        )
        
        # Extract optimal parameters
        optimal_params = {
            'confidence_threshold': result.x[0],
            'min_data_points': int(result.x[1]),
            'min_hr': int(result.x[2]),
            'max_hr': int(result.x[3]),
            'f1_score': -result.fun,
            'n_evaluations': len(result.func_vals)
        }
        
        logger.info(f"Optimization completed for {behavior_type}: "
                   f"F1={optimal_params['f1_score']:.3f}")
        return optimal_params
    
    def optimize_all_behaviors(self, n_calls_per_behavior: int = 50) -> Dict[str, Dict[str, Any]]:
        """Optimize thresholds for all behavior types"""
        if not self.feedback_data:
            raise ValueError("No feedback data loaded. Call load_feedback_data() first.")
        
        training_data = self.prepare_training_data()
        if not training_data:
            raise ValueError("No valid training data prepared from feedback.")
        
        results = {}
        
        for behavior_type in [BehaviorConfigType.DEEP_SLEEP.value, 
                             BehaviorConfigType.ANXIOUS_PACING.value,
                             BehaviorConfigType.PLAYING_FETCH.value]:
            try:
                optimal_params = self.optimize_behavior_thresholds(
                    behavior_type, training_data, n_calls_per_behavior
                )
                results[behavior_type] = optimal_params
            except Exception as e:
                logger.error(f"Failed to optimize {behavior_type}: {e}")
                results[behavior_type] = {'error': str(e)}
        
        return results
    
    def apply_optimized_thresholds(self, optimization_results: Dict[str, Dict[str, Any]],
                                 min_improvement_threshold: float = 0.05) -> Dict[str, bool]:
        """Apply optimized thresholds if they show sufficient improvement"""
        applied_changes = {}
        
        for behavior_type, results in optimization_results.items():
            if 'error' in results:
                logger.warning(f"Skipping {behavior_type} due to optimization error")
                applied_changes[behavior_type] = False
                continue
            
            # Get current performance baseline
            current_config = self.config.get_config(behavior_type)
            if not current_config:
                continue
            
            # Check improvement threshold
            optimized_f1 = results.get('f1_score', 0.0)
            if optimized_f1 < min_improvement_threshold:
                logger.info(f"Skipping {behavior_type}: F1 score {optimized_f1:.3f} "
                           f"below threshold {min_improvement_threshold}")
                applied_changes[behavior_type] = False
                continue
            
            # Apply new thresholds
            if not self.dry_run:
                success = self.config.update_thresholds(
                    behavior_type=behavior_type,
                    confidence_threshold=results['confidence_threshold'],
                    min_data_points=results['min_data_points'],
                    heart_rate_range=(results['min_hr'], results['max_hr'])
                )
                applied_changes[behavior_type] = success
                
                if success:
                    logger.info(f"Applied optimized thresholds for {behavior_type}")
                else:
                    logger.warning(f"Failed to apply thresholds for {behavior_type}")
            else:
                logger.info(f"[DRY RUN] Would apply thresholds for {behavior_type}: "
                           f"F1={optimized_f1:.3f}")
                applied_changes[behavior_type] = True
        
        return applied_changes
    
    def generate_optimization_report(self, optimization_results: Dict[str, Dict[str, Any]],
                                   applied_changes: Dict[str, bool]) -> Dict[str, Any]:
        """Generate detailed optimization report"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        report = {
            "timestamp": timestamp,
            "config_version": self.config.config_version,
            "dry_run": self.dry_run,
            "feedback_data_count": len(self.feedback_data),
            "optimization_results": optimization_results,
            "applied_changes": applied_changes,
            "summary": {
                "total_behaviors": len(optimization_results),
                "successful_optimizations": len([r for r in optimization_results.values() 
                                               if 'error' not in r]),
                "applied_changes_count": sum(applied_changes.values())
            }
        }
        
        return report

def main():
    """Main optimization pipeline"""
    parser = argparse.ArgumentParser(description='Optimize behavioral interpreter thresholds')
    parser.add_argument('--s3-bucket', required=True, help='S3 bucket containing feedback data')
    parser.add_argument('--feedback-prefix', default='feedback/', 
                       help='S3 prefix for feedback data')
    parser.add_argument('--max-feedback-items', type=int, default=1000,
                       help='Maximum feedback items to load')
    parser.add_argument('--optimization-calls', type=int, default=50,
                       help='Number of Bayesian optimization calls per behavior')
    parser.add_argument('--min-improvement', type=float, default=0.05,
                       help='Minimum F1 score improvement threshold')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no changes applied)')
    parser.add_argument('--output-file', help='Output file for optimization report')
    parser.add_argument('--config-output', help='Output file for optimized configuration')
    
    args = parser.parse_args()
    
    try:
        # Initialize optimizer
        optimizer = ThresholdOptimizer(
            s3_bucket=args.s3_bucket,
            feedback_prefix=args.feedback_prefix,
            dry_run=args.dry_run
        )
        
        # Load feedback data
        feedback_count = optimizer.load_feedback_data(args.max_feedback_items)
        if feedback_count == 0:
            logger.error("No feedback data loaded. Exiting.")
            return 1
        
        # Run optimization
        logger.info("Starting threshold optimization...")
        optimization_results = optimizer.optimize_all_behaviors(args.optimization_calls)
        
        # Apply results
        applied_changes = optimizer.apply_optimized_thresholds(
            optimization_results, args.min_improvement
        )
        
        # Generate report
        report = optimizer.generate_optimization_report(optimization_results, applied_changes)
        
        # Output results
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Optimization report saved to {args.output_file}")
        
        if args.config_output and not args.dry_run:
            optimizer.config.save_to_file(args.config_output)
            logger.info(f"Optimized configuration saved to {args.config_output}")
        
        # Print summary
        print("\nOptimization Summary:")
        print(f"- Feedback items processed: {feedback_count}")
        print(f"- Behaviors optimized: {report['summary']['successful_optimizations']}")
        print(f"- Changes applied: {report['summary']['applied_changes_count']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())