# CogniFlow Development Makefile

.PHONY: help install install-dev test lint format clean build run docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run test suite"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run mypy type checking"
	@echo "  clean        - Clean build artifacts and cache"
	@echo "  build        - Build distribution packages"
	@echo "  run          - Run the application"
	@echo "  docs         - Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev: install
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=assistente_dsa --cov-report=html

# Code Quality
lint:
	flake8 assistente_dsa/
	@echo "Linting completed"

format:
	black assistente_dsa/
	@echo "Code formatted"

type-check:
	mypy assistente_dsa/
	@echo "Type checking completed"

# Maintenance
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/ .coverage htmlcov/

# Build
build: clean
	python -m build

# Run
run:
	python assistente_dsa/main_00_launcher.py

# Documentation
docs:
	@echo "Documentation generation not yet implemented"
	@echo "Consider using Sphinx for comprehensive documentation"

# Development setup
setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete"

# CI simulation
ci: lint type-check test
	@echo "CI checks passed"

# Quick development cycle
dev: format lint test
	@echo "Development cycle completed"