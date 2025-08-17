"""
S3 utilities for secure JSON storage with server-side encryption.
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Initialize S3 client with retry configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
session = boto3.Session()
s3_client = session.client(
    's3',
    region_name=AWS_REGION,
    config=boto3.session.Config(
        retries={'max_attempts': 3, 'mode': 'adaptive'},
        max_pool_connections=50
    )
)


def put_json(bucket: str, key: str, data: dict[str, Any],
             metadata: dict[str, str] | None = None) -> dict[str, Any]:
    """
    Put JSON data to S3 with server-side encryption (SSE-S3).

    Args:
        bucket: S3 bucket name
        key: S3 object key
        data: Dictionary to store as JSON
        metadata: Optional metadata to attach to the object

    Returns:
        S3 put_object response

    Raises:
        ClientError: If S3 operation fails
        ValueError: If data cannot be serialized to JSON
    """
    try:
        # Serialize data to JSON
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

        # Prepare put_object parameters
        put_params = {
            'Bucket': bucket,
            'Key': key,
            'Body': json_str,
            'ContentType': 'application/json',
            'ServerSideEncryption': 'AES256',  # SSE-S3
        }

        # Add metadata if provided
        if metadata:
            put_params['Metadata'] = metadata

        # Put object to S3
        response = s3_client.put_object(**put_params)

        logger.info(
            f"Successfully stored JSON to S3: bucket={bucket}, key={key}, etag={response.get('ETag')}, size={len(json_str)}"
        )

        return response

    except ValueError as e:
        logger.error(f"Failed to serialize data to JSON: {e}")
        raise ValueError(f"Data cannot be serialized to JSON: {e}") from e

    except ClientError as e:
        logger.error(f"Failed to put JSON to S3: bucket={bucket}, key={key}, error={e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error putting JSON to S3: bucket={bucket}, key={key}, error={e}")
        raise
