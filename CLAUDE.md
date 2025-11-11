# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI-based LEGO inventory management service for Raspberry Pi 5. Tracks LEGO sets, parts inventory, and integrates with Bricklink API to fetch set metadata and inventories. Uses SQLite for storage.

**Current Status**: Initial scaffold (6/10) - clean architecture but requires critical refactoring before production use.

## Development Commands

### Running the Service
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8081

# With auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

### Testing
Currently no tests exist. When implementing tests:
```bash
# Run tests (future)
pytest

# Run with coverage (future)
pytest --cov=app --cov-report=html
```

### Database
Database is created automatically at `./data/lego_inventory.db` on first startup. No migrations currently implemented.

## Architecture

### Three-Layer Clean Architecture

```
app/
├── api/                 # HTTP layer - request/response handling
│   ├── sets_router.py   # POST /sets/ - Add new LEGO set
│   └── inventory_router.py  # GET/PATCH /inventory/ - Query/update parts
├── core/                # Domain layer - business logic
│   ├── models.py        # Pydantic models (LegoSet, Part, InventoryItem)
│   ├── services.py      # InventoryService - orchestrates set addition
│   └── states.py        # PieceState enum (MISSING, OWNED_LOCKED, OWNED_FREE)
└── infrastructure/      # External dependencies
    ├── db.py            # SQLAlchemy tables + repositories
    └── bricklink_client.py  # Bricklink API client (stub)
```

### Key Design Patterns

- **Repository Pattern**: Database access via `SqliteSetsRepository` and `SqliteInventoryRepository`
- **Service Layer**: `InventoryService` contains business logic for adding sets and parts
- **Pydantic Models**: All domain objects and API requests/responses use Pydantic

### State Management

Parts have three states (app/core/states.py:3):
- `MISSING`: Part needs to be acquired
- `OWNED_LOCKED`: Part exists but assembled in a set
- `OWNED_FREE`: Part available in inventory pool

When a set is added as assembled, parts default to `OWNED_LOCKED`. Disassembled sets use `OWNED_FREE`.

## Critical Issues (Must Fix Before Production)

### 1. Session Management Anti-Pattern
**Location**: app/infrastructure/db.py:52-119

Repositories manually create/close sessions in each method. This causes resource leaks and makes testing impossible.

**Must implement**:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Then inject session into repository constructors and use `Depends(get_db)` in routers.

### 2. Global Repository Instances
**Location**: app/api/sets_router.py:14-17, app/api/inventory_router.py:8

Module-level instances prevent dependency injection and testing.

**Must change**: Use `Depends()` to inject repositories into each endpoint.

### 3. No Error Handling
**Location**: All routers and services

Only generic `Exception` catches with 500 errors. Need custom exception hierarchy:
- `SetNotFoundError` → 404
- `BricklinkAPIError` → 502
- `InvalidSetNumberError` → 400

Create `app/core/exceptions.py` with domain exceptions.

### 4. No Tests
No test directory exists. Minimum requirement: service layer tests with mocked repositories (80% coverage target).

### 5. Deprecated Lifecycle Events
**Location**: app/main.py:11-13

`@app.on_event("startup")` is deprecated. Must migrate to `@asynccontextmanager` lifespan pattern.

### 6. Unpinned Dependencies
**Location**: requirements.txt

All dependencies unpinned. Pin versions with `==` or `~=` for reproducible builds.

## Important Implementation Details

### Async/Sync Mismatch
**Issue**: FastAPI endpoints are async, but SQLAlchemy operations are synchronous (app/infrastructure/db.py).

**Options for fixing**:
1. Use `sqlalchemy[asyncio]` with `aiosqlite` (recommended for proper async)
2. Use `asyncio.to_thread()` for sync operations
3. Accept sync limitation for single-user Raspberry Pi deployment

Current implementation may work for single-user but violates async best practices.

### Bricklink API Client
**Location**: app/infrastructure/bricklink_client.py

Currently returns stub data. When implementing:
- OAuth 1.0a authentication required
- Rate limiting and retry logic needed
- Cache responses to reduce API calls
- Handle pagination for large set inventories

### Service Layer Pattern
**Location**: app/core/services.py:5-26

`InventoryService.add_set()` orchestrates:
1. Fetch set metadata from Bricklink
2. Fetch part inventory from Bricklink
3. Store set in sets table
4. Add each part to inventory with appropriate state

This is the correct layer for business logic - keep routers thin.

## Configuration

Environment variables (prefix: `LEGO_`):
- `LEGO_DB_PATH`: SQLite database path (default: `./data/lego_inventory.db`)
- `LEGO_BRICKLINK_CONSUMER_KEY`: Bricklink OAuth consumer key
- `LEGO_BRICKLINK_CONSUMER_SECRET`: Bricklink OAuth consumer secret
- `LEGO_BRICKLINK_TOKEN`: Bricklink OAuth token
- `LEGO_BRICKLINK_TOKEN_SECRET`: Bricklink OAuth token secret
- `LEGO_LOG_LEVEL`: Logging level (default: `INFO`)

Copy `.env.example` to `.env` and fill in credentials.

## Coding Standards

- **Type hints everywhere**: Use Pydantic models and Python type hints
- **Async by default**: All endpoints should be `async def`
- **No global state**: Use FastAPI's `Depends()` for dependency injection
- **Clean architecture**: Keep API, domain, and infrastructure layers separate
- **Pydantic models**: All request/response objects and domain models
- **Error handling**: Custom exceptions in `core/`, convert to HTTPException in API layer

When adding features, maintain the three-layer architecture and avoid coupling layers.

## Key Reference Files

- **TODO.md**: Comprehensive prioritized task list with 23 items
- **.claude/instructions.md**: Detailed coding standards and architecture patterns
- **.claude/quick-reference.md**: Code snippets and patterns
- **README.md**: Quick start guide and project structure

See TODO.md for detailed breakdown of work needed before production deployment.
