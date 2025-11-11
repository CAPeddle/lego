# Claude Code Instructions for Lego Inventory Service

## Project Overview

This is a FastAPI-based Lego inventory management service designed to run on Raspberry Pi 5. The service helps track Lego sets, parts inventory, and integrates with the Bricklink API to fetch set metadata and parts lists.

**Primary Use Cases:**
- Track owned Lego sets (assembled or disassembled)
- Manage parts inventory with state tracking (MISSING, OWNED_LOCKED, OWNED_FREE)
- Request missing pieces from Bricklink or other services
- Provide inventory reports for building new sets

## Architecture & Design Principles

### Current Structure
```
app/
├── main.py              # FastAPI app factory and lifecycle
├── api/                 # HTTP routers and request/response models
├── core/                # Domain models, services, business logic
└── infrastructure/      # External integrations (DB, Bricklink API)
```

### Architecture Patterns
- **Clean Architecture**: Maintain separation between API, business logic, and infrastructure
- **Dependency Injection**: Use FastAPI's `Depends()` for all dependencies (NOT global instances)
- **Repository Pattern**: Database access through repository interfaces
- **Service Layer**: Business logic lives in services, not routers

### Key Principles
1. **No global state in routers** - Use dependency injection
2. **Session management via FastAPI dependencies** - Never create sessions manually
3. **Type everything** - Use Pydantic models and type hints throughout
4. **Async by default** - All endpoints and I/O operations should be async
5. **Error handling** - Custom exceptions for domain errors, proper HTTP status codes

## Critical Issues to Address (Prioritized)

### 🔴 CRITICAL (Must Fix Before Production)

1. **Session Management Anti-Pattern** (app/infrastructure/db.py)
   - Current: Manually creating/closing sessions in each repository method
   - Required: Use FastAPI dependency injection with `get_db()` generator
   - Example:
     ```python
     def get_db():
         db = SessionLocal()
         try:
             yield db
         finally:
             db.close()
     ```

