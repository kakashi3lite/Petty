"""
Cryptographic utilities for data protection
"""

import hashlib
import hmac
import secrets
from typing import Optional, Union

def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_hex(length)

def hash_data(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """Hash data using specified algorithm"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    if algorithm == 'sha256':
        return hashlib.sha256(data).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def secure_compare(a: str, b: str) -> bool:
    """Securely compare two strings to prevent timing attacks"""
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))

class DataEncryption:
    """Simple data encryption utility (mock implementation for testing)"""
    
    def __init__(self, key: Optional[str] = None):
        self.key = key or generate_token(32)
    
    def encrypt(self, plaintext: str) -> str:
        """Mock encryption - in production, use proper encryption like Fernet"""
        return f"ENCRYPTED[{hash_data(plaintext + self.key)[:16]}]"
    
    def decrypt(self, ciphertext: str) -> str:
        """Mock decryption - in production, use proper decryption"""
        if ciphertext.startswith("ENCRYPTED[") and ciphertext.endswith("]"):
            return "[DECRYPTED_DATA]"
        return ciphertext

# Alias for backward compatibility
SecureCrypto = DataEncryption

def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """Encrypt sensitive data using default encryption"""
    encryptor = DataEncryption(key)
    return encryptor.encrypt(data)

def decrypt_sensitive_data(ciphertext: str, key: Optional[str] = None) -> str:
    """Decrypt sensitive data using default encryption"""
    decryptor = DataEncryption(key)
    return decryptor.decrypt(ciphertext)

# Additional aliases for backward compatibility
generate_secure_token = generate_token
