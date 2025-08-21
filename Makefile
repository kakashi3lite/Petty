# Petty Production-Grade Makefile
.PHONY: help bootstrap test lint security deploy clean docs \
py.lint py.test sam.validate flutter.analyze flutter.test \
branches-status branches-summary branches-sync-commands branches-status-json branches-fetch \
branches-bulk-sync branches-bulk-sync-auto branches-bulk-sync-dry
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION := 3.11
VENV_PATH := .venv
FLUTTER_PATH := mobile_app
SAM_CONFIG := infrastructure/samconfig.toml
AWS_REGION := us-east-1
AWS_PROFILE := default

# Cross-platform Python binary / virtualenv helpers
ifeq ($(OS),Windows_NT)
  PYTHON_BIN ?= python
  VENV_PY := $(VENV_PATH)/Scripts/python
  VENV_PIP := $(VENV_PATH)/Scripts/pip
else
  PYTHON_BIN ?= python3
  VENV_PY := $(VENV_PATH)/bin/python
  VENV_PIP := $(VENV_PATH)/bin/pip
endif
PYTEST_ENV := PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

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
	$(PYTHON_BIN) -m venv $(VENV_PATH) || (echo "$(RED)Failed to create venv$(RESET)" && exit 1)
	$(VENV_PIP) install --upgrade pip setuptools wheel
	$(VENV_PIP) install -e ".[dev,security,observability]"
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	$(VENV_PY) -m pre_commit install
	$(VENV_PY) -m pre_commit install --hook-type commit-msg
	@echo "$(YELLOW)Setting up Flutter environment...$(RESET)"
	cd $(FLUTTER_PATH) && flutter pub get
	@echo "$(YELLOW)Installing AWS SAM CLI dependencies...$(RESET)"
	sam --version || (echo "$(RED)Please install AWS SAM CLI$(RESET)" && exit 1)
	@echo "$(YELLOW)Creating secrets baseline...$(RESET)"
	$(VENV_PY) -m detect_secrets scan --baseline .secrets.baseline || touch .secrets.baseline
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
	$(VENV_PY) -m ruff check src/ tests/ --fix
	$(VENV_PY) -m black src/ tests/
	$(VENV_PY) -m mypy src/ tests/
	@echo "$(YELLOW)Flutter linting...$(RESET)"
	cd $(FLUTTER_PATH) && dart format . && flutter analyze
	@echo "$(GREEN)✅ Linting complete!$(RESET)"

# --- Granular convenience targets (Python / SAM / Flutter) ---
py.lint: ## Python lint + type check only
	@echo "$(BLUE)🔍 Python lint (ruff, black --check, mypy)...$(RESET)"
	$(VENV_PY) -m ruff check src/ tests/
	$(VENV_PY) -m black --check src/ tests/
	$(VENV_PY) -m mypy src/ tests/

py.test: ## Python tests only
	@echo "$(BLUE)🧪 Python tests (plugin autoload disabled)...$(RESET)"
	$(PYTEST_ENV) $(VENV_PY) -m pytest tests/ -v --tb=short

sam.validate: ## Validate SAM template only
	@echo "$(BLUE)🧪 Validating SAM template...$(RESET)"
	sam validate --lint

flutter.analyze: ## Run Flutter analyzer
	@echo "$(BLUE)🔎 Flutter analyze...$(RESET)"
	cd $(FLUTTER_PATH) && flutter analyze

flutter.test: ## Run Flutter tests only
	@echo "$(BLUE)🧪 Flutter tests...$(RESET)"
	cd $(FLUTTER_PATH) && flutter test

security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(RESET)"
	@echo "$(YELLOW)Python security scanning...$(RESET)"
	$(VENV_PY) -m bandit -r src/ -f json -o security-report.json || true
	$(VENV_PY) -m safety check --json --output safety-report.json || true
	@echo "$(YELLOW)Secret detection...$(RESET)"
	$(VENV_PY) -m detect_secrets scan --baseline .secrets.baseline || true
	@echo "$(YELLOW)Dependency scanning...$(RESET)"
	$(VENV_PY) -m pip_audit --format=json --output=audit-report.json || true
	@echo "$(GREEN)✅ Security checks complete!$(RESET)"

