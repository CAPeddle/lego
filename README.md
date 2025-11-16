
# Lego Inventory Service

Minimal, modular FastAPI service to manage LEGO sets and part inventory.
Designed for Raspberry Pi 5. SQLite backend. Clean architecture.

## Status

⚠️ **INITIAL SCAFFOLD - REFACTORING REQUIRED**

This codebase has a good architectural foundation but requires critical refactoring before production use. See [TODO.md](TODO.md) for prioritized work items.

**Code Review Score**: 6/10
- ✅ Clean architecture and separation of concerns
- ✅ Type hints and Pydantic models
- ❌ Session management anti-pattern (critical)
- ❌ No dependency injection (critical)
- ❌ Missing error handling (critical)
- ❌ No tests (critical)


## Quick Start

### Running on Windows (PowerShell)

1. Create and activate venv:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Configure environment (optional):
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your Bricklink API credentials
   ```

4. Start the service:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8081
   ```

5. Access API docs: http://localhost:8081/docs

---

### Running on Raspberry Pi (Linux)

1. Create and activate venv:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your Bricklink API credentials
   ```

4. Start the service:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8081
   ```

5. Access API docs: http://localhost:8081/docs

## Project Structure

```
app/
├── main.py              # FastAPI app factory and lifecycle
├── api/                 # HTTP routers and request/response models
│   ├── sets_router.py   # Endpoints for managing sets
│   └── inventory_router.py  # Endpoints for inventory operations
├── core/                # Domain models, services, business logic
│   ├── models.py        # Pydantic models (LegoSet, Part, InventoryItem)
│   ├── services.py      # Business logic (InventoryService)
│   └── states.py        # Enums (PieceState)
└── infrastructure/      # External integrations (DB, APIs)
    ├── db.py            # SQLAlchemy setup and repositories
    └── bricklink_client.py  # Bricklink API client (stub)
```

## Documentation

- **[.claude/session-start.md](.claude/session-start.md)** - **START HERE** for new Claude sessions
- **[research.md](research.md)** - Research and investigation log
- **[TODO.md](TODO.md)** - Prioritized list of tasks and improvements
- **[.claude/instructions.md](.claude/instructions.md)** - Comprehensive coding guidelines and architecture decisions
- **[.claude/quick-reference.md](.claude/quick-reference.md)** - Code patterns and snippets

## For Developers

### New Claude Sessions

**START HERE**: Read **[.claude/session-start.md](.claude/session-start.md)** for:
- Environment setup instructions
- How to run tests
- Research documentation requirements

### Before Development

Read in this order:
1. **[.claude/session-start.md](.claude/session-start.md)** - Setup and workflow
2. **[TODO.md](TODO.md)** - See what needs to be done
3. **[.claude/instructions.md](.claude/instructions.md)** - Understand architecture and standards
4. **[.claude/quick-reference.md](.claude/quick-reference.md)** - Common patterns

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term

# Run specific test
pytest tests/test_infrastructure/test_bricklink_catalog.py -v
```

**Next recommended tasks**:
1. Fix session management anti-pattern
2. Implement dependency injection
3. Add error handling
4. Write tests

See [TODO.md](TODO.md) for detailed breakdown.
