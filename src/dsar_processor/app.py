"""
DSAR Processor Lambda Function

This function handles DSAR (Data Subject Access Request) API endpoints and orchestrates
the processing workflow using AWS Step Functions.

Endpoints:
- POST /dsar/request - Initiate new DSAR request
- GET /dsar/status/{request_id} - Check DSAR request status

Features:
- Request validation and sanitization
- Step Functions workflow orchestration
- Presigned URL generation for secure data access
- Comprehensive audit logging
- Rate limiting and security controls
"""

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Import security and observability modules
try:
    from aws_lambda_powertools import Logger, Metrics, Tracer
    from aws_lambda_powertools.logging import correlation_paths
    from aws_lambda_powertools.metrics import MetricUnit
    from aws_lambda_powertools.utilities.typing import LambdaContext
    AWS_POWERTOOLS_AVAILABLE = True
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False
    class LambdaContext:
        pass

try:
    from common.security.crypto_utils import generate_secure_token
    from common.security.input_validators import InputValidator, sanitize_text_input
    from common.security.output_schemas import secure_response_wrapper
    from common.security.rate_limiter import RateLimitExceeded, rate_limit_decorator
    from common.security.redaction import safe_log
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False
    def safe_log(data): return str(data)[:100] + "..."
    def generate_secure_token(length=16):
        import secrets
        return secrets.token_hex(length)

# Initialize AWS clients
stepfunctions = boto3.client('stepfunctions')
s3 = boto3.client('s3')

# Environment variables
DSAR_BUCKET = os.getenv('DSAR_BUCKET', 'petty-dsar-exports')
STATE_MACHINE_ARN = os.getenv('STATE_MACHINE_ARN')
TIMESTREAM_DB = os.getenv('TIMESTREAM_DB', 'PettyDB')
TIMESTREAM_TABLE = os.getenv('TIMESTREAM_TABLE', 'CollarMetrics')

# Initialize observability
if AWS_POWERTOOLS_AVAILABLE:
    logger = Logger()
    tracer = Tracer()
    metrics = Metrics()
else:
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)


