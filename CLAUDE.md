# CLAUDE.md

> **Note**: This file provides quick guidance for Claude Code CLI. For comprehensive documentation, see `.claude/instructions.md` and `.claude/quick-reference.md`.

## Project Overview

FastAPI-based LEGO inventory management service for Raspberry Pi 5. Tracks LEGO sets, parts inventory, and integrates with Bricklink API.

**Current Status**: Initial scaffold (6/10) - clean architecture but requires critical refactoring before production use.

## Session Start (New Claude Sessions)

**IMPORTANT**: When starting a new Claude session, see **[.claude/session-start.md](.claude/session-start.md)** for:
- Environment setup instructions
- How to run tests
- Research documentation requirements

**Research Documentation**: All research and investigation MUST be documented in **[research.md](research.md)**

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests (recommended first step)
pytest

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

## Architecture

Three-layer clean architecture:
- **api/** - HTTP routers and request/response handling
- **core/** - Domain models, services, business logic
- **infrastructure/** - External integrations (DB, Bricklink API)

**Key Patterns**: Repository pattern, Service layer, Dependency Injection, Pydantic models

## Critical Issues (Must Fix)

🔴 **Session Management Anti-Pattern** - Repositories manually create/close sessions → Use FastAPI DI with `get_db()` generator

🔴 **Global Repository Instances** - Module-level instances → Inject via `Depends()`

🔴 **No Error Handling** - Generic 500 errors → Create custom exception hierarchy in `app/core/exceptions.py`

🔴 **No Tests** - No test directory → Add `tests/` with pytest

🔴 **Deprecated Lifecycle Events** - Using `@app.on_event()` → Migrate to `@asynccontextmanager` lifespan

🔴 **Unpinned Dependencies** - No version constraints → Pin all dependencies

See [TODO.md](TODO.md) for complete prioritized task list (23 items).

## Coding Standards

- **Type hints everywhere** - Use Pydantic models and Python type hints
- **Async by default** - All endpoints should be `async def`
- **No global state** - Use FastAPI's `Depends()` for dependency injection
- **Clean architecture** - Keep API, domain, and infrastructure layers separate
- **Error handling** - Custom exceptions in `core/`, convert to HTTPException in API layer

## Configuration

Environment variables (prefix: `LEGO_`):
- `LEGO_DB_PATH` - SQLite database path (default: `./data/lego_inventory.db`)
- `LEGO_BRICKLINK_CONSUMER_KEY` - Bricklink OAuth consumer key
- `LEGO_BRICKLINK_CONSUMER_SECRET` - Bricklink OAuth consumer secret
- `LEGO_BRICKLINK_TOKEN` - Bricklink OAuth token
- `LEGO_BRICKLINK_TOKEN_SECRET` - Bricklink OAuth token secret
- `LEGO_LOG_LEVEL` - Logging level (default: `INFO`)

Copy `.env.example` to `.env` and fill in credentials.

## Documentation

- **[.claude/session-start.md](.claude/session-start.md)** - **START HERE** for new sessions: environment setup, test instructions, research requirements
- **[research.md](research.md)** - Research and investigation log (REQUIRED for all sessions)
- **[TODO.md](TODO.md)** - 23 prioritized tasks and improvements
- **[.claude/instructions.md](.claude/instructions.md)** - Comprehensive coding guidelines, testing standards, deployment, security
- **[.claude/quick-reference.md](.claude/quick-reference.md)** - Code patterns and snippets (DI, error handling, async, testing)
- **[README.md](README.md)** - Quick start guide and project structure

## State Management

Parts have three states (app/core/states.py:3):
- `MISSING` - Part needs to be acquired
- `OWNED_LOCKED` - Part exists but assembled in a set
- `OWNED_FREE` - Part available in inventory pool

---

**For detailed implementation guidance, code patterns, testing standards, and deployment instructions, see [.claude/instructions.md](.claude/instructions.md)**
