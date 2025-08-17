"""
Data redaction utilities for privacy compliance
"""

import re
from typing import Any

# Common patterns for redaction
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')

def redact_email(text: str, replacement: str = "[EMAIL_REDACTED]") -> str:
    """Redact email addresses from text"""
    return EMAIL_PATTERN.sub(replacement, text)

def redact_phone(text: str, replacement: str = "[PHONE_REDACTED]") -> str:
    """Redact phone numbers from text"""
    return PHONE_PATTERN.sub(replacement, text)

def redact_ssn(text: str, replacement: str = "[SSN_REDACTED]") -> str:
    """Redact Social Security Numbers from text"""
    return SSN_PATTERN.sub(replacement, text)

def redact_credit_card(text: str, replacement: str = "[CARD_REDACTED]") -> str:
    """Redact credit card numbers from text"""
    return CREDIT_CARD_PATTERN.sub(replacement, text)

def redact_pii(text: str) -> str:
    """Comprehensive PII redaction"""
    if not isinstance(text, str):
        return text

    result = text
    result = redact_email(result)
    result = redact_phone(result)
    result = redact_ssn(result)
    result = redact_credit_card(result)

    return result

def redact_dict(data: dict[str, Any], keys_to_redact: list[str] | None = None) -> dict[str, Any]:
    """Redact specified keys from dictionary"""
    if keys_to_redact is None:
        keys_to_redact = ['email', 'phone', 'ssn', 'credit_card', 'password', 'token']

    result = {}
    for key, value in data.items():
        if key.lower() in [k.lower() for k in keys_to_redact]:
            result[key] = "[REDACTED]"
        elif isinstance(value, str):
            result[key] = redact_pii(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, keys_to_redact)
        elif isinstance(value, list):
            result[key] = [redact_dict(item, keys_to_redact) if isinstance(item, dict)
                          else redact_pii(item) if isinstance(item, str)
                          else item for item in value]
        else:
            result[key] = value

    return result

class DataRedactor:
    """Production-grade data redaction utility"""

    def __init__(self, keys_to_redact: list[str] | None = None):
        self.keys_to_redact = keys_to_redact or ['email', 'phone', 'ssn', 'credit_card', 'password', 'token']

    def redact_text(self, text: str) -> str:
        """Redact PII from text"""
        return redact_pii(text)

    def redact_data(self, data: str | dict[str, Any] | list[Any]) -> str | dict[str, Any] | list[Any]:
        """Redact PII from various data types"""
        if isinstance(data, str):
            return self.redact_text(data)
        elif isinstance(data, dict):
            return redact_dict(data, self.keys_to_redact)
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        else:
            return data

def safe_log(data: str | dict[str, Any] | list[Any], redactor: DataRedactor | None = None) -> str | dict[str, Any] | list[Any]:
    """Safely prepare data for logging by redacting PII"""
    if redactor is None:
        redactor = DataRedactor()

    return redactor.redact_data(data)
