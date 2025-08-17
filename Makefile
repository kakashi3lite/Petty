# Petty Production-Grade Makefile
.PHONY: help bootstrap test lint security deploy clean docs
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION := 3.11
VENV_PATH := .venv
FLUTTER_PATH := mobile_app
SAM_CONFIG := infrastructure/samconfig.toml
AWS_REGION := us-east-1
AWS_PROFILE := default

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Petty Production-Grade Build System$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Set up development environment
	@echo "$(BLUE)🚀 Bootstrapping Petty development environment...$(RESET)"
	@echo "$(YELLOW)Creating Python virtual environment...$(RESET)"
	python$(PYTHON_VERSION) -m venv $(VENV_PATH)
	$(VENV_PATH)/Scripts/pip install --upgrade pip setuptools wheel
	$(VENV_PATH)/Scripts/pip install -e ".[dev,security,observability]"
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	$(VENV_PATH)/Scripts/pre-commit install
	$(VENV_PATH)/Scripts/pre-commit install --hook-type commit-msg
	@echo "$(YELLOW)Setting up Flutter environment...$(RESET)"
	cd $(FLUTTER_PATH) && flutter pub get
	@echo "$(YELLOW)Installing AWS SAM CLI dependencies...$(RESET)"
	sam --version || (echo "$(RED)Please install AWS SAM CLI$(RESET)" && exit 1)
	@echo "$(YELLOW)Creating secrets baseline...$(RESET)"
	$(VENV_PATH)/Scripts/detect-secrets scan --baseline .secrets.baseline || touch .secrets.baseline
	@echo "$(GREEN)✅ Bootstrap complete!$(RESET)"

clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)🧹 Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/
	rm -rf src/**/__pycache__/ tests/**/__pycache__/
	cd $(FLUTTER_PATH) && flutter clean
	sam build --clean || true
	@echo "$(GREEN)✅ Clean complete!$(RESET)"

lint: ## Run code linting and formatting
	@echo "$(BLUE)🔍 Running linting and formatting...$(RESET)"
	@echo "$(YELLOW)Python linting...$(RESET)"
	$(VENV_PATH)/Scripts/ruff check src/ tests/ --fix
	$(VENV_PATH)/Scripts/black src/ tests/
	$(VENV_PATH)/Scripts/mypy src/ tests/
	@echo "$(YELLOW)Flutter linting...$(RESET)"
	cd $(FLUTTER_PATH) && dart format . && flutter analyze
	@echo "$(GREEN)✅ Linting complete!$(RESET)"

security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(RESET)"
	@echo "$(YELLOW)Python security scanning...$(RESET)"
	$(VENV_PATH)/Scripts/bandit -r src/ -f json -o security-report.json || true
	$(VENV_PATH)/Scripts/safety check --json --output safety-report.json || true
	@echo "$(YELLOW)Secret detection...$(RESET)"
	$(VENV_PATH)/Scripts/detect-secrets scan --baseline .secrets.baseline
	@echo "$(YELLOW)Dependency scanning...$(RESET)"
	$(VENV_PATH)/Scripts/pip-audit --format=json --output=audit-report.json || true
	@echo "$(GREEN)✅ Security checks complete!$(RESET)"

test: ## Run all tests
	@echo "$(BLUE)🧪 Running tests...$(RESET)"
	@echo "$(YELLOW)Python unit tests...$(RESET)"
	$(VENV_PATH)/Scripts/pytest tests/ -v --tb=short
	@echo "$(YELLOW)Property-based tests...$(RESET)"
	$(VENV_PATH)/Scripts/pytest tests/ -m "property" -v
	@echo "$(YELLOW)Integration tests...$(RESET)"
	$(VENV_PATH)/Scripts/pytest tests/ -m "integration" -v
	@echo "$(YELLOW)Flutter tests...$(RESET)"
	cd $(FLUTTER_PATH) && flutter test
	@echo "$(GREEN)✅ All tests passed!$(RESET)"

test-fast: ## Run fast tests only
	@echo "$(BLUE)⚡ Running fast tests...$(RESET)"
	$(VENV_PATH)/Scripts/pytest tests/ -m "not slow and not integration" -x --tb=short

