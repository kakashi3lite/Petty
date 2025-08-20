# Installation Guide

Complete installation instructions for all Petty components across different platforms and deployment scenarios.

## 📋 Installation Overview

Petty can be installed in several configurations:

| Installation Type | Use Case | Complexity | Time Required |
|------------------|----------|------------|---------------|
| **Local Development** | Development & testing | Low | 15 minutes |
| **Self-Hosted** | Personal/small team use | Medium | 45 minutes |
| **Cloud Deployment** | Production use | High | 2-3 hours |
| **Docker** | Containerized deployment | Medium | 30 minutes |

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4GB
- **Storage**: 10GB available space
- **OS**: Windows 10+, macOS 12+, Ubuntu 20.04+
- **Network**: Broadband internet connection

### Recommended Requirements
- **CPU**: 4 cores, 3.0 GHz
- **RAM**: 16GB
- **Storage**: 50GB SSD
- **OS**: Windows 11, macOS 13+, Ubuntu 22.04+
- **Network**: Stable broadband with low latency

### For Production Deployment
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: 100GB+ SSD with backup
- **Network**: Enterprise-grade connection
- **Security**: Firewall, SSL certificates

## 🐍 Python Backend Installation

### Prerequisites
```bash
# Check Python version (3.11+ required)
python --version

# Check pip version
pip --version

# Install/upgrade pip if needed
python -m pip install --upgrade pip
```

### Option 1: pip Installation (Recommended)
```bash
# Clone repository
git clone https://github.com/kakashi3lite/Petty.git
cd Petty

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install Petty
pip install -e .

# Verify installation
python -c "import petty; print('✅ Petty installed successfully')"
```

### Option 2: Poetry Installation
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone https://github.com/kakashi3lite/Petty.git
cd Petty

# Install dependencies
poetry install

# Activate environment
poetry shell

# Verify installation
python -c "import petty; print('✅ Petty installed successfully')"
```

### Option 3: Conda Installation
```bash
# Create conda environment
conda create -n petty python=3.11
conda activate petty

# Clone repository
git clone https://github.com/kakashi3lite/Petty.git
cd Petty

# Install dependencies
pip install -e .

# Verify installation
python -c "import petty; print('✅ Petty installed successfully')"
```

### Development Dependencies
```bash
# Install development dependencies
pip install -e .[dev]

# Install security dependencies
pip install -e .[security]

# Install observability dependencies
pip install -e .[observability]

# Install all optional dependencies
pip install -e .[dev,security,observability]
```

## 📱 Flutter Mobile App Installation

### Prerequisites
```bash
# Check Flutter version (3.16+ required)
flutter --version

# Check Flutter doctor
flutter doctor
```

### Install Flutter (if not already installed)

#### Windows
```powershell
# Download Flutter SDK
Invoke-WebRequest -Uri "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.x-stable.zip" -OutFile "flutter.zip"

# Extract to C:\src\flutter
Expand-Archive -Path "flutter.zip" -DestinationPath "C:\src\"

# Add to PATH
$env:PATH += ";C:\src\flutter\bin"

# Verify installation
flutter doctor
```

#### macOS
```bash
# Using Homebrew
brew install flutter

# Or download directly
curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_3.16.x-stable.zip
unzip flutter_macos_3.16.x-stable.zip
export PATH="$PATH:`pwd`/flutter/bin"

# Verify installation
flutter doctor
```

#### Linux
```bash
# Download Flutter
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.16.x-stable.tar.xz

# Extract
tar xf flutter_linux_3.16.x-stable.tar.xz

# Add to PATH
export PATH="$PATH:`pwd`/flutter/bin"

# Add to .bashrc for persistence
echo 'export PATH="$PATH:/path/to/flutter/bin"' >> ~/.bashrc

# Verify installation
flutter doctor
```

### Install Mobile App Dependencies
```bash
# Navigate to mobile app directory
cd mobile_app

# Get dependencies
flutter pub get

# Verify dependencies
flutter pub deps
```

### Build Mobile App
```bash
# For Android (debug)
flutter build apk --debug

# For Android (release)
flutter build apk --release

# For iOS (requires macOS and Xcode)
flutter build ios --release

# For web
flutter build web
```

## 🐳 Docker Installation

### Prerequisites
```bash
# Install Docker
# Windows/macOS: Download Docker Desktop
# Linux: 
sudo apt-get update
sudo apt-get install docker.io docker-compose
```

### Option 1: Docker Compose (Recommended)
```yaml
# docker-compose.yml
version: '3.8'

services:
  petty-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: petty
      POSTGRES_USER: petty
      POSTGRES_PASSWORD: petty_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Individual Docker Container
```bash
# Build image
docker build -t petty:latest .

# Run container
docker run -d \
  --name petty-api \
  -p 3000:3000 \
  -e ENVIRONMENT=development \
  petty:latest

# View logs
docker logs -f petty-api

# Stop container
docker stop petty-api
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml .
COPY setup.py .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ src/
COPY tests/ tests/

# Create non-root user
RUN useradd --create-home --shell /bin/bash petty
USER petty

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Expose port
EXPOSE 3000

# Start application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

## ☁️ AWS Cloud Installation

### Prerequisites
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Install SAM CLI
pip install aws-sam-cli

# Verify installation
sam --version
aws sts get-caller-identity
```

