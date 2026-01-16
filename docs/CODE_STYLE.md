# Code Style Guide

This document defines the coding standards and conventions for the publ-data-manager project.

## Table of Contents

- [General Principles](#general-principles)
- [Type Hints](#type-hints)
- [Docstrings](#docstrings)
- [Naming Conventions](#naming-conventions)
- [Code Organization](#code-organization)
- [Testing Conventions](#testing-conventions)
- [Linting and Formatting](#linting-and-formatting)

## General Principles

1. **Readability** - Code should be easy to read and understand
2. **Simplicity** - Prefer simple solutions over complex ones
3. **Consistency** - Follow established patterns in the codebase
4. **Explicit** - Be explicit rather than implicit

## Type Hints

### Required for All Functions

All functions must have type hints for parameters and return values.

```python
# Good
def process_member(email: str, data: dict[str, Any]) -> Member | None:
    ...

# Bad
def process_member(email, data):
    ...
```

### Modern Syntax (Python 3.11+)

Use modern union syntax instead of `Optional` or `Union`:

```python
# Good
def find_record(id: str) -> Record | None:
    ...

def process(items: list[str] | tuple[str, ...]) -> dict[str, int]:
    ...

# Bad (old style)
from typing import Optional, Union, List, Dict

def find_record(id: str) -> Optional[Record]:
    ...

def process(items: Union[List[str], Tuple[str, ...]]) -> Dict[str, int]:
    ...
```

### Complex Types

For complex types, use `TypeAlias` or define custom types:

```python
from typing import TypeAlias

RecordData: TypeAlias = dict[str, str | int | bool | None]

def update_record(record_id: str, data: RecordData) -> bool:
    ...
```

### Generic Collections

Use lowercase generic types:

```python
# Good
items: list[str] = []
mapping: dict[str, int] = {}
records: set[Record] = set()

# Bad
items: List[str] = []
mapping: Dict[str, int] = {}
```

## Docstrings

### Google Style

Use Google-style docstrings for all public functions and classes:

```python
def sync_member_data(
    email: str,
    fields: dict[str, Any],
    *,
    force: bool = False,
) -> SyncResult:
    """Synchronize member data to Airtable.

    Downloads the latest member data from Publ and updates
    the corresponding Airtable record.

    Args:
        email: The member's email address (primary key).
        fields: Dictionary of field names to values to update.
        force: If True, update even if data appears unchanged.

    Returns:
        SyncResult containing the operation status and any errors.

    Raises:
        AirtableError: If the Airtable API request fails.
        ValidationError: If the email format is invalid.

    Example:
        >>> result = sync_member_data(
        ...     "user@example.com",
        ...     {"Name": "John Doe", "Status": "Active"}
        ... )
        >>> print(result.success)
        True
    """
```

### Class Docstrings

```python
class MemberSync:
    """Handles synchronization of member data between Publ and Airtable.

    This class manages the download of member data from the Publ platform
    and synchronizes it with the corresponding Airtable base.

    Attributes:
        config: Configuration settings for the sync process.
        logger: Logger instance for operation logging.

    Example:
        >>> sync = MemberSync(config)
        >>> sync.run()
    """
```

### When to Write Docstrings

- **Required**: All public functions, classes, and modules
- **Optional**: Private functions (`_name`) if logic is complex
- **Skip**: Obvious getters/setters, `__init__` if trivial

## Naming Conventions

### Variables and Functions

Use `snake_case`:

```python
# Good
member_count = 0
total_records = 100

def calculate_sync_delta():
    ...

def get_active_members():
    ...

# Bad
memberCount = 0
TotalRecords = 100
```

### Classes

Use `PascalCase`:

```python
# Good
class MemberRecord:
    ...

class AirtableSyncer:
    ...

# Bad
class member_record:
    ...

class airtable_syncer:
    ...
```

### Constants

Use `SCREAMING_SNAKE_CASE`:

```python
# Good
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 30
API_BASE_URL = "https://api.airtable.com/v0"

# Bad
maxRetryCount = 3
default_timeout_seconds = 30
```

### Private Members

Use single underscore prefix:

```python
class Syncer:
    def __init__(self):
        self._cache: dict[str, Any] = {}  # Private attribute

    def _validate_input(self, data: dict) -> bool:  # Private method
        ...
```

### Module-Level Private

Use single underscore prefix:

```python
_DEFAULT_CONFIG = {...}  # Module-private constant

def _helper_function():  # Module-private function
    ...
```

## Code Organization

### Import Order

Imports should be grouped and sorted:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import logging
from datetime import datetime
from pathlib import Path

# Third-party
import yaml
from pyairtable import Api

# Local
from src.config import Config
from src.utils import parse_date
```

Ruff will automatically sort imports with `ruff check --fix`.

### Module Structure

```python
"""Module docstring describing the module's purpose."""

# Imports (grouped as above)
import ...

# Module-level constants
MAX_RECORDS = 1000

# Type aliases
RecordData = dict[str, Any]

# Classes
class MainClass:
    ...

class HelperClass:
    ...

# Functions
def main_function():
    ...

def _helper_function():
    ...

# Module entry point (if applicable)
if __name__ == "__main__":
    main_function()
```

### Line Length

Maximum line length is **100 characters** (configured in pyproject.toml).

## Testing Conventions

### Test Organization

Use class-based grouping for related tests:

```python
class TestMemberValidation:
    """Tests for member validation functions."""

    def test_valid_email_returns_true(self):
        assert validate_email("user@example.com") is True

    def test_invalid_email_returns_false(self):
        assert validate_email("invalid") is False

    def test_empty_email_returns_false(self):
        assert validate_email("") is False


class TestMemberSync:
    """Tests for member synchronization."""

    def test_sync_creates_new_record(self, mock_airtable):
        ...

    def test_sync_updates_existing_record(self, mock_airtable):
        ...
```

### Test Naming

Use descriptive names that explain what is being tested:

```python
# Good
def test_parse_date_with_valid_iso_format_returns_datetime():
    ...

def test_sync_with_network_error_raises_connection_error():
    ...

# Bad
def test_parse():
    ...

def test_1():
    ...
```

### Fixtures

Define fixtures in `conftest.py`:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_member_data() -> dict[str, Any]:
    """Provide sample member data for tests."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "status": "Active",
    }

@pytest.fixture
def mock_airtable_client(mocker):
    """Provide a mocked Airtable client."""
    return mocker.patch("src.airtable_syncer.Api")
```

## Linting and Formatting

### Tools

- **Ruff**: Linting and formatting (replaces Black, isort, Flake8)
- **Mypy**: Static type checking

### Commands

```bash
# Check for linting issues
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type check
mypy src/
```

### Pre-commit

Pre-commit hooks run automatically on `git commit`:

```bash
# Install hooks (one-time)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Configuration

Tool configuration is in `pyproject.toml`. Key settings:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

## Examples

### Complete Function Example

```python
def sync_records_to_airtable(
    records: list[RecordData],
    *,
    batch_size: int = 10,
    dry_run: bool = False,
) -> SyncSummary:
    """Synchronize records to Airtable in batches.

    Processes the given records and creates or updates them in Airtable.
    Records are processed in batches to respect API rate limits.

    Args:
        records: List of record data dictionaries to sync.
        batch_size: Number of records per batch (default: 10).
        dry_run: If True, simulate the sync without making changes.

    Returns:
        SyncSummary with counts of created, updated, and failed records.

    Raises:
        ValueError: If batch_size is less than 1.
        AirtableError: If the API request fails.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    summary = SyncSummary()

    for batch in _chunk_list(records, batch_size):
        if dry_run:
            logger.info(f"[DRY RUN] Would sync {len(batch)} records")
            summary.skipped += len(batch)
            continue

        try:
            results = _sync_batch(batch)
            summary.update(results)
        except AirtableError as e:
            logger.error(f"Batch sync failed: {e}")
            summary.failed += len(batch)

    return summary
```
