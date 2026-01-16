# Contributing to publ-data-manager

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)

## Prerequisites

- Python 3.11 or higher
- Git
- Access to the project's Airtable base (for integration testing)

## Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd publ-data-manager
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**

   ```bash
   pre-commit install
   ```

5. **Configure environment**

   Copy `.env.example` to `.env` and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

## Branch Naming Convention

Use the following prefixes for your branches:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/add-refund-tracking` |
| `fix/` | Bug fixes | `fix/csv-encoding-error` |
| `docs/` | Documentation only | `docs/update-api-guide` |
| `refactor/` | Code refactoring | `refactor/simplify-sync-logic` |
| `test/` | Test additions/updates | `test/add-validator-tests` |
| `chore/` | Maintenance tasks | `chore/update-dependencies` |

### Examples

```bash
git checkout -b feature/member-deactivation
git checkout -b fix/airtable-connection-timeout
git checkout -b docs/add-troubleshooting-guide
```

## Commit Message Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Scope (Optional)

Use the module name or area affected:

- `sync` - Airtable synchronization
- `download` - Data download functionality
- `config` - Configuration handling
- `tests` - Test infrastructure

### Examples

```bash
# Feature
git commit -m "feat(sync): add automatic refund-order linking"

# Bug fix
git commit -m "fix(download): handle UTF-8 BOM in CSV files"

# Documentation
git commit -m "docs: update installation instructions"

# Refactoring
git commit -m "refactor(sync): simplify member deactivation logic"

# Breaking change
git commit -m "feat(config)!: change settings.yaml structure

BREAKING CHANGE: settings.yaml now uses 'tables' instead of 'table_ids'"
```

## Pull Request Process

1. **Create a feature branch** from `main`

   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature
   ```

2. **Make your changes** following the code style guidelines

3. **Run quality checks** before committing

   ```bash
   # Run linting
   ruff check src/ tests/

   # Run type checking
   mypy src/

   # Run tests
   pytest tests/ -v
   ```

4. **Commit your changes** using conventional commits

5. **Push your branch** and create a pull request

   ```bash
   git push -u origin feature/your-feature
   ```

6. **Fill out the PR template** completely

7. **Address review feedback** promptly

### PR Requirements

- All CI checks must pass
- At least one approving review
- Branch must be up-to-date with `main`
- No merge conflicts

## Code Review Guidelines

### For Authors

- Keep PRs focused and reasonably sized
- Provide context in the PR description
- Respond to feedback constructively
- Update documentation if needed

### For Reviewers

- Be constructive and specific in feedback
- Distinguish between required changes and suggestions
- Approve when satisfied, don't block on minor issues
- Test locally if changes are significant

## Questions?

If you have questions about contributing, please open an issue with the `question` label.