class DSARRequestValidator:
    """Validates DSAR requests according to GDPR requirements"""

    VALID_REQUEST_TYPES = {'export', 'delete'}
    VALID_DATA_TYPES = {'behavioral_events', 'sensor_metrics', 'location_data', 'all'}

    @staticmethod
    def validate_request(request_data: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize DSAR request"""
        errors = []

        # Required fields
        if 'user_id' not in request_data:
            errors.append("user_id is required")
        elif not isinstance(request_data['user_id'], str) or len(request_data['user_id']) < 3:
            errors.append("user_id must be a string with at least 3 characters")

        if 'request_type' not in request_data:
            errors.append("request_type is required")
        elif request_data['request_type'] not in DSARRequestValidator.VALID_REQUEST_TYPES:
            errors.append(f"request_type must be one of: {', '.join(DSARRequestValidator.VALID_REQUEST_TYPES)}")

        # Optional fields validation
        if 'data_types' in request_data:
            if not isinstance(request_data['data_types'], list):
                errors.append("data_types must be a list")
            else:
                invalid_types = set(request_data['data_types']) - DSARRequestValidator.VALID_DATA_TYPES
                if invalid_types:
                    errors.append(f"Invalid data_types: {', '.join(invalid_types)}")

        if 'date_range' in request_data:
            date_range = request_data['date_range']
            if not isinstance(date_range, dict):
                errors.append("date_range must be an object")
            else:
                if 'start' in date_range:
                    try:
                        datetime.fromisoformat(date_range['start'].replace('Z', '+00:00'))
                    except ValueError:
                        errors.append("date_range.start must be a valid ISO 8601 date")

                if 'end' in date_range:
                    try:
                        datetime.fromisoformat(date_range['end'].replace('Z', '+00:00'))
                    except ValueError:
                        errors.append("date_range.end must be a valid ISO 8601 date")

        if errors:
            raise ValueError(f"Request validation failed: {'; '.join(errors)}")

        # Sanitize and return validated request
        validated_request = {
            'user_id': sanitize_text_input(request_data['user_id']) if SECURITY_MODULES_AVAILABLE else request_data['user_id'],
            'request_type': request_data['request_type'],
            'data_types': request_data.get('data_types', ['all']),
            'date_range': request_data.get('date_range', {}),
            'include_raw': request_data.get('include_raw', False),
            'apply_differential_privacy': request_data.get('apply_differential_privacy', True),
            'request_id': generate_secure_token(16),
            'created_at': datetime.now(UTC).isoformat(),
            'status': 'pending'
        }

        return validated_request


def create_audit_record(request_data: dict[str, Any], action: str, result: str = 'success') -> None:
    """Create audit record for DSAR operations"""
    audit_record = {
        'timestamp': datetime.now(UTC).isoformat(),
        'request_id': request_data.get('request_id', 'unknown'),
        'user_id': safe_log(request_data.get('user_id', 'unknown')),
        'action': action,
        'request_type': request_data.get('request_type', 'unknown'),
        'result': result,
        'compliance_framework': 'GDPR',
        'retention_period_days': 2555  # 7 years for compliance records
    }

    logger.info("DSAR audit record", extra=audit_record)

    # TODO: In production, also store in dedicated audit database/table


def generate_presigned_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """Generate presigned URL for secure file access"""
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        logger.error("Failed to generate presigned URL", extra={'error': str(e), 'bucket': bucket, 'key': key})
        raise


def handle_dsar_request(event: dict[str, Any]) -> dict[str, Any]:
    """Handle new DSAR request"""
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        # Validate request
        validated_request = DSARRequestValidator.validate_request(body)

        # Create audit record
        create_audit_record(validated_request, 'dsar_request_initiated')

        # Start Step Functions execution
        execution_input = {
            'request': validated_request,
            'execution_name': f"dsar-{validated_request['request_id']}"
        }

        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_input['execution_name'],
            input=json.dumps(execution_input)
        )

        logger.info(
            "DSAR workflow started",
            extra={
                'request_id': validated_request['request_id'],
                'execution_arn': response['executionArn'],
                'user_id': safe_log(validated_request['user_id'])
            }
        )

        # Return response
        return {
            'statusCode': 202,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'request_id': validated_request['request_id'],
                'status': 'processing',
                'message': 'DSAR request submitted successfully',
                'estimated_completion': (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
                'execution_arn': response['executionArn']
            })
        }

    except ValueError as e:
        logger.error("DSAR request validation failed", extra={'error': str(e)})
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid request', 'details': str(e)})
        }

    except Exception as e:
        logger.error("Failed to process DSAR request", extra={'error': str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_dsar_status(event: dict[str, Any]) -> dict[str, Any]:
    """Handle DSAR status check"""
    try:
        # Extract request ID from path
        path_parameters = event.get('pathParameters', {})
        request_id = path_parameters.get('request_id')

        if not request_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'request_id is required'})
            }

        # Find execution by name
        execution_name = f"dsar-{request_id}"

        try:
            # Get execution status
            execution_arn = f"{STATE_MACHINE_ARN.rsplit(':', 1)[0]}:execution:PettyDSARWorkflow:{execution_name}"

            response = stepfunctions.describe_execution(executionArn=execution_arn)

            status_map = {
                'RUNNING': 'processing',
                'SUCCEEDED': 'completed',
                'FAILED': 'failed',
                'TIMED_OUT': 'failed',
                'ABORTED': 'cancelled'
            }

            status = status_map.get(response['status'], 'unknown')

            result = {
                'request_id': request_id,
                'status': status,
                'started_at': response['startDate'].isoformat(),
                'last_updated': datetime.now(UTC).isoformat()
            }

            if status == 'completed' and response.get('output'):
                output = json.loads(response['output'])
                if 'download_url' in output:
                    result['download_url'] = output['download_url']
                    result['download_expires_at'] = (datetime.now(UTC) + timedelta(hours=24)).isoformat()

            if status == 'failed' and response.get('error'):
                result['error'] = response['error']

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }

        except stepfunctions.exceptions.ExecutionDoesNotExist:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'DSAR request not found'})
            }

    except Exception as e:
        logger.error("Failed to check DSAR status", extra={'error': str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_step_function_action(event: dict[str, Any]) -> dict[str, Any]:
    """Handle Step Functions actions (validate, generate_presigned_url)"""
    action = event.get('action')
    request_data = event.get('request', {})

    if action == 'validate':
        # Request is already validated, just return it
        return request_data

    elif action == 'generate_presigned_url':
        # Generate presigned URL for completed export
        export_key = f"exports/{request_data['request_id']}/export.zip"

        try:
            download_url = generate_presigned_url(
                bucket=DSAR_BUCKET,
                key=export_key,
                expiration=86400  # 24 hours
            )

            result = request_data.copy()
            result['download_url'] = download_url
            result['download_expires_at'] = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
            result['status'] = 'completed'

            # Create audit record
            create_audit_record(request_data, 'dsar_export_url_generated')

            return result

        except Exception as e:
            logger.error("Failed to generate presigned URL", extra={'error': str(e)})
            raise

    else:
        raise ValueError(f"Unknown action: {action}")


@tracer.capture_lambda_handler if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@logger.inject_lambda_context(log_event=True) if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@rate_limit_decorator("dsar", tokens=5) if SECURITY_MODULES_AVAILABLE else lambda x: x
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    AWS Lambda handler for DSAR operations
    
    Handles:
    - HTTP API requests for DSAR initiation and status
    - Step Functions task execution
    """
    try:
        # Check if this is an HTTP API request or Step Functions task
        if 'httpMethod' in event or 'requestContext' in event:
            # HTTP API request
            path = event.get('requestContext', {}).get('http', {}).get('path', '')
            method = event.get('requestContext', {}).get('http', {}).get('method', '')

            if method == 'POST' and path == '/dsar/request':
                return handle_dsar_request(event)
            elif method == 'GET' and '/dsar/status/' in path:
                return handle_dsar_status(event)
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Not found'})
                }
        else:
            # Step Functions task
            return handle_step_function_action(event)

    except RateLimitExceeded if SECURITY_MODULES_AVAILABLE else Exception:
        return {
            'statusCode': 429,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Rate limit exceeded'})
        }

    except Exception as e:
        logger.error("Unhandled error in DSAR processor", extra={'error': str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
