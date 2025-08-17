"""
Authentication and authorization utilities
"""

import base64
import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any


class TokenManager:
    """Simple token management for API authentication (mock JWT)"""

    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or secrets.token_hex(32)

    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate a simple token for user authentication"""
        payload = {
            'user_id': user_id,
            'exp': (datetime.now(UTC) + timedelta(seconds=expires_in)).isoformat(),
            'iat': datetime.now(UTC).isoformat()
        }

        # Simple base64 encoding (not secure, for testing only)
        token_data = json.dumps(payload)
        token = base64.b64encode(token_data.encode()).decode()
        return f"token_{token}"

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode a token"""
        try:
            if not token.startswith("token_"):
                return None

            token_data = token[6:]  # Remove "token_" prefix
            decoded = base64.b64decode(token_data).decode()
            payload = json.loads(decoded)

            # Check expiration
            exp_time = datetime.fromisoformat(payload['exp'])
            if exp_time < datetime.now(UTC):
                return None

            return payload
        except Exception:
            return None

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
            'created_at': datetime.now(UTC),
            'active': True
        }

        return api_key

    def verify_api_key(self, api_key: str) -> str | None:
        """Verify an API key and return the service name"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash in self.api_keys and self.api_keys[key_hash]['active']:
            return self.api_keys[key_hash]['service_name']

        return None

# Global instances for backward compatibility
token_manager = TokenManager()
api_key_manager = APIKeyManager()

def verify_jwt_token(token: str) -> dict[str, Any] | None:
    """Verify JWT token using global token manager"""
    return token_manager.verify_token(token)

def generate_api_key(service_name: str) -> str:
    """Generate API key using global manager"""
    return api_key_manager.generate_api_key(service_name)

def verify_api_key(api_key: str) -> str | None:
    """Verify API key using global manager"""
    return api_key_manager.verify_api_key(api_key)

# Backward compatibility alias
AuthManager = TokenManager

def create_jwt_token(user_id: str, expires_in: int = 3600) -> str:
    """Create a JWT token using global token manager"""
    return token_manager.generate_token(user_id, expires_in)

def require_auth(func):
    """Decorator to require authentication for function"""
    def wrapper(*args, **kwargs):
        # Mock authentication check
        return func(*args, **kwargs)
    return wrapper