### Deploy to AWS
```bash
# Build SAM application
sam build

# Deploy to development environment
sam deploy --config-env dev --guided

# Deploy to staging environment
sam deploy --config-env staging

# Deploy to production environment
sam deploy --config-env prod --guided
```

### Environment-Specific Configuration
```yaml
# samconfig.toml
version = 0.1

[dev]
[dev.deploy]
[dev.deploy.parameters]
stack_name = "petty-dev"
s3_bucket = "petty-dev-deployment-bucket"
region = "us-east-1"
parameter_overrides = [
  "Environment=dev",
  "LogLevel=debug"
]

[staging]
[staging.deploy]
[staging.deploy.parameters]
stack_name = "petty-staging"
s3_bucket = "petty-staging-deployment-bucket"
region = "us-east-1"
parameter_overrides = [
  "Environment=staging",
  "LogLevel=info"
]

[prod]
[prod.deploy]
[prod.deploy.parameters]
stack_name = "petty-prod"
s3_bucket = "petty-prod-deployment-bucket"
region = "us-east-1"
parameter_overrides = [
  "Environment=prod",
  "LogLevel=warn"
]
```

## 🔧 Development Tools Installation

### Code Editor Setup

#### VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "dart-code.dart-code",
    "dart-code.flutter",
    "ms-vscode.makefile-tools",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json"
  ]
}
```

#### PyCharm/IntelliJ Setup
1. Install Python plugin
2. Install Flutter/Dart plugin
3. Configure Python interpreter to use virtual environment
4. Configure code style to use Black formatter

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Testing Tools
```bash
# Install test dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test types
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
pytest -m security    # Run only security tests
```

## 🔍 Verification & Validation

### System Health Check
```bash
# Run comprehensive validation
python tests/validate_system.py

# Check API health
curl http://localhost:3000/health

# Check mobile app connectivity
flutter run --dart-define=API_BASE_URL=http://localhost:3000
```

### Performance Benchmarks
```bash
# Run performance tests
python tests/performance/test_performance.py

# Load testing with Locust
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:3000
```

### Security Validation
```bash
# Run security tests
python -m pytest tests/security/

# Run bandit security scanner
bandit -r src/

# Run safety dependency checker
safety check
```

## 🔧 Configuration

### Environment Variables
```bash
# Required environment variables
export PETTY_ENVIRONMENT=development
export PETTY_LOG_LEVEL=info
export PETTY_API_PORT=3000

# Optional environment variables
export PETTY_DATABASE_URL=postgresql://localhost/petty
export PETTY_REDIS_URL=redis://localhost:6379/0
export PETTY_AWS_REGION=us-east-1
```

### Configuration Files
```yaml
# config/development.yaml
environment: development
log_level: debug
api:
  port: 3000
  host: 0.0.0.0
  cors_enabled: true
database:
  type: sqlite
  path: ./data/petty.db
cache:
  type: memory
  ttl: 300
```

## 🚨 Troubleshooting Installation

### Common Issues

#### Python Issues
```bash
# Issue: Python version mismatch
# Solution: Use pyenv to manage Python versions
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0

# Issue: Permission denied on pip install
# Solution: Use user install or fix permissions
pip install --user -e .
# Or fix permissions:
sudo chown -R $USER:$USER ~/.local
```

#### Flutter Issues
```bash
# Issue: Flutter doctor shows issues
# Solution: Follow specific recommendations
flutter doctor --verbose

# Issue: Android SDK not found
# Solution: Install Android Studio or set ANDROID_HOME
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

#### Docker Issues
```bash
# Issue: Docker daemon not running
# Solution: Start Docker daemon
sudo systemctl start docker

# Issue: Permission denied on Docker commands
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### AWS Issues
```bash
# Issue: AWS credentials not configured
# Solution: Configure AWS CLI
aws configure
# Or use environment variables:
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Getting Help

1. **Check logs**: Look for error messages in application logs
2. **Verify prerequisites**: Ensure all required tools are installed
3. **Check documentation**: Refer to component-specific guides
4. **Search issues**: Check [GitHub Issues](https://github.com/kakashi3lite/Petty/issues)
5. **Ask for help**: Open a new issue with detailed error information

## 📚 Next Steps

After successful installation:

1. **[Quick Start Guide](quick-start.md)** - Get up and running quickly
2. **[Development Setup](development-setup.md)** - Set up development environment
3. **[Deployment Guide](../deployment/README.md)** - Deploy to production
4. **[Configuration Reference](../reference/configuration.md)** - Detailed configuration options

---

**Installation Complete!** 🎉

You're now ready to start using Petty. Proceed to the [Quick Start Guide](quick-start.md) to begin monitoring your pet's behavior and health.

**Last Updated**: January 20, 2024 | **Version**: 0.1.0