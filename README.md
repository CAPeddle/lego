
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

- **[TODO.md](TODO.md)** - Prioritized list of tasks and improvements
- **[.claude/instructions.md](.claude/instructions.md)** - Comprehensive coding guidelines and architecture decisions
- **[.claude/quick-reference.md](.claude/quick-reference.md)** - Code patterns and snippets

## For Developers

Before starting development, read:
1. [TODO.md](TODO.md) - See what needs to be done
2. [.claude/instructions.md](.claude/instructions.md) - Understand the architecture and standards
3. [.claude/quick-reference.md](.claude/quick-reference.md) - Common patterns

**Next recommended tasks**:
1. Fix session management anti-pattern
2. Implement dependency injection
3. Add error handling
4. Write tests

See [TODO.md](TODO.md) for detailed breakdown.
