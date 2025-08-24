## Multi-stage Dockerfile for Petty FastAPI service
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps (security & performance minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --upgrade pip && \
    pip install . && \
    pip install gunicorn

EXPOSE 8080

ENV PORT=8080 SERVICE_NAME=petty-api ENVIRONMENT=production

CMD ["gunicorn", "api_service:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60"]