test: ## Run all tests
	@echo "$(BLUE)🧪 Running tests...$(RESET)"
	@echo "$(YELLOW)Python unit tests...$(RESET)"
	$(PYTEST_ENV) $(VENV_PY) -m pytest tests/ -v --tb=short
	@echo "$(YELLOW)Property-based tests...$(RESET)"
	$(PYTEST_ENV) $(VENV_PY) -m pytest tests/ -m "property" -v
	@echo "$(YELLOW)Integration tests...$(RESET)"
	$(PYTEST_ENV) $(VENV_PY) -m pytest tests/ -m "integration" -v
	@echo "$(YELLOW)Flutter tests...$(RESET)"
	cd $(FLUTTER_PATH) && flutter test
	@echo "$(GREEN)✅ All tests passed!$(RESET)"

test-fast: ## Run fast tests only
	@echo "$(BLUE)⚡ Running fast tests...$(RESET)"
	$(PYTEST_ENV) $(VENV_PY) -m pytest tests/ -m "not slow and not integration" -x --tb=short

build: ## Build all artifacts
	@echo "$(BLUE)🔨 Building artifacts...$(RESET)"
	@echo "$(YELLOW)Building Python packages...$(RESET)"
	$(VENV_PY) -m build
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
	$(VENV_PY) -m pdoc src/ --output-dir docs/api/
	@echo "$(GREEN)✅ Documentation generated!$(RESET)"

validate: ## Validate infrastructure and code
	@echo "$(BLUE)✅ Validating project...$(RESET)"
	@echo "$(YELLOW)Validating SAM template...$(RESET)"
	sam validate --lint
	@echo "$(YELLOW)Validating Python syntax...$(RESET)"
	$(VENV_PY) -m py_compile src/**/*.py || true
	@echo "$(YELLOW)Validating Flutter code...$(RESET)"
	cd $(FLUTTER_PATH) && flutter analyze --fatal-infos
	@echo "$(GREEN)✅ Validation complete!$(RESET)"

simulate: ## Run local simulation
	@echo "$(BLUE)🎭 Starting local simulation...$(RESET)"
	@echo "$(YELLOW)Starting SAM local API...$(RESET)"
	sam local start-api --port 3000 &
	@echo "$(YELLOW)Running collar simulator...$(RESET)"
	$(VENV_PY) tools/collar_simulator.py \
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
	$(VENV_PY) -m pytest_watch tests/ -- -x --tb=short || echo "pytest-watch not installed"

format: ## Format all code
	$(VENV_PY) -m black src/ tests/
	$(VENV_PY) -m ruff check src/ tests/ --fix
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

# Branch management targets
branches-status: ## Check branch synchronization status
	@echo "$(BLUE)📊 Checking branch synchronization status...$(RESET)"
	python tools/branch_sync_check.py

branches-summary: ## Quick branch sync summary
	@echo "$(BLUE)📋 Quick branch sync summary...$(RESET)"
	python tools/branch_sync_summary.py

branches-sync-commands: ## Generate commands to sync branches with main
	@echo "$(BLUE)🔧 Generating branch sync commands...$(RESET)"
	python tools/branch_sync_check.py --sync-commands

branches-status-json: ## Output branch status as JSON
	@echo "$(BLUE)📄 Outputting branch status as JSON...$(RESET)"
	python tools/branch_sync_check.py --json

branches-fetch: ## Fetch all remote branches
	@echo "$(BLUE)📥 Fetching all remote branches...$(RESET)"
	git remote set-branches origin '*'
	git fetch --all

branches-bulk-sync: ## Bulk sync branches behind main (interactive)
	@echo "$(BLUE)⚡ Bulk sync branches behind main...$(RESET)"
	python tools/bulk_branch_sync.py --interactive

branches-bulk-sync-auto: ## Bulk sync branches behind main (automatic)
	@echo "$(BLUE)⚡ Bulk sync branches behind main (auto)...$(RESET)"
	python tools/bulk_branch_sync.py

branches-bulk-sync-dry: ## Show what bulk sync would do (dry run)
	@echo "$(BLUE)🔍 Bulk sync dry run...$(RESET)"
	python tools/bulk_branch_sync.py --dry-run
