# Security Documentation

## OWASP LLM Top 10 Mitigations

This document outlines how Petty implements security controls aligned with the OWASP LLM Top 10 for AI applications.

### LLM01: Prompt Injection

**Risk**: Malicious inputs could manipulate the behavioral interpreter's logic or output.

**Mitigations Implemented**:
- **Input Validation**: All collar data is validated using Pydantic models with strict field validation
- **Input Sanitization**: Text inputs are HTML-escaped and stripped of potential injection patterns
- **Schema Enforcement**: Only predefined behavior types and data formats are accepted
- **Rate Limiting**: AI inference endpoints are rate-limited to prevent abuse
- **⭐ NEW: AI Guardrails**: Comprehensive prompt injection keyword detection with 30+ injection patterns
- **⭐ NEW: Input Size Limits**: Maximum 10KB input size with field count limits (20 fields max)
- **⭐ NEW: Nested Data Sanitization**: Recursive sanitization of nested objects with depth limits

**Code References**:
- `src/common/security/input_validators.py`
- `src/behavioral_interpreter/interpreter.py`
- **⭐ NEW**: `src/common/security/guardrails.py`

**Keywords Blocked**:
- Command injection: "ignore previous instructions", "admin mode", "forget everything"
- SQL injection: "DROP TABLE", "UNION SELECT", "DELETE FROM"
- XSS: `<script>`, "javascript:", "onload="
- System commands: "rm -rf", "sudo", "exec("

### LLM02: Insecure Output Handling

**Risk**: AI-generated content could contain malicious payloads or leak sensitive information.

**Mitigations Implemented**:
- **Output Sanitization**: All AI-generated text is sanitized before display
- **Schema Validation**: Output conforms to predefined Pydantic schemas
- **Content Filtering**: Outputs are checked against allow-lists of valid behaviors
- **Length Limits**: All text outputs are length-limited to prevent overflow attacks
- **⭐ NEW: Comprehensive Output Validation**: Pydantic-based AIPlanOutput schema with field sanitization
- **⭐ NEW: Health Alert Filtering**: Automatic filtering of suspicious content in health alerts
- **⭐ NEW: Size Limits**: Maximum 50KB output size enforcement

**Code References**:
- `src/common/security/output_schemas.py`
- Behavioral interpreter output validation
- **⭐ NEW**: `src/common/security/guardrails.py` (AIPlanOutput model)

### LLM03: Training Data Poisoning

**Risk**: Not directly applicable as we use rule-based behavioral analysis, but future ML models could be vulnerable.

**Future Mitigations Planned**:
- Data provenance tracking for training datasets
- Anomaly detection in training data
- Federated learning architecture to limit exposure
- Data validation pipelines before training

### LLM04: Model Denial of Service

**Risk**: Excessive requests could overwhelm the behavioral analysis system.

**Mitigations Implemented**:
- **Rate Limiting**: Token bucket algorithm with per-collar-ID limits
- **Circuit Breakers**: Automatic failure protection with configurable thresholds
- **Input Size Limits**: Maximum data points processed per request
- **Resource Monitoring**: AWS Lambda concurrency controls and timeouts
- **⭐ NEW: AI Endpoint Rate Limiting**: Configurable per-minute/per-hour limits with IP-based keys
- **⭐ NEW: Multi-layer Rate Limiting**: Function-level and IP-level rate limiting
- **⭐ NEW: Input/Output Size Controls**: Strict limits on data size to prevent resource exhaustion

**Code References**:
- `src/common/security/rate_limiter.py`
- Lambda timeout configurations in SAM template
- **⭐ NEW**: `src/common/security/guardrails.py` (ai_rate_limit decorator)

### LLM05: Supply Chain Vulnerabilities

**Risk**: Compromised dependencies could affect the entire system.

**Mitigations Implemented**:
- **Dependency Scanning**: Automated scanning with Safety, Bandit, and GitHub Dependabot
- **SBOM Generation**: Software Bill of Materials for all components
- **Signed Artifacts**: All build artifacts signed with Cosign
- **SLSA Provenance**: Build provenance tracking with SLSA Level 3
- **Container Security**: Base images regularly updated and scanned

**Code References**:
- `.github/workflows/ci.yml`
- `.github/workflows/build-sign.yml`
- `pyproject.toml` security dependencies

### LLM06: Sensitive Information Disclosure

**Risk**: Pet data or user information could be inadvertently exposed in logs or outputs.

**Mitigations Implemented**:
- **Data Classification**: All data fields classified by sensitivity level
- **Log Redaction**: Automatic PII redaction in structured logs
- **Encryption**: KMS encryption for sensitive data at rest
- **Access Controls**: Least privilege IAM policies
- **Data Minimization**: Only necessary data collected and retained

**Code References**:
- `src/common/security/redaction.py`
- `src/common/observability/logger.py`

### LLM07: Insecure Plugin Design

**Risk**: Future extensibility features could introduce security vulnerabilities.

**Future Mitigations Planned**:
- Plugin sandboxing with strict capabilities
- Plugin signing and verification
- API allow-lists for plugin interactions
- Runtime security monitoring for plugins

### LLM08: Excessive Agency

**Risk**: AI system performing actions beyond intended scope.

