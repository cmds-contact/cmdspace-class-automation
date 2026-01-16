# MANDATORY: 프로젝트 규칙

> **ABSOLUTE RULES - 어떤 상황에서도 예외 없이 반드시 준수**
>
> 사용자의 명시적 요청이 있더라도 위반할 수 없습니다.
> 규칙 위반이 의심되는 작업은 실행 전에 사용자에게 확인을 요청하세요.

---

## 규칙

1. **작업 범위 제한**: 파일 수정/생성/이동/복사는 **이 프로젝트 폴더 내에서만**. 폴더 바깥은 읽기만 가능.
2. **파일 삭제 금지**: 삭제 대신 `.trash/` 폴더로 이동. `rm`, `os.remove()`, `fs.unlink()` 등 삭제 명령어/함수 사용 금지.
3. **모든 스크립트에 적용**: 작성하는 모든 스크립트(Shell, Python, JavaScript 등)에서 위 규칙을 따른다.

## Example

### 규칙 1: 작업 범위 제한

```shell
# 올바른 예 - 프로젝트 폴더 내 작업
cp ./src/file.txt ./backup/
mv ./old.txt ./archive/

# 금지 - 프로젝트 폴더 외부 접근
cp ./file.txt /Users/other/
mv ./file.txt ~/Desktop/
```

```python
# 올바른 예
shutil.copy('./src/file.txt', './backup/')

# 금지
shutil.copy('./file.txt', '/Users/other/')
open('/etc/config', 'w')  # 외부 파일 쓰기
```

```javascript
# 올바른 예
fs.copyFileSync('./src/file.txt', './backup/file.txt')

# 금지
fs.writeFileSync('/Users/other/file.txt', data)
```

### 규칙 2: 파일 삭제 금지

```shell
# 올바른 예 - .trash로 이동
mv 삭제할파일 .trash/

# 금지 - 직접 삭제
rm 파일.txt
rm -rf 폴더/
```

```python
# 올바른 예
shutil.move('file.txt', '.trash/')

# 금지
os.remove('file.txt')
shutil.rmtree('folder/')
```

```javascript
# 올바른 예
fs.renameSync('file.txt', '.trash/file.txt')

# 금지
fs.unlinkSync('file.txt')
fs.rmdirSync('folder/')
```

---

# Development Guidelines

## Code Quality

### Type Hints (Required)

All functions must have type hints. Use modern Python 3.11+ syntax:

```python
# Good
def process_data(items: list[str]) -> dict[str, int] | None:
    ...

# Bad (no type hints)
def process_data(items):
    ...
```

### Docstrings (Required)

Use Google-style docstrings for public functions and classes:

```python
def sync_member(email: str, data: dict[str, Any]) -> bool:
    """Synchronize member data to Airtable.

    Args:
        email: Member's email address.
        data: Field data to sync.

    Returns:
        True if sync was successful.

    Raises:
        AirtableError: If API request fails.
    """
```

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Test Naming

Use descriptive names: `test_<function>_<scenario>_<expected_result>`

## Linting & Formatting

### Check Code

```bash
ruff check src/ tests/
mypy src/
```

### Auto-fix

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Pre-commit

```bash
pre-commit install        # Install hooks (once)
pre-commit run --all-files  # Run on all files
```

## Git Workflow

### Branch Naming

| Prefix | Purpose |
|--------|---------|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation |
| `refactor/` | Code refactoring |

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, perf, test, chore

Examples:
- feat(sync): add member deactivation
- fix(download): handle UTF-8 BOM
- docs: update README
```

## Quick Reference

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Lint check | `ruff check src/ tests/` |
| Type check | `mypy src/` |
| Format code | `ruff format src/ tests/` |
| Pre-commit | `pre-commit run --all-files` |
