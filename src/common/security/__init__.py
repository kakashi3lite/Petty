"""
Common security module providing OWASP LLM Top 10 mitigations.

This module implements security controls for:
- Input validation and sanitization
- Output schema validation
- Rate limiting
- Data redaction
- Authentication/Authorization
- Cryptographic operations
"""

from .input_validators import (
    InputValidator,
    validate_collar_data,
    validate_user_feedback,
    sanitize_text_input,
)
from .output_schemas import (
    OutputValidator,
    validate_timeline_output,
    validate_behavior_output,
    secure_response_wrapper,
)
from .rate_limiter import (
    RateLimiter,
    rate_limit_decorator,
    CircuitBreaker,
)
from .redaction import (
    DataRedactor,
    redact_pii,
    safe_log,
)
from .crypto_utils import (
    SecureCrypto,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    generate_secure_token,
)
from .auth import (
    AuthManager,
    ProductionTokenManager,
    TokenPair,
    verify_jwt_token,
    create_jwt_token,
    create_token_pair,
    refresh_token_pair,
    revoke_refresh_token,
    require_auth,
)

__all__ = [
    "InputValidator",
    "validate_collar_data",
    "validate_user_feedback",
    "sanitize_text_input",
    "OutputValidator",
    "validate_timeline_output",
    "validate_behavior_output",
    "secure_response_wrapper",
    "RateLimiter",
    "rate_limit_decorator",
    "CircuitBreaker",
    "DataRedactor",
    "redact_pii",
    "safe_log",
    "SecureCrypto",
    "encrypt_sensitive_data",
    "decrypt_sensitive_data",
    "generate_secure_token",
    "AuthManager",
    "ProductionTokenManager",
    "TokenPair",
    "verify_jwt_token",
    "create_jwt_token",
    "create_token_pair",
    "refresh_token_pair",
    "revoke_refresh_token",
    "require_auth",
]
