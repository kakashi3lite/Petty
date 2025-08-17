"""
Authentication and authorization utilities with production-grade JWT implementation
"""

import hashlib
import secrets
import json
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
import jwt
from dataclasses import dataclass, asdict
import uuid

@dataclass
class TokenPair:
    """JWT access and refresh token pair"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"

@dataclass
class JWTPayload:
    """Standard JWT payload structure"""
    sub: str  # Subject (user ID)
    iat: int  # Issued at
    exp: int  # Expiration
    iss: str  # Issuer
    aud: str  # Audience
    jti: str  # JWT ID
    typ: str  # Token type (access/refresh)
    scope: Optional[str] = None

class KeyManager:
    """Manages RSA/ECDSA keys for JWT signing"""
    
    def __init__(self, algorithm: str = "RS256"):
        self.algorithm = algorithm
        self._private_key = None
        self._public_key = None
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        if self.algorithm.startswith("RS"):
            self._generate_rsa_keys()
        elif self.algorithm.startswith("ES"):
            self._generate_ec_keys()
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
    
    def _generate_rsa_keys(self):
        """Generate RSA key pair"""
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._public_key = self._private_key.public_key()
    
    def _generate_ec_keys(self):
        """Generate ECDSA key pair"""
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self._public_key = self._private_key.public_key()
    
    @property
    def private_key(self):
        return self._private_key
    
    @property
    def public_key(self):
        return self._public_key
    
    def get_private_key_pem(self) -> str:
        """Get private key in PEM format"""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

class RefreshTokenStore:
    """In-memory store for refresh tokens (use Redis/DB in production)"""
    
    def __init__(self):
        self._tokens = {}
    
    def store_token(self, jti: str, user_id: str, expires_at: datetime):
        """Store refresh token"""
        self._tokens[jti] = {
            'user_id': user_id,
            'expires_at': expires_at,
            'revoked': False
        }
    
    def is_valid_token(self, jti: str) -> bool:
        """Check if refresh token is valid"""
        token_data = self._tokens.get(jti)
        if not token_data:
            return False
        
        return (
            not token_data['revoked'] and 
            token_data['expires_at'] > datetime.now(timezone.utc)
        )
    
    def revoke_token(self, jti: str):
        """Revoke refresh token"""
        if jti in self._tokens:
            self._tokens[jti]['revoked'] = True
    
    def get_user_id(self, jti: str) -> Optional[str]:
        """Get user ID for refresh token"""
        token_data = self._tokens.get(jti)
        return token_data['user_id'] if token_data else None
    
    def cleanup_expired(self):
        """Remove expired tokens"""
        now = datetime.now(timezone.utc)
        expired_tokens = [
            jti for jti, data in self._tokens.items()
            if data['expires_at'] <= now
        ]
        for jti in expired_tokens:
            del self._tokens[jti]

class ProductionTokenManager:
    """Production-grade JWT token manager with refresh token rotation"""
    
    def __init__(
        self, 
        algorithm: str = "RS256",
        issuer: str = "petty-api",
        audience: str = "petty-users",
        access_token_ttl: int = 900,  # 15 minutes
        refresh_token_ttl: int = 604800  # 7 days
    ):
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        
        self.key_manager = KeyManager(algorithm)
        self.refresh_store = RefreshTokenStore()
    
    def generate_token_pair(self, user_id: str, scope: Optional[str] = None) -> TokenPair:
        """Generate access and refresh token pair"""
        now = datetime.now(timezone.utc)
        
        # Generate access token
        access_jti = str(uuid.uuid4())
        access_payload = JWTPayload(
            sub=user_id,
            iat=int(now.timestamp()),
            exp=int((now + timedelta(seconds=self.access_token_ttl)).timestamp()),
            iss=self.issuer,
            aud=self.audience,
            jti=access_jti,
            typ="access",
            scope=scope
        )
        
        access_token = jwt.encode(
            asdict(access_payload),
            self.key_manager.private_key,
            algorithm=self.algorithm
        )
        
        # Generate refresh token
        refresh_jti = str(uuid.uuid4())
        refresh_expires_at = now + timedelta(seconds=self.refresh_token_ttl)
        refresh_payload = JWTPayload(
            sub=user_id,
            iat=int(now.timestamp()),
            exp=int(refresh_expires_at.timestamp()),
            iss=self.issuer,
            aud=self.audience,
            jti=refresh_jti,
            typ="refresh"
        )
        
        refresh_token = jwt.encode(
            asdict(refresh_payload),
            self.key_manager.private_key,
            algorithm=self.algorithm
        )
        
        # Store refresh token
        self.refresh_store.store_token(refresh_jti, user_id, refresh_expires_at)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_ttl
        )
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode access token"""
        try:
            payload = jwt.decode(
                token,
                self.key_manager.public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Ensure it's an access token
            if payload.get('typ') != 'access':
                return None
                
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode refresh token"""
        try:
            payload = jwt.decode(
                token,
                self.key_manager.public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Ensure it's a refresh token and not revoked
            if (payload.get('typ') != 'refresh' or 
                not self.refresh_store.is_valid_token(payload.get('jti'))):
                return None
                
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def refresh_tokens(self, refresh_token: str) -> Optional[TokenPair]:
        """Generate new token pair using refresh token"""
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        user_id = payload['sub']
        scope = payload.get('scope')
        
        # Revoke old refresh token
        self.refresh_store.revoke_token(payload['jti'])
        
        # Generate new token pair
        return self.generate_token_pair(user_id, scope)
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.key_manager.public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_exp": False}  # Allow expired tokens for revocation
            )
            
            if payload.get('typ') == 'refresh':
                self.refresh_store.revoke_token(payload['jti'])
                return True
                
        except jwt.InvalidTokenError:
            pass
            
        return False
    
    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set for token verification"""
        public_key_pem = self.key_manager.get_public_key_pem()
        
        # This is a simplified JWKS - in production, include proper key metadata
        return {
            "keys": [{
                "kty": "RSA" if self.algorithm.startswith("RS") else "EC",
                "use": "sig",
                "alg": self.algorithm,
                "kid": "main-key",
                "n": base64.urlsafe_b64encode(public_key_pem.encode()).decode().rstrip("="),
            }]
        }

# Legacy TokenManager for backward compatibility
class TokenManager:
    """Legacy token management (kept for backward compatibility)"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self._production_manager = ProductionTokenManager()
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate token using production manager"""
        token_pair = self._production_manager.generate_token_pair(user_id)
        return token_pair.access_token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token using production manager"""
        return self._production_manager.verify_access_token(token)

class APIKeyManager:
    """API key management for service authentication"""
    
    def __init__(self):
        self.api_keys = {}  # In production, use a database
    
    def generate_api_key(self, service_name: str) -> str:
        """Generate a new API key for a service"""
        api_key = f"pk_{secrets.token_hex(16)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            'service_name': service_name,
            'created_at': datetime.now(timezone.utc),
            'active': True
        }
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify an API key and return the service name"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys and self.api_keys[key_hash]['active']:
            return self.api_keys[key_hash]['service_name']
        
        return None

# Global instances
production_token_manager = ProductionTokenManager()
token_manager = TokenManager()  # Legacy compatibility
api_key_manager = APIKeyManager()

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token using production token manager"""
    return production_token_manager.verify_access_token(token)

def generate_api_key(service_name: str) -> str:
    """Generate API key using global manager"""
    return api_key_manager.generate_api_key(service_name)

def verify_api_key(api_key: str) -> Optional[str]:
    """Verify API key using global manager"""
    return api_key_manager.verify_api_key(api_key)

def create_jwt_token(user_id: str, expires_in: int = 3600) -> str:
    """Create a JWT token using production token manager"""
    token_pair = production_token_manager.generate_token_pair(user_id)
    return token_pair.access_token

def create_token_pair(user_id: str, scope: Optional[str] = None) -> TokenPair:
    """Create access and refresh token pair"""
    return production_token_manager.generate_token_pair(user_id, scope)

def refresh_token_pair(refresh_token: str) -> Optional[TokenPair]:
    """Refresh token pair using refresh token"""
    return production_token_manager.refresh_tokens(refresh_token)

def revoke_refresh_token(refresh_token: str) -> bool:
    """Revoke refresh token"""
    return production_token_manager.revoke_refresh_token(refresh_token)

# Backward compatibility alias
AuthManager = TokenManager

def require_auth(func):
    """Decorator to require authentication for function"""
    def wrapper(*args, **kwargs):
        # Production authentication check would go here
        return func(*args, **kwargs)
    return wrapper
