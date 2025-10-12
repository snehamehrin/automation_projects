.PHONY: help install install-dev test test-unit test-integration test-e2e lint format clean dev build docker-build docker-run deploy

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

# Testing
test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	pytest tests/e2e/ -v

test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term

# Code quality
lint: ## Run linting
	flake8 src tests
	mypy src
	black --check src tests
	isort --check-only src tests

format: ## Format code
	black src tests
	isort src tests

# Development
dev: ## Start development server
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Start background worker
	celery -A src.workers.celery_app worker --loglevel=info

# Database
db-migrate: ## Run database migrations
	alembic upgrade head

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(message)"

db-reset: ## Reset database (WARNING: destructive)
	alembic downgrade base
	alembic upgrade head

# Docker
docker-build: ## Build Docker image
	docker build -t reddit-sentiment-analyzer .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env reddit-sentiment-analyzer

# Deployment
deploy-staging: ## Deploy to staging
	kubectl apply -f deployment/k8s/staging/

deploy-prod: ## Deploy to production
	kubectl apply -f deployment/k8s/production/

# Utilities
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

logs: ## Show application logs
	tail -f logs/app.log

# Setup
setup: install-dev ## Complete development setup
	cp .env.example .env
	@echo "Please edit .env with your configuration"
	@echo "Run 'make db-migrate' to setup database"
	@echo "Run 'make test' to verify installation"

# CI/CD
ci-test: ## Run tests for CI
	pytest --cov=src --cov-report=xml --junitxml=test-results.xml

ci-lint: ## Run linting for CI
	flake8 src tests
	mypy src
	black --check src tests
	isort --check-only src tests
