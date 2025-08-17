# Multi-stage Dockerfile for Petty AI Pet Monitoring System
# Security hardened with minimal attack surface

#------------------------------------------------------------------------------
# Stage 1: Build Dependencies and Security Scanning
#------------------------------------------------------------------------------
FROM python:3.11-slim-bullseye AS builder

# Set build arguments for better security
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=dev

# Add metadata labels
LABEL maintainer="Petty Team <team@petty.ai>"
LABEL org.opencontainers.image.title="Petty AI Pet Monitoring"
LABEL org.opencontainers.image.description="AI-powered pet behavior monitoring and analytics"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL org.opencontainers.image.vendor="Petty Team"
LABEL org.opencontainers.image.licenses="MIT"

# Security: Create non-root user early
RUN groupadd -r petty && useradd -r -g petty -s /bin/false petty

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Install Python dependencies for security scanning
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir bandit safety pip-audit

# Copy source code for security analysis
COPY src/ ./src/
COPY tests/ ./tests/

# Run security scans during build
RUN bandit -r src/ -f json -o /tmp/bandit-results.json || true
RUN safety check --json --output /tmp/safety-results.json || true
RUN pip-audit --format=json --output=/tmp/audit-results.json || true

# Install application dependencies
RUN pip install --no-cache-dir -e ".[security,observability]"

#------------------------------------------------------------------------------
# Stage 2: Production Runtime
#------------------------------------------------------------------------------
FROM python:3.11-slim-bullseye AS runtime

# Set build arguments for metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=dev

# Add metadata labels
LABEL maintainer="Petty Team <team@petty.ai>"
LABEL org.opencontainers.image.title="Petty AI Pet Monitoring Runtime"
LABEL org.opencontainers.image.description="Production runtime for Petty AI system"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF

# Security hardening: Install only runtime dependencies and security updates
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Security: Create non-root user and group
RUN groupadd -r petty && useradd -r -g petty -s /bin/false -u 1001 petty

# Create app directory with proper permissions
RUN mkdir -p /app /app/logs /app/data \
    && chown -R petty:petty /app

WORKDIR /app

# Copy application code and dependencies from builder
COPY --from=builder --chown=petty:petty /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=petty:petty /usr/local/bin /usr/local/bin
COPY --from=builder --chown=petty:petty /app/src ./src
COPY --chown=petty:petty infrastructure/ ./infrastructure/

# Copy security scan results for transparency
COPY --from=builder /tmp/*-results.json ./security-reports/

# Security: Set proper file permissions
RUN chmod -R 755 /app \
    && chmod -R 644 /app/src \
    && chmod 755 /app/src

# Health check script
COPY --chown=petty:petty <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import subprocess
import json

def main():
    try:
        # Basic health checks
        import src.common.observability.logger
        import src.common.security.auth
        print("Health check passed")
        sys.exit(0)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

RUN chmod +x /app/healthcheck.py

# Security: Switch to non-root user
USER petty

# Expose port (application should bind to this port)
EXPOSE 8080

# Environment variables for security
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /app/healthcheck.py

# Default command
CMD ["python3", "-m", "src.ai_core_service"]

#------------------------------------------------------------------------------
# Stage 3: Development/Testing (Optional)
#------------------------------------------------------------------------------
FROM builder AS development

# Install development dependencies
RUN pip install --no-cache-dir -e ".[dev,security,observability]"

# Install additional development tools
RUN pip install --no-cache-dir \
    pytest-watch \
    pytest-xdist \
    ipython \
    jupyter

# Copy all source files including tests
COPY --chown=petty:petty . .

# Switch to non-root user
USER petty

# Development server command
CMD ["python3", "-m", "pytest", "--watch"]

#------------------------------------------------------------------------------
# Stage 4: CI/Security Scanning
#------------------------------------------------------------------------------
FROM builder AS security-scanner

# Install additional security tools
RUN pip install --no-cache-dir \
    semgrep \
    detect-secrets \
    cyclonedx-bom

# Copy all source code
COPY --chown=petty:petty . .

# Generate SBOM
RUN cyclonedx-py --format json --output /app/sbom.json .

# Run comprehensive security scans
RUN semgrep --config=auto src/ --json --output=/app/semgrep-results.json || true
RUN detect-secrets scan --all-files --baseline /app/.secrets.baseline || true

# Export security artifacts
CMD ["sh", "-c", "cp /app/*.json /security-output/ 2>/dev/null || true"]