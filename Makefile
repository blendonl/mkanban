.PHONY: setup clean clean-all executable dist test lint format help

# Variables
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
APP_NAME := mkanban
MAIN_FILE := src/main.py
DIST_DIR := dist
BUILD_DIR := build

# Default target
help:
	@echo "Available targets:"
	@echo "  setup       - Create virtual environment and install dependencies"
	@echo "  executable  - Build standalone executable with PyInstaller"
	@echo "  dist        - Create distribution package"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean build artifacts"
	@echo "  clean-all   - Clean everything including virtual environment"

# Create virtual environment and install dependencies
setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install build pyinstaller

# Build standalone executable
executable: clean
	$(VENV_BIN)/pyinstaller --onefile \
		--name $(APP_NAME) \
		--add-data "src:src" \
		--hidden-import textual \
		--hidden-import click \
		--hidden-import pydantic \
		--hidden-import frontmatter \
		--hidden-import logging.handlers \
		--hidden-import aiohttp \
		--hidden-import aiohttp.connector \
		--hidden-import aiohttp.client \
		$(MAIN_FILE)
	@echo "Executable built: $(DIST_DIR)/$(APP_NAME)"

# Create distribution package
dist: clean
	$(VENV_BIN)/python -m build

# Run tests
test:
	$(VENV_BIN)/pytest

# Run linting
lint:
	$(VENV_BIN)/ruff check src/ main.py --fix

# Format code
format:
	$(VENV_BIN)/black src/

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)/ $(DIST_DIR)/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Clean everything including virtual environment
clean-all: clean
	rm -rf $(VENV)
