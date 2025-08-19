"""
Alarm mitigation Lambda function.
Handles CloudWatch alarms and triggers safe mode adjustments.
"""

import json
import os
import boto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS clients
ssm_client = boto3.client('ssm')
lambda_client = boto3.client('lambda')
stepfunctions_client = boto3.client('stepfunctions')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for alarm mitigation
    
    Processes CloudWatch alarm notifications and:
    1. Determines appropriate safe mode level
    2. Updates system configuration
    3. Triggers Step Functions orchestration
    """
    logger.info("Alarm mitigation triggered", extra={"event": event})
    
    try:
        # Parse SNS message
        sns_message = _parse_sns_message(event)
        if not sns_message:
            logger.error("Failed to parse SNS message")
            return {"statusCode": 400, "body": "Invalid SNS message"}
        
        # Extract alarm details
        alarm_data = _extract_alarm_data(sns_message)
        logger.info("Processing alarm", extra={"alarm_data": alarm_data})
        
        # Determine safe mode level based on alarm
        safe_mode = _determine_safe_mode(alarm_data)
        logger.info(f"Determined safe mode: {safe_mode}")
        
        # Update safe mode configuration
        _update_safe_mode(safe_mode)
        
        # Update Lambda function environment variables
        _update_lambda_environments(safe_mode)
        
        # Trigger Step Functions orchestration
        step_function_arn = os.environ.get('STEP_FUNCTION_ARN')
        if step_function_arn:
            _trigger_step_function(step_function_arn, alarm_data, safe_mode)
        
        logger.info("Alarm mitigation completed successfully")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Alarm mitigation completed",
                "safe_mode": safe_mode,
                "alarm": alarm_data.get("AlarmName", "unknown")
            })
        }
        
    except Exception as e:
        logger.error(f"Alarm mitigation failed: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }


def _parse_sns_message(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse SNS message from the event"""
    try:
        if 'Records' in event and len(event['Records']) > 0:
            record = event['Records'][0]
            if record.get('EventSource') == 'aws:sns':
                message = record['Sns']['Message']
                if isinstance(message, str):
                    return json.loads(message)
                return message
        return None
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to parse SNS message: {e}")
        return None


def _extract_alarm_data(sns_message: Dict[str, Any]) -> Dict[str, Any]:
    """Extract alarm data from SNS message"""
    return {
        "AlarmName": sns_message.get("AlarmName", "unknown"),
        "NewStateValue": sns_message.get("NewStateValue", "UNKNOWN"),
        "NewStateReason": sns_message.get("NewStateReason", ""),
        "StateChangeTime": sns_message.get("StateChangeTime", datetime.utcnow().isoformat()),
        "Region": sns_message.get("Region", "us-east-1"),
        "AccountId": sns_message.get("AWSAccountId", ""),
        "Trigger": sns_message.get("Trigger", {})
    }


def _determine_safe_mode(alarm_data: Dict[str, Any]) -> str:
    """Determine safe mode level based on alarm characteristics"""
    alarm_name = alarm_data.get("AlarmName", "").lower()
    state = alarm_data.get("NewStateValue", "")
    
    # Only escalate on ALARM state
    if state != "ALARM":
        return "normal"
    
    # Determine severity based on alarm name patterns
    if any(pattern in alarm_name for pattern in ["critical", "emergency", "throttle"]):
        if "throttle" in alarm_name:
            return "emergency"
        return "critical"
    elif any(pattern in alarm_name for pattern in ["high", "error", "duration"]):
        return "elevated"
    else:
        return "elevated"  # Default to elevated for any alarm


def _update_safe_mode(safe_mode: str) -> None:
    """Update safe mode parameter in SSM"""
    try:
        parameter_name = os.environ.get('SAFE_MODE_PARAMETER', '/petty/safe-mode')
        
        ssm_client.put_parameter(
            Name=parameter_name,
            Value=safe_mode,
            Type='String',
            Overwrite=True,
            Description=f'Safe mode set by alarm mitigation at {datetime.utcnow().isoformat()}'
        )
        
        logger.info(f"Updated safe mode parameter to: {safe_mode}")
        
    except Exception as e:
        logger.error(f"Failed to update safe mode parameter: {e}")
        raise


def _update_lambda_environments(safe_mode: str) -> None:
    """Update environment variables for all Lambda functions"""
    try:
        # List of Lambda functions to update
        functions_to_update = [
            "DataProcessorFunction",
            "TimelineGeneratorFunction", 
            "FeedbackHandlerFunction"
        ]
        
        for function_name in functions_to_update:
            try:
                # Get current configuration
                response = lambda_client.get_function_configuration(FunctionName=function_name)
                
                # Update environment variables
                current_env = response.get('Environment', {}).get('Variables', {})
                current_env['SAFE_MODE'] = safe_mode
                
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={'Variables': current_env}
                )
                
                logger.info(f"Updated {function_name} with safe mode: {safe_mode}")
                
            except lambda_client.exceptions.ResourceNotFoundException:
                logger.warning(f"Function {function_name} not found, skipping")
            except Exception as e:
                logger.error(f"Failed to update {function_name}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to update Lambda environments: {e}")
        # Don't raise here - this is not critical


def _trigger_step_function(step_function_arn: str, alarm_data: Dict[str, Any], safe_mode: str) -> None:
    """Trigger Step Functions orchestration"""
    try:
        execution_input = {
            **alarm_data,
            "safeMode": safe_mode,
            "mitigationTimestamp": datetime.utcnow().isoformat()
        }
        
        response = stepfunctions_client.start_execution(
            stateMachineArn=step_function_arn,
            name=f"mitigation-{alarm_data.get('AlarmName', 'unknown')}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(execution_input)
        )
        
        logger.info(f"Started Step Functions execution: {response['executionArn']}")
        
    except Exception as e:
        logger.error(f"Failed to trigger Step Functions: {e}")
        # Don't raise here - the main mitigation can still succeed