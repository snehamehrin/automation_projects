# Supabase MCP Server Makefile

.PHONY: help install install-dev test test-cov lint format clean run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=src/supabase_mcp --cov-report=html --cov-report=term

lint: ## Run linting
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run: ## Run the MCP server
	python server.py

setup: install-dev ## Set up development environment
	@echo "Development environment ready!"
	@echo "Copy env.example to .env and configure your Supabase credentials"

check: lint test ## Run all checks (lint + test)