**Mitigations Implemented**:
- **No Direct Actions**: Behavioral interpreter only generates reports, no direct pet actions
- **Human in the Loop**: All recommendations require human review
- **Action Allow-Lists**: Predefined set of allowed recommendation types
- **Audit Logging**: All AI decisions logged for review

**Code References**:
- Behavioral interpreter design limits agency to analysis only
- Structured logging for audit trails

### LLM09: Overreliance

**Risk**: Users trusting AI recommendations without proper validation.

**Mitigations Implemented**:
- **Confidence Scores**: All AI outputs include confidence metrics
- **Uncertainty Indicators**: Clear indication when AI is uncertain
- **Human Oversight**: Veterinary consultation features built-in
- **User Education**: Clear documentation of AI limitations
- **Feedback Loops**: User feedback collection for continuous improvement

**Code References**:
- Confidence scoring in behavioral interpreter
- Tele-vet integration in mobile app

### LLM10: Model Theft

**Risk**: Unauthorized access to AI models or training data.

**Mitigations Implemented**:
- **Access Controls**: IAM policies restricting model access
- **API Authentication**: JWT-based authentication for all endpoints
- **Rate Limiting**: Prevents model extraction through excessive queries
- **Monitoring**: Anomaly detection for unusual access patterns
- **Obfuscation**: Model logic distributed across multiple components

**Code References**:
- `src/common/security/auth.py`
- CloudWatch monitoring and alerting

## Secrets Management Policy

### Secret Types and Handling

1. **API Keys**: Stored in AWS Systems Manager Parameter Store
2. **Database Credentials**: AWS Secrets Manager with automatic rotation
3. **Encryption Keys**: AWS KMS with key rotation enabled
4. **Signing Keys**: Secure key generation and storage for artifact signing

### Secret Rotation

- Database passwords: 30-day automatic rotation
- API keys: 90-day manual rotation
- Encryption keys: Annual rotation
- Signing keys: As needed for security incidents

### Access Policies

- Secrets accessible only by authorized services
- All secret access logged and monitored
- Multi-factor authentication required for manual secret access
- Principle of least privilege enforced

## Red Team Testing Runbook

### Regular Testing Cadence

- **Monthly**: Automated vulnerability scans
- **Quarterly**: Manual penetration testing
- **Annually**: Comprehensive red team exercise

### Test Scenarios

1. **Prompt Injection Attacks**
   - Malicious collar data injection
   - Timeline manipulation attempts
   - Behavioral model confusion attacks

2. **Data Exfiltration Attempts**
   - Log injection for data leakage
   - Side-channel attacks on behavioral patterns
   - API abuse for data harvesting

3. **Denial of Service Testing**
   - Rate limit bypass attempts
   - Resource exhaustion attacks
   - Circuit breaker testing

4. **Supply Chain Attacks**
   - Dependency confusion attacks
   - Package substitution attempts
   - Build process compromise simulation

### Testing Tools

- Custom behavioral model fuzzing tools
- OWASP ZAP for API security testing
- Nuclei for vulnerability scanning
- Custom IoT security testing framework

### Reporting and Remediation

1. All findings documented in security tracking system
2. Critical issues patched within 24 hours
3. High severity issues addressed within 7 days
4. Regular issues included in quarterly security updates
5. Post-remediation validation testing required

## Incident Response Plan

### Incident Classification

- **P0 (Critical)**: Data breach, system compromise, service unavailable
- **P1 (High)**: Attempted breach, significant vulnerability, partial service impact
- **P2 (Medium)**: Minor vulnerability, limited impact
- **P3 (Low)**: Security improvement opportunities

### Response Team

- **Incident Commander**: VP Engineering or designated backup
- **Security Lead**: CISO or security team lead
- **Technical Lead**: Senior engineer familiar with affected system
- **Communications Lead**: Designated spokesperson for customer/public communication

### Response Procedures

1. **Detection and Analysis** (0-30 minutes)
   - Alert verification and initial assessment
   - Incident classification and team notification
   - Initial containment measures if needed

2. **Containment and Eradication** (30 minutes - 4 hours)
   - Isolate affected systems
   - Remove threat presence
   - Preserve evidence for investigation

3. **Recovery** (2-24 hours)
   - Restore systems from clean backups
   - Implement additional monitoring
   - Gradual service restoration with validation

4. **Post-Incident Activities** (1-7 days)
   - Comprehensive incident analysis
   - Lessons learned documentation
   - Process improvements implementation
   - Customer and stakeholder communication

### Communication Templates

- Internal incident notifications
- Customer impact communications
- Regulatory compliance notifications
- Public disclosure templates (if required)

## Compliance and Audit

### Regulatory Requirements

- **GDPR**: EU data protection compliance for pet owners
- **CCPA**: California privacy compliance
- **SOC 2 Type II**: Annual audit for service organization controls
- **ISO 27001**: Information security management system

### Audit Trail Requirements

- All user actions logged and retained for 7 years
- System changes tracked with approval workflows
- Data access logging with user identification
- Regular access reviews and privilege audits

### Data Retention Policies

- Collar telemetry data: 3 years
- User account data: Until account deletion + 30 days
- Audit logs: 7 years
- Security events: 10 years
- Backup data: Aligned with primary data retention
