"""
Production-grade secrets management using AWS Secrets Manager and SSM Parameter Store
Provides secure, cached, and rotatable secret management for the Petty application
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from dataclasses import dataclass
from enum import Enum
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class SecretType(Enum):
    """Types of secrets managed by the system"""
    JWT_KEYS = "jwt_keys"
    DATABASE_CREDENTIALS = "database_credentials"
    API_KEYS = "api_keys"
    ENCRYPTION_KEYS = "encryption_keys"
    THIRD_PARTY_TOKENS = "third_party_tokens"

@dataclass
class SecretMetadata:
    """Metadata for cached secrets"""
    secret_name: str
    secret_type: SecretType
    cached_at: datetime
    ttl_seconds: int
    version_id: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the cached secret has expired"""
        expiry_time = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry_time

class ProductionSecretsManager:
    """
    Production-grade secrets management with caching, encryption, and rotation support
    
    Features:
    - AWS Secrets Manager integration
    - SSM Parameter Store support
    - In-memory caching with TTL
    - Automatic secret rotation handling
    - Local encryption for sensitive data
    - Comprehensive audit logging
    """
    
    def __init__(self, 
                 region_name: str = None, 
                 cache_ttl_seconds: int = 300,
                 enable_local_encryption: bool = True):
        """
        Initialize the secrets manager
        
        Args:
            region_name: AWS region for secrets (defaults to environment)
            cache_ttl_seconds: Time to live for cached secrets (default: 5 minutes)
            enable_local_encryption: Whether to encrypt cached secrets locally
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_local_encryption = enable_local_encryption
        
        # Initialize AWS clients
        try:
            self.secrets_client = boto3.client('secretsmanager', region_name=self.region_name)
            self.ssm_client = boto3.client('ssm', region_name=self.region_name)
        except NoCredentialsError:
            logger.warning("AWS credentials not found - using fallback mode")
            self.secrets_client = None
            self.ssm_client = None
        
        # In-memory cache
        self._cache: Dict[str, tuple] = {}  # secret_name -> (encrypted_data, metadata)
        
        # Local encryption key (derived from environment)
        if enable_local_encryption:
            self._encryption_key = self._derive_encryption_key()
        else:
            self._encryption_key = None
        
        logger.info(f"Secrets manager initialized for region {self.region_name}")
    
    def _derive_encryption_key(self) -> Fernet:
        """Derive encryption key from environment for local secret encryption"""
        # Use a combination of environment variables to derive key
        seed = os.getenv("SECRET_ENCRYPTION_SEED", "petty-default-seed-change-in-production")
        salt = os.getenv("SECRET_ENCRYPTION_SALT", "petty-salt").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(seed.encode()))
        return Fernet(key)
    
    def _encrypt_local_data(self, data: str) -> str:
        """Encrypt data for local caching"""
        if not self._encryption_key:
            return data
        return self._encryption_key.encrypt(data.encode()).decode()
    
    def _decrypt_local_data(self, encrypted_data: str) -> str:
        """Decrypt locally cached data"""
        if not self._encryption_key:
            return encrypted_data
        return self._encryption_key.decrypt(encrypted_data.encode()).decode()
    
    async def get_secret(self, 
                        secret_name: str, 
                        secret_type: SecretType = SecretType.API_KEYS,
                        force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get secret from AWS Secrets Manager with caching
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            secret_type: Type of secret for categorization
            force_refresh: Force refresh from AWS (bypass cache)
            
        Returns:
            Secret data as dictionary or None if not found
        """
        # Check cache first (unless force refresh)
        if not force_refresh and secret_name in self._cache:
            encrypted_data, metadata = self._cache[secret_name]
            
            if not metadata.is_expired:
                try:
                    decrypted_data = self._decrypt_local_data(encrypted_data)
                    logger.debug(f"Retrieved secret {secret_name} from cache")
                    return json.loads(decrypted_data)
                except Exception as e:
                    logger.warning(f"Failed to decrypt cached secret {secret_name}: {e}")
                    # Continue to fetch from AWS
        
        # Fetch from AWS Secrets Manager
        if not self.secrets_client:
            logger.error("AWS Secrets Manager client not available")
            return None
        
        try:
            logger.info(f"Fetching secret {secret_name} from AWS Secrets Manager")
            
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            
            # Cache the secret
            metadata = SecretMetadata(
                secret_name=secret_name,
                secret_type=secret_type,
                cached_at=datetime.now(timezone.utc),
                ttl_seconds=self.cache_ttl_seconds,
                version_id=response.get('VersionId')
            )
            
            encrypted_data = self._encrypt_local_data(json.dumps(secret_data))
            self._cache[secret_name] = (encrypted_data, metadata)
            
            logger.info(f"Successfully retrieved and cached secret {secret_name}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Secret {secret_name} not found in AWS Secrets Manager")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_name}: {e}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_name}: {e}")
            else:
                logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None
    
    async def get_parameter(self, 
                           parameter_name: str, 
                           decrypt: bool = True,
                           force_refresh: bool = False) -> Optional[str]:
        """
        Get parameter from AWS SSM Parameter Store
        
        Args:
            parameter_name: Name of the parameter
            decrypt: Whether to decrypt SecureString parameters
            force_refresh: Force refresh from AWS (bypass cache)
            
        Returns:
            Parameter value or None if not found
        """
        cache_key = f"param_{parameter_name}"
        
        # Check cache first
        if not force_refresh and cache_key in self._cache:
            encrypted_data, metadata = self._cache[cache_key]
            
            if not metadata.is_expired:
                try:
                    decrypted_data = self._decrypt_local_data(encrypted_data)
                    logger.debug(f"Retrieved parameter {parameter_name} from cache")
                    return decrypted_data
                except Exception as e:
                    logger.warning(f"Failed to decrypt cached parameter {parameter_name}: {e}")
        
        # Fetch from SSM
        if not self.ssm_client:
            logger.error("AWS SSM client not available")
            return None
        
        try:
            logger.info(f"Fetching parameter {parameter_name} from SSM Parameter Store")
            
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            
            parameter_value = response['Parameter']['Value']
            
            # Cache the parameter
            metadata = SecretMetadata(
                secret_name=cache_key,
                secret_type=SecretType.API_KEYS,  # Default type for parameters
                cached_at=datetime.now(timezone.utc),
                ttl_seconds=self.cache_ttl_seconds
            )
            
            encrypted_data = self._encrypt_local_data(parameter_value)
            self._cache[cache_key] = (encrypted_data, metadata)
            
            logger.info(f"Successfully retrieved and cached parameter {parameter_name}")
            return parameter_value
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                logger.warning(f"Parameter {parameter_name} not found in SSM")
            else:
                logger.error(f"Failed to retrieve parameter {parameter_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving parameter {parameter_name}: {e}")
            return None
    
    def get_jwt_keys(self) -> Optional[Dict[str, str]]:
        """Get JWT signing keys from secrets manager"""
        import asyncio
        try:
            return asyncio.run(self.get_secret("petty/jwt-keys", SecretType.JWT_KEYS))
        except Exception as e:
            logger.error(f"Failed to retrieve JWT keys: {e}")
            return None
    
    def get_database_credentials(self, database_name: str) -> Optional[Dict[str, str]]:
        """Get database credentials"""
        import asyncio
        try:
            return asyncio.run(self.get_secret(f"petty/db-{database_name}", SecretType.DATABASE_CREDENTIALS))
        except Exception as e:
            logger.error(f"Failed to retrieve database credentials for {database_name}: {e}")
            return None
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for external service"""
        import asyncio
        try:
            secret_data = asyncio.run(self.get_secret(f"petty/api-keys/{service_name}", SecretType.API_KEYS))
            return secret_data.get('api_key') if secret_data else None
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service_name}: {e}")
            return None
    
    def get_encryption_key(self, purpose: str) -> Optional[str]:
        """Get encryption key for specific purpose (e.g., 'pii', 'user-data')"""
        import asyncio
        try:
            secret_data = asyncio.run(self.get_secret(f"petty/encryption-keys/{purpose}", SecretType.ENCRYPTION_KEYS))
            return secret_data.get('key') if secret_data else None
        except Exception as e:
            logger.error(f"Failed to retrieve encryption key for {purpose}: {e}")
            return None
    
    def create_secret(self, 
                     secret_name: str, 
                     secret_data: Dict[str, Any],
                     description: str = "",
                     secret_type: SecretType = SecretType.API_KEYS) -> bool:
        """
        Create a new secret in AWS Secrets Manager
        
        Args:
            secret_name: Name for the new secret
            secret_data: Secret data as dictionary
            description: Description of the secret
            secret_type: Type of secret
            
        Returns:
            True if successful, False otherwise
        """
        if not self.secrets_client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            logger.info(f"Creating secret {secret_name} in AWS Secrets Manager")
            
            self.secrets_client.create_secret(
                Name=secret_name,
                Description=description or f"Petty {secret_type.value} secret",
                SecretString=json.dumps(secret_data),
                Tags=[
                    {'Key': 'Service', 'Value': 'Petty'},
                    {'Key': 'SecretType', 'Value': secret_type.value},
                    {'Key': 'CreatedBy', 'Value': 'PettySecretsManager'}
                ]
            )
            
            logger.info(f"Successfully created secret {secret_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                logger.warning(f"Secret {secret_name} already exists")
                return False
            else:
                logger.error(f"Failed to create secret {secret_name}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error creating secret {secret_name}: {e}")
            return False
    
    def rotate_secret(self, secret_name: str) -> bool:
        """
        Trigger secret rotation
        
        Args:
            secret_name: Name of the secret to rotate
            
        Returns:
            True if rotation started successfully
        """
        if not self.secrets_client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            logger.info(f"Starting rotation for secret {secret_name}")
            
            self.secrets_client.rotate_secret(SecretId=secret_name)
            
            # Clear from cache to force refresh
            if secret_name in self._cache:
                del self._cache[secret_name]
            
            logger.info(f"Successfully started rotation for secret {secret_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error rotating secret {secret_name}: {e}")
            return False
    
    def clear_cache(self, secret_name: Optional[str] = None) -> None:
        """
        Clear secret cache
        
        Args:
            secret_name: Specific secret to clear, or None to clear all
        """
        if secret_name:
            if secret_name in self._cache:
                del self._cache[secret_name]
                logger.info(f"Cleared cache for secret {secret_name}")
        else:
            self._cache.clear()
            logger.info("Cleared all secret cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_secrets = len(self._cache)
        expired_secrets = 0
        
        for _, (_, metadata) in self._cache.items():
            if metadata.is_expired:
                expired_secrets += 1
        
        return {
            "total_cached_secrets": total_secrets,
            "expired_secrets": expired_secrets,
            "cache_hit_ratio": 0.0,  # Would need counters to track this
            "cache_ttl_seconds": self.cache_ttl_seconds
        }

# Global secrets manager instance
secrets_manager = ProductionSecretsManager()

# Convenience functions for common operations
def get_jwt_keys() -> Optional[Dict[str, str]]:
    """Get JWT signing keys"""
    return secrets_manager.get_jwt_keys()

def get_database_url(database_name: str = "petty") -> Optional[str]:
    """Get database connection URL"""
    credentials = secrets_manager.get_database_credentials(database_name)
    if credentials:
        return f"postgresql://{credentials['username']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['database']}"
    return None

def get_external_api_key(service_name: str) -> Optional[str]:
    """Get API key for external service"""
    return secrets_manager.get_api_key(service_name)

def get_pii_encryption_key() -> Optional[str]:
    """Get encryption key for PII data"""
    return secrets_manager.get_encryption_key("pii")

# Export key components
__all__ = [
    'ProductionSecretsManager',
    'SecretType',
    'SecretMetadata',
    'secrets_manager',
    'get_jwt_keys',
    'get_database_url',
    'get_external_api_key',
    'get_pii_encryption_key'
]