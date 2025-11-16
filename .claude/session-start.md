# Session Start Instructions

> **Auto-loaded**: This file is automatically loaded at the start of each Claude session to provide context and setup instructions.

## 🚀 Quick Session Checklist

When starting a new session, follow these steps:

1. **Verify environment is activated** - Check if virtual environment is active
2. **Run tests first** - Verify current state before making changes
3. **Document research** - All research and investigation must be documented in `research.md`

---

## 📦 Environment Setup

### Creating a New Environment

If the virtual environment doesn't exist, create it:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Activating Existing Environment

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### Verifying Installation

```bash
# Check installed packages
pip list

# Verify pytest is available
pytest --version

# Verify FastAPI is installed
python -c "import fastapi; print(fastapi.__version__)"
```

---

## 🧪 Running Tests

### Standard Test Commands

```bash
# Run all tests (recommended first step)
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app --cov-report=term --cov-report=html

# Run specific test file
pytest tests/test_infrastructure/test_bricklink_catalog.py

# Run specific test function
pytest tests/test_infrastructure/test_bricklink_catalog.py::test_function_name

# Run tests matching a pattern
pytest -k "test_oauth"
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_infrastructure/     # Infrastructure layer tests
│   ├── test_bricklink_catalog.py
│   └── test_oauth_client.py
└── __init__.py
```

### Coverage Reports

After running with coverage, view the HTML report:
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View in browser (if available)
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

---

## 📝 Documentation Requirements

### Research Documentation (REQUIRED)

**CRITICAL**: All research, investigation, and analysis MUST be documented in `research.md`

Create or append to `research.md` when:
- Exploring codebase to understand architecture
- Investigating bugs or issues
- Researching external APIs (Bricklink, etc.)
- Analyzing performance or optimization opportunities
- Reviewing error messages or stack traces
- Understanding existing code patterns

### Research Documentation Format

```markdown
## [Date] - [Topic/Issue]

**Session ID**: [session-id]
**Investigator**: Claude
**Status**: [In Progress | Completed | Blocked]

### Objective
What are you trying to understand or solve?

### Investigation Steps
1. First step taken
2. Second step taken
3. ...

### Findings
- Key finding 1
- Key finding 2
- ...

### Code References
- `file_path:line_number` - Description
- `app/core/services.py:45` - Service initialization pattern

### Conclusions
Summary of what was learned

### Next Steps
- [ ] Action item 1
- [ ] Action item 2

---
```

### Example Research Entry

```markdown
## 2025-11-16 - Understanding Session Management Pattern

**Session ID**: 01RddWraz1WdjfHExvr4Pind
**Investigator**: Claude
**Status**: Completed

### Objective
Investigate how database sessions are currently managed and identify anti-patterns.

### Investigation Steps
1. Read `app/infrastructure/db.py`
2. Examined repository implementations
3. Checked router dependency injection

### Findings
- Repositories manually create SessionLocal() instances
- No use of FastAPI dependency injection for sessions
- Each method creates/destroys connections (inefficient)
- Potential resource leaks if exceptions occur

### Code References
- `app/infrastructure/db.py:52-119` - Manual session management in repositories
- `app/api/sets_router.py:14-17` - Global repository instances

### Conclusions
Current pattern violates FastAPI best practices. Need to refactor to use `get_db()` dependency with proper injection.

### Next Steps
- [ ] Create `get_db()` dependency function
- [ ] Refactor repositories to accept Session in __init__
- [ ] Update all routers to inject db dependency

---
```

---

## 🏗️ Project Architecture Reference

### Layer Structure
- **app/api/** - HTTP routers, request/response handling
- **app/core/** - Business logic, services, domain models
- **app/infrastructure/** - Database, external APIs, repositories

### Key Files
- **CLAUDE.md** - Project overview and quick reference
- **.claude/instructions.md** - Comprehensive development guidelines
- **.claude/quick-reference.md** - Code patterns and snippets
- **TODO.md** - Prioritized task list (23 items)
- **pytest.ini** - Test configuration

---

## 🔧 Development Workflow

### Before Making Changes

1. **Activate environment**: `source venv/bin/activate`
2. **Run tests**: `pytest` (ensure all passing)
3. **Check git status**: `git status`
4. **Review TODO.md**: Understand current priorities

### During Development

1. **Document research**: Update `research.md` with findings
2. **Write tests first**: Follow TDD when possible
3. **Run tests frequently**: `pytest -v`
4. **Check code style**: Use type hints, follow clean architecture

### After Making Changes

1. **Run full test suite**: `pytest --cov=app`
2. **Verify no regressions**: All tests should pass
3. **Update documentation**: If behavior changed
4. **Document findings**: Update `research.md` with conclusions

---

## 🎯 Current Project Status

**Overall Assessment**: 6/10 - Good foundation, needs refactoring

### Critical Issues to Be Aware Of

1. **Session Management Anti-Pattern** - Repositories manually create/close sessions
2. **Global Repository Instances** - Module-level instances instead of DI
3. **No Error Handling** - Generic 500 errors only
4. **Deprecated Lifecycle Events** - Using `@app.on_event()` instead of lifespan

See **TODO.md** for complete prioritized list.

---

## 🔍 Debugging Tips

### Common Issues

**Import Errors**
```bash
# Verify environment is activated
which python

# Reinstall dependencies
pip install -r requirements.txt
```

**Test Failures**
```bash
# Run with full traceback
pytest -v --tb=long

# Run specific failing test
pytest tests/path/to/test.py::test_name -v
```

**Database Issues**
```bash
# Check database path
echo $LEGO_DB_PATH

# Verify database file exists
ls -lh data/lego_inventory.db
```

---

## 📚 Quick Reference Links

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pytest Docs**: https://docs.pytest.org/
- **Bricklink API**: https://www.bricklink.com/v3/api.page

---

## ⚠️ Important Reminders

1. **Always activate venv before running commands**
2. **Run tests before and after making changes**
3. **Document all research in research.md** (required!)
4. **Follow clean architecture principles** (see .claude/instructions.md)
5. **Use dependency injection** (no global instances)
6. **Handle errors explicitly** (no generic exceptions)
7. **Write tests for new code** (aim for 80% coverage)

---

**Last Updated**: 2025-11-16
**Session ID Format**: claude/description-[session-id]
