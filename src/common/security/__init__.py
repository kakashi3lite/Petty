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

from .auth import (
    AuthManager,
    create_jwt_token,
    require_auth,
    verify_jwt_token,
)
from .crypto_utils import (
    SecureCrypto,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    generate_secure_token,
)
from .input_validators import (
    InputValidator,
    sanitize_text_input,
    validate_collar_data,
    validate_user_feedback,
)
from .output_schemas import (
    OutputValidator,
    secure_response_wrapper,
    validate_behavior_output,
    validate_timeline_output,
)
from .rate_limiter import (
    CircuitBreaker,
    RateLimiter,
    rate_limit_decorator,
)
from .redaction import (
    DataRedactor,
    redact_pii,
    safe_log,
)

__all__ = [
    "AuthManager",
    "CircuitBreaker",
    "DataRedactor",
    "InputValidator",
    "OutputValidator",
    "RateLimiter",
    "SecureCrypto",
    "create_jwt_token",
    "decrypt_sensitive_data",
    "encrypt_sensitive_data",
    "generate_secure_token",
    "rate_limit_decorator",
    "redact_pii",
    "require_auth",
    "safe_log",
    "sanitize_text_input",
    "secure_response_wrapper",
    "validate_behavior_output",
    "validate_collar_data",
    "validate_timeline_output",
    "validate_user_feedback",
    "verify_jwt_token",
]
