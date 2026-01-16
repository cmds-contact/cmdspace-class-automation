# Development Guide

This guide covers setting up the development environment and common development tasks.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)

## Environment Setup

### Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone and navigate to the project**

   ```bash
   git clone <repository-url>
   cd publ-data-manager
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**

   ```bash
   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

4. **Install dependencies**

   ```bash
   # Production dependencies
   pip install -r requirements.txt

   # Development dependencies
   pip install -e ".[dev]"
   ```

5. **Install Playwright browsers** (for data download)

   ```bash
   playwright install chromium
   ```

6. **Set up pre-commit hooks**

   ```bash
   pre-commit install
   ```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Airtable Configuration
AIRTABLE_API_KEY=your_api_key_here
AIRTABLE_BASE_ID=your_base_id_here

# Publ Platform Credentials
PUBL_EMAIL=your_email@example.com
PUBL_PASSWORD=your_password_here
```

## Project Structure

```
publ-data-manager/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration management
│   ├── downloader.py      # Publ data download
│   ├── airtable_syncer.py # Airtable synchronization
│   ├── data_analyzer.py   # Data analysis utilities
│   ├── logger.py          # Logging configuration
│   └── utils.py           # Helper functions
├── tests/                  # Test files
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   ├── test_*.py          # Test modules
├── docs/                   # Documentation
├── downloads/              # Downloaded CSV files (gitignored)
├── logs/                   # Application logs (gitignored)
├── .github/               # GitHub configuration
├── pyproject.toml         # Project configuration
├── requirements.txt       # Production dependencies
├── settings.yaml          # Runtime settings
└── .env                   # Environment variables (gitignored)
```

## Configuration

### settings.yaml

Runtime configuration for table mappings and sync behavior:

```yaml
tables:
  members:
    table_id: "tblXXXXXXXX"
    primary_key: "Email"
  orders:
    table_id: "tblYYYYYYYY"
    primary_key: "Order ID"
```

### pyproject.toml

Project metadata and tool configuration (ruff, mypy, pytest).

## Running the Application

### Full Sync

```bash
python -m src.main
```

### Download Only

```bash
python -m src.main --download-only
```

### Sync Only (Skip Download)

```bash
python -m src.main --sync-only
```

### Dry Run

```bash
python -m src.main --dry-run
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_utils.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run with HTML Coverage Report

```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test

```bash
pytest tests/test_utils.py::TestDateParsing::test_valid_date -v
```

## Debugging

### Enable Debug Logging

Set the log level in your code or environment:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs

Logs are stored in the `logs/` directory:

```bash
# View latest log
tail -f logs/sync_$(date +%Y%m%d).log
```

### Interactive Debugging

```bash
# Run with pdb
python -m pdb -m src.main

# Or use breakpoint() in code
```

## Common Tasks

### Linting

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

### Type Checking

```bash
mypy src/
```

### Pre-commit Checks

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files
```

### Update Dependencies

```bash
# Update pip
pip install --upgrade pip

# Update pre-commit hooks
pre-commit autoupdate
```

### Clean Build Artifacts

```bash
# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Tool caches
rm -rf .ruff_cache .mypy_cache .pytest_cache

# Coverage
rm -rf htmlcov .coverage coverage.xml
```

## IDE Configuration

### VS Code

Recommended extensions:

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  }
}
```

### PyCharm

1. Set Python interpreter to `.venv/bin/python`
2. Enable Ruff plugin
3. Configure external tools for pre-commit