build: ## Build all artifacts
	@echo "$(BLUE)🔨 Building artifacts...$(RESET)"
	@echo "$(YELLOW)Building Python packages...$(RESET)"
	$(VENV_PATH)/Scripts/python -m build
	@echo "$(YELLOW)Building SAM stack...$(RESET)"
	sam build --parallel
	@echo "$(YELLOW)Building Flutter app...$(RESET)"
	cd $(FLUTTER_PATH) && flutter build apk --debug
	@echo "$(GREEN)✅ Build complete!$(RESET)"

deploy-dev: ## Deploy to development environment
	@echo "$(BLUE)🚀 Deploying to development...$(RESET)"
	@$(MAKE) security
	@$(MAKE) test-fast
	sam deploy --config-env dev --parameter-overrides Environment=dev

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)🚀 Deploying to staging...$(RESET)"
	@$(MAKE) security
	@$(MAKE) test
	sam deploy --config-env staging --parameter-overrides Environment=staging

deploy-prod: ## Deploy to production environment
	@echo "$(BLUE)🚀 Deploying to production...$(RESET)"
	@echo "$(RED)⚠️  Production deployment requires manual approval$(RESET)"
	@read -p "Are you sure you want to deploy to production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) security && \
		$(MAKE) test && \
		sam deploy --config-env prod --parameter-overrides Environment=prod; \
	else \
		echo "$(YELLOW)Deployment cancelled$(RESET)"; \
	fi

docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(RESET)"
	$(VENV_PATH)/Scripts/python -m pdoc src/ --output-dir docs/api/
	@echo "$(GREEN)✅ Documentation generated!$(RESET)"

validate: ## Validate infrastructure and code
	@echo "$(BLUE)✅ Validating project...$(RESET)"
	@echo "$(YELLOW)Validating SAM template...$(RESET)"
	sam validate --lint
	@echo "$(YELLOW)Validating Python syntax...$(RESET)"
	$(VENV_PATH)/Scripts/python -m py_compile src/**/*.py
	@echo "$(YELLOW)Validating Flutter code...$(RESET)"
	cd $(FLUTTER_PATH) && flutter analyze --fatal-infos
	@echo "$(GREEN)✅ Validation complete!$(RESET)"

simulate: ## Run local simulation
	@echo "$(BLUE)🎭 Starting local simulation...$(RESET)"
	@echo "$(YELLOW)Starting SAM local API...$(RESET)"
	sam local start-api --port 3000 &
	@echo "$(YELLOW)Running collar simulator...$(RESET)"
	$(VENV_PATH)/Scripts/python tools/collar_simulator.py \
		--collar-id "SN-123" \
		--endpoint-url "http://localhost:3000/ingest" \
		--interval 5

# CI/CD helpers
ci-setup: ## Set up CI environment
	pip install --upgrade pip setuptools wheel
	pip install -e ".[dev,security,observability]"

ci-test: ## Run tests in CI
	pytest tests/ --junitxml=test-results.xml --cov=src --cov-report=xml

ci-security: ## Run security checks in CI
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json
	detect-secrets scan --baseline .secrets.baseline

# Development helpers
dev-setup: bootstrap ## Alias for bootstrap

watch-tests: ## Watch for changes and run tests
	$(VENV_PATH)/Scripts/pytest-watch tests/ -- -x --tb=short

format: ## Format all code
	$(VENV_PATH)/Scripts/black src/ tests/
	$(VENV_PATH)/Scripts/ruff check src/ tests/ --fix
	cd $(FLUTTER_PATH) && dart format .

check: lint security test ## Run all checks (lint, security, test)

# Environment-specific targets
env-dev: ## Set up development environment variables
	@echo "Setting up development environment..."
	@echo "export AWS_PROFILE=dev" > .env.dev
	@echo "export AWS_REGION=us-east-1" >> .env.dev
	@echo "export ENVIRONMENT=development" >> .env.dev

env-staging: ## Set up staging environment variables
	@echo "Setting up staging environment..."
	@echo "export AWS_PROFILE=staging" > .env.staging
	@echo "export AWS_REGION=us-east-1" >> .env.staging
	@echo "export ENVIRONMENT=staging" >> .env.staging

env-prod: ## Set up production environment variables
	@echo "Setting up production environment..."
	@echo "export AWS_PROFILE=prod" > .env.prod
	@echo "export AWS_REGION=us-east-1" >> .env.prod
	@echo "export ENVIRONMENT=production" >> .env.prod
