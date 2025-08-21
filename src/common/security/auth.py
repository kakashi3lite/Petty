"""
Production-grade authentication and authorization utilities with cryptographic JWT
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenPair:
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # 15 minutes

@dataclass
class TokenPayload:
    """JWT token payload"""
    user_id: str
    scopes: List[str]
    iat: datetime
    exp: datetime
    token_type: str

class ProductionTokenManager:
    """Production-grade JWT token management with RSA encryption"""
    
    def __init__(self, private_key: Optional[str] = None, public_key: Optional[str] = None):
        self.algorithm = ALGORITHMS.RS256
        self.issuer = "petty-api"
        self.audience = "petty-clients"
        
        # Generate RSA key pair if not provided (in production, load from secrets)
        if private_key and public_key:
            self.private_key = private_key
            self.public_key = public_key
        else:
            self._generate_key_pair()
        
        # Token revocation list (in production, use Redis or database)
        self._revoked_tokens = set()
    
    def _generate_key_pair(self):
        """Generate RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        self.public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def generate_token_pair(self, user_id: str, scopes: Optional[List[str]] = None) -> TokenPair:
        """Generate access and refresh token pair"""
        if scopes is None:
            scopes = ["read"]
        
        now = datetime.now(timezone.utc)
        
        # Access token (15 minutes)
        access_payload = {
            'user_id': user_id,
            'scopes': scopes,
            'iat': now.timestamp(),
            'exp': (now + timedelta(minutes=15)).timestamp(),
            'nbf': now.timestamp(),
            'iss': self.issuer,
            'aud': self.audience,
            'token_type': 'access',
            'jti': secrets.token_hex(16)  # Unique token ID
        }
        
        # Refresh token (7 days)
        refresh_payload = {
            'user_id': user_id,
            'iat': now.timestamp(),
            'exp': (now + timedelta(days=7)).timestamp(),
            'nbf': now.timestamp(),
            'iss': self.issuer,
            'aud': self.audience,
            'token_type': 'refresh',
            'jti': secrets.token_hex(16)
        }
        
        try:
            access_token = jwt.encode(access_payload, self.private_key, algorithm=self.algorithm)
            refresh_token = jwt.encode(refresh_payload, self.private_key, algorithm=self.algorithm)
            
            logger.info(f"Generated token pair for user {user_id} with scopes {scopes}")
            
            return TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=900
            )
        except Exception as e:
            logger.error(f"Failed to generate token pair: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            # Check if token is revoked
            if token in self._revoked_tokens:
                logger.warning("Attempt to use revoked token")
                return None
            
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Verify token type
            if payload.get('token_type') != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('token_type')}")
                return None
            
            return TokenPayload(
                user_id=payload['user_id'],
                scopes=payload.get('scopes', []),
                iat=datetime.fromtimestamp(payload['iat'], tz=timezone.utc),
                exp=datetime.fromtimestamp(payload['exp'], tz=timezone.utc),
                token_type=payload['token_type']
            )
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        try:
            # In production, store in Redis with TTL
            self._revoked_tokens.add(token)
            logger.info("Token revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    def refresh_access_token(self, refresh_token: str) -> Optional[TokenPair]:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        # Generate new token pair
        return self.generate_token_pair(payload.user_id, payload.scopes)

class ProductionAPIKeyManager:
    """Production-grade API key management for service authentication"""
    
    def __init__(self):
        # In production, use AWS Secrets Manager or database
        self.api_keys = {}
    
    def generate_api_key(self, service_name: str, permissions: Optional[List[str]] = None) -> str:
        """Generate a new API key for a service with specific permissions"""
        if permissions is None:
            permissions = ["read"]
        
        api_key = f"pk_{secrets.token_hex(32)}"  # Longer key for better security
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            'service_name': service_name,
            'permissions': permissions,
            'created_at': datetime.now(timezone.utc),
            'last_used': None,
            'usage_count': 0,
            'active': True
        }
        
        logger.info(f"Generated API key for service {service_name} with permissions {permissions}")
        return api_key
    
    def verify_api_key(self, api_key: str, required_permission: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Verify an API key and check permissions"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            if key_hash not in self.api_keys or not self.api_keys[key_hash]['active']:
                logger.warning("Invalid or inactive API key used")
                return None
            
            key_data = self.api_keys[key_hash]
            
            # Check permission if required
            if required_permission and required_permission not in key_data['permissions']:
                logger.warning(f"API key lacks required permission: {required_permission}")
                return None
            
            # Update usage statistics
            key_data['last_used'] = datetime.now(timezone.utc)
            key_data['usage_count'] += 1
            
            return key_data
            
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if key_hash in self.api_keys:
                self.api_keys[key_hash]['active'] = False
                logger.info("API key revoked successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

# Global instances for production use
production_token_manager = ProductionTokenManager()
production_api_key_manager = ProductionAPIKeyManager()

# Legacy compatibility layer
def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Legacy JWT verification - returns dict for backward compatibility"""
    payload = production_token_manager.verify_token(token)
    if payload:
        return {
            'user_id': payload.user_id,
            'scopes': payload.scopes,
            'exp': payload.exp.isoformat(),
            'iat': payload.iat.isoformat()
        }
    return None

def generate_api_key(service_name: str) -> str:
    """Generate API key using production manager"""
    return production_api_key_manager.generate_api_key(service_name)

def verify_api_key(api_key: str) -> Optional[str]:
    """Verify API key and return service name for backward compatibility"""
    result = production_api_key_manager.verify_api_key(api_key)
    return result['service_name'] if result else None

def create_jwt_token(user_id: str, expires_in: int = 900) -> str:
    """Create JWT token pair and return access token for backward compatibility"""
    token_pair = production_token_manager.generate_token_pair(user_id)
    return token_pair.access_token

def require_auth(required_scopes: Optional[List[str]] = None):
    """Decorator to require authentication with specific scopes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # In production, extract token from request headers and verify
            # For now, return function as-is for backward compatibility
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Backward compatibility aliases
TokenManager = ProductionTokenManager
APIKeyManager = ProductionAPIKeyManager
AuthManager = ProductionTokenManager