2. **Global Repository Instances** (app/api/*.py)
   - Current: Module-level repository instances
   - Required: Inject repositories via `Depends()`
   - Makes code testable and follows DI principles

3. **No Error Handling**
   - Current: Bare except with generic 500 errors
   - Required: Custom exception hierarchy, specific error codes
   - Create `app/core/exceptions.py` with domain exceptions

4. **No Tests**
   - Current: No test directory or files
   - Required: `tests/` directory with pytest
   - Minimum: Service layer tests with mocked repositories

5. **Deprecated Lifespan Events** (app/main.py)
   - Current: `@app.on_event("startup")`
   - Required: Use `@asynccontextmanager` lifespan pattern

6. **Unpinned Dependencies** (requirements.txt)
   - Current: No version constraints
   - Required: Pin all dependencies with `==` or `~=`

### 🟡 HIGH PRIORITY (Fix Soon)

7. **Blocking I/O in Async Endpoints**
   - Current: Synchronous SQLAlchemy with async FastAPI
   - Options:
     - Use `sqlalchemy[asyncio]` with `aiosqlite`
     - Use `run_in_executor` for sync operations
     - Accept limitation for SQLite on Raspberry Pi

8. **Stub Bricklink API Client**
   - Current: Fake data returned
   - Required: OAuth 1.0 implementation, real API calls
   - Add rate limiting and retry logic

9. **No Logging**
   - Required: Structured logging with appropriate levels
   - Use Python's `logging` module, not print statements

10. **No Database Migrations**
    - Current: `metadata.create_all()`
    - Required: Alembic for schema versioning

### 🟢 MEDIUM PRIORITY

11. Add input validation (set_no format, constraints)
12. Add docstrings to all public functions
13. Convert to ORM models instead of Table definitions
14. Add health check endpoint (`/health`)
15. Use `pydantic-settings` for configuration management

### ⚪ LOW PRIORITY

16. Add pyproject.toml for modern Python packaging
17. Add pre-commit hooks (ruff, mypy, black)
18. Add CI/CD pipeline (GitHub Actions)
19. Add CLI interface for local management
20. Add Docker support

## Coding Standards

### Python Style
- Use **ruff** for linting and formatting
- Use **mypy** in strict mode for type checking
- Follow PEP 8 with 100-character line length
- Use type hints everywhere

### Pydantic Models
- All API request/response models use Pydantic
- Enable `from_attributes = True` (formerly `orm_mode`) when needed
- Use validators for complex validation logic

### Error Handling
```python
# Custom exceptions (app/core/exceptions.py)
class LegoServiceError(Exception):
    """Base exception for all domain errors"""

class SetNotFoundError(LegoServiceError):
    """Raised when a set doesn't exist"""

class BricklinkAPIError(LegoServiceError):
    """Raised when Bricklink API fails"""

# In routers, convert to HTTP exceptions
@router.post("/")
async def add_set(req: CreateSetRequest, service: InventoryService = Depends(get_service)):
    try:
        result = await service.add_set(req.set_no, req.assembled)
        return result
    except SetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BricklinkAPIError as e:
        raise HTTPException(status_code=502, detail=f"Bricklink API error: {e}")
```

### Database Patterns
```python
# Correct: Dependency injection
@router.get("/")
async def list_sets(db: Session = Depends(get_db)):
    repo = SqliteSetsRepository(db)
    return repo.list_all()

# Wrong: Global instances
repo = SqliteSetsRepository()  # DON'T DO THIS

@router.get("/")
async def list_sets():
    return repo.list_all()
```

### Async Guidelines
- All route handlers should be `async def`
- All database operations should be async (when using async SQLAlchemy)
- Use `asyncio.gather()` for parallel operations
- Don't mix sync and async unnecessarily

## Environment Configuration

### Required Environment Variables
- `LEGO_DB_PATH`: Path to SQLite database (default: `./data/lego_inventory.db`)
- `BRICKLINK_CONSUMER_KEY`: OAuth consumer key
- `BRICKLINK_CONSUMER_SECRET`: OAuth consumer secret
- `BRICKLINK_TOKEN`: OAuth token
- `BRICKLINK_TOKEN_SECRET`: OAuth token secret
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Configuration Management
Create `app/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_path: str = "./data/lego_inventory.db"
    bricklink_consumer_key: str
    bricklink_consumer_secret: str
    bricklink_token: str
    bricklink_token_secret: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "LEGO_"

settings = Settings()
```

## Testing Standards

### Directory Structure
```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_api/            # API integration tests
├── test_core/           # Service and model unit tests
└── test_infrastructure/ # Repository and client tests
```

### Testing Patterns
```python
# conftest.py - Shared fixtures
import pytest
from sqlalchemy import create_engine
from app.infrastructure.db import Base, SessionLocal

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session
    session.close()

@pytest.fixture
def mock_bricklink_client():
    # Return mock client
    pass

# test_core/test_services.py
def test_add_set(db_session, mock_bricklink_client):
    repo = SqliteSetsRepository(db_session)
    service = InventoryService(repo, mock_bricklink_client)
    result = await service.add_set("75192", assembled=False)
    assert result.set_no == "75192"
```

### Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for service layer
- Use `pytest-cov` for coverage reports

## Bricklink API Integration

### Authentication
- OAuth 1.0a required
- Use `requests-oauthlib` or `httpx-oauth`
- Store credentials in environment variables

### Rate Limiting
- Bricklink limits: Unknown, implement conservative backoff
- Use `tenacity` for retry logic with exponential backoff

### API Endpoints to Implement
1. `GET /items/{type}/{no}` - Get item metadata
2. `GET /items/{type}/{no}/subsets` - Get set inventory
3. Handle pagination for large inventories

## Git Workflow

### Commit Messages
Follow conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `refactor:` Code refactoring
- `test:` Adding tests
- `docs:` Documentation changes
- `chore:` Maintenance tasks

### Branch Naming
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Claude sessions: `claude/description-sessionid`

## Performance Considerations

### Raspberry Pi 5 Constraints
- Limited RAM - keep database queries efficient
- SQLite is appropriate for single-user deployment
- Consider read replicas if multiple users access concurrently
- Monitor disk I/O for SD card wear

### Optimization Strategies
- Use database indexes on frequently queried columns
- Cache Bricklink API responses (consider Redis or in-memory cache)
- Lazy load relationships in ORM
- Use connection pooling appropriately

## Security Checklist

- [ ] Never commit API keys or secrets
- [ ] Use environment variables for sensitive data
- [ ] Validate all user inputs
- [ ] Use parameterized queries (SQLAlchemy handles this)
- [ ] Implement rate limiting on API endpoints
- [ ] Add authentication if exposed to internet
- [ ] Use HTTPS in production
- [ ] Set appropriate CORS policies

## Deployment

### Production Checklist
- [ ] Pin all dependency versions
- [ ] Set up proper logging
- [ ] Configure database backups
- [ ] Use systemd service or supervisor
- [ ] Set up monitoring/alerting
- [ ] Document deployment process
- [ ] Test recovery procedures

### Systemd Service Example
```ini
[Unit]
Description=Lego Inventory Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lego
Environment="PATH=/home/pi/lego/venv/bin"
ExecStart=/home/pi/lego/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081
Restart=always

[Install]
WantedBy=multi-user.target
```

## References

- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 Docs: https://docs.sqlalchemy.org/
- Bricklink API: https://www.bricklink.com/v3/api.page
- Pydantic: https://docs.pydantic.dev/

## Review History

- **2025-11-11**: Initial code review completed
  - Identified critical session management anti-pattern
  - Highlighted need for dependency injection
  - Documented missing error handling and tests
  - Overall assessment: 6/10 - Good foundation, needs refactoring

---

**Last Updated**: 2025-11-11
**Reviewed By**: Claude Code Review Session
