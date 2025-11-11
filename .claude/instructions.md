# Claude Code Instructions for Lego Inventory Service

> **Quick Start**: See [CLAUDE.md](../CLAUDE.md) for project overview, quick start commands, and critical issues summary.

This file provides comprehensive development guidelines, testing standards, deployment procedures, and security considerations for Claude Code when working in this repository.

## Architecture & Design Principles

### Clean Architecture Philosophy

This project follows a strict three-layer architecture to maintain separation of concerns:

**API Layer** (`app/api/`)
- HTTP request/response handling only
- No business logic
- Convert domain exceptions to HTTP exceptions
- Thin controllers that delegate to services

**Domain Layer** (`app/core/`)
- Business logic and rules
- Domain models (Pydantic)
- Service orchestration
- Custom exceptions
- No knowledge of HTTP or databases

**Infrastructure Layer** (`app/infrastructure/`)
- Database access (repositories)
- External API clients (Bricklink)
- No business logic
- Implements interfaces defined by domain

### Key Architectural Principles

1. **Dependency Injection Over Global State**
   - Use FastAPI's `Depends()` for all dependencies
   - No module-level service/repository instances
   - Makes code testable and maintainable

2. **Repository Pattern for Data Access**
   - All database operations through repository interfaces
   - Repositories injected via dependencies
   - Session management handled by framework

3. **Service Layer for Business Logic**
   - Services orchestrate complex operations
   - Services use repositories and external clients
   - Keep routers thin - delegate to services

4. **Explicit Error Handling**
   - Custom exception hierarchy for domain errors
   - Convert to appropriate HTTP status codes at API boundary
   - Never let generic exceptions leak to users

## Detailed Critical Issues Breakdown

### 🔴 CRITICAL #1: Session Management Anti-Pattern

**Current Problem** (app/infrastructure/db.py:52-119):
```python
# ❌ WRONG - Manual session management
class SqliteSetsRepository:
    def add(self, lego_set: LegoSet):
        db = SessionLocal()  # Creates new session
        try:
            # ... operations
            db.commit()
        finally:
            db.close()  # Manual cleanup
```

**Why This Is Critical**:
- Resource leaks if exceptions occur before `finally`
- Makes testing impossible (can't inject test database)
- Violates FastAPI best practices
- Each method creates/destroys connections (inefficient)

**Required Solution**:
```python
# ✅ CORRECT - Dependency injection
def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SqliteSetsRepository:
    def __init__(self, db: Session):
        self.db = db  # Injected session

    def add(self, lego_set: LegoSet):
        # Use self.db - no manual session management
        self.db.add(lego_set)
        self.db.commit()

# In router
@router.post("/")
async def add_set(req: Request, db: Session = Depends(get_db)):
    repo = SqliteSetsRepository(db)
    # ... use repo
```

**Implementation Steps**:
1. Add `get_db()` dependency in `app/infrastructure/db.py`
2. Refactor all repositories to accept `Session` in `__init__`
3. Remove all `SessionLocal()` calls from repository methods
4. Update routers to inject `db: Session = Depends(get_db)`
5. Add tests to verify session handling

### 🔴 CRITICAL #2: Global Repository Instances

**Current Problem** (app/api/sets_router.py:14-17):
```python
# ❌ WRONG
sets_repo = SqliteSetsRepository()  # Module-level
inventory_repo = SqliteInventoryRepository()

@router.post("/")
async def add_set(req: Request):
    # Uses global repo - can't test, can't inject dependencies
    return sets_repo.add(req.set)
```

**Required Solution**:
```python
# ✅ CORRECT
def get_sets_repository(db: Session = Depends(get_db)):
    return SqliteSetsRepository(db)

def get_inventory_service(
    db: Session = Depends(get_db),
    bricklink: BricklinkClient = Depends(get_bricklink_client)
):
    sets_repo = SqliteSetsRepository(db)
    inv_repo = SqliteInventoryRepository(db)
    return InventoryService(inv_repo, sets_repo, bricklink)

@router.post("/")
async def add_set(
    req: Request,
    service: InventoryService = Depends(get_inventory_service)
):
    return await service.add_set(req.set_no, req.assembled)
```

### 🔴 CRITICAL #3: Error Handling

**Current Problem**: Generic exception handling with 500 errors only

**Required Implementation**:

Create `app/core/exceptions.py`:
```python
class LegoServiceError(Exception):
    """Base exception for all domain errors."""
    pass

class SetNotFoundError(LegoServiceError):
    """Raised when set doesn't exist in Bricklink."""
    pass

class BricklinkAPIError(LegoServiceError):
    """Raised when Bricklink API request fails."""
    pass

class InvalidSetNumberError(LegoServiceError):
    """Raised when set number format is invalid."""
    pass

class DatabaseError(LegoServiceError):
    """Raised when database operation fails."""
    pass
```

Router error handling pattern:
```python
from app.core.exceptions import SetNotFoundError, BricklinkAPIError

@router.post("/")
async def add_set(req: CreateSetRequest, service = Depends(get_service)):
    try:
        result = await service.add_set(req.set_no)
        return {"ok": True, "set": result}
    except SetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BricklinkAPIError as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")
    except InvalidSetNumberError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error adding set")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 🔴 CRITICAL #4: No Tests

**Minimum Viable Testing**:

Create `tests/` structure:
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_api/
│   └── test_sets_router.py
└── test_core/
    ├── test_services.py
    └── test_models.py
```

**conftest.py** with essential fixtures:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.db import Base

@pytest.fixture
def db_session():
    """Provide in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def mock_bricklink_client():
    """Mock Bricklink API client."""
    class MockClient:
        async def fetch_set_metadata(self, set_no):
            return {
                "set_no": set_no,
                "name": f"Test Set {set_no}",
                "year": 2024
            }

        async def fetch_set_inventory(self, set_no):
            return [
                {"part_no": "3001", "color_id": 1, "qty": 4},
                {"part_no": "3002", "color_id": 2, "qty": 2}
            ]
    return MockClient()
```

**Target Coverage**: 80% overall, 100% for service layer

### 🔴 CRITICAL #5: Deprecated Lifecycle Events

**Current Problem** (app/main.py:11-13):
```python
# ❌ DEPRECATED
@app.on_event("startup")
def startup():
    init_db()
```

**Required Solution**:
```python
# ✅ CORRECT
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database")
    init_db()
    logger.info("Application ready")

    yield  # Application runs

    # Shutdown
    logger.info("Shutting down")
    # Cleanup code here

app = FastAPI(lifespan=lifespan)
```

### 🔴 CRITICAL #6: Unpinned Dependencies

**Current Problem**: `requirements.txt` has no version constraints

**Required Action**:
```bash
# Generate pinned requirements
pip freeze > requirements.txt
```

Or use version ranges:
```
fastapi~=0.109.0
uvicorn[standard]~=0.27.0
sqlalchemy~=2.0.25
pydantic~=2.5.0
```

## Testing Standards

### Testing Philosophy

- **Test behavior, not implementation** - Tests should verify outcomes, not internal details
- **Unit tests for services** - Mock repositories and external dependencies
- **Integration tests for repositories** - Use real in-memory database
- **API tests for endpoints** - Use TestClient with mocked services

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_api/                # API integration tests
│   ├── test_sets_router.py
│   └── test_inventory_router.py
├── test_core/               # Unit tests
│   ├── test_services.py
│   ├── test_models.py
│   └── test_validators.py
└── test_infrastructure/     # Integration tests
    ├── test_repositories.py
    └── test_bricklink_client.py
```

### Testing Patterns

**Service Layer Test** (most important):
```python
import pytest
from app.core.services import InventoryService
from app.core.exceptions import SetNotFoundError

@pytest.mark.asyncio
async def test_add_set_success(db_session, mock_bricklink_client):
    # Arrange
    sets_repo = SqliteSetsRepository(db_session)
    inv_repo = SqliteInventoryRepository(db_session)
    service = InventoryService(inv_repo, sets_repo, mock_bricklink_client)

    # Act
    result = await service.add_set("75192", assembled=False)

    # Assert
    assert result.set_no == "75192"
    assert result.name == "Test Set 75192"
    assert result.assembled is False

    # Verify parts were added to inventory
    parts = await inv_repo.list_by_set("75192")
    assert len(parts) == 2  # Mock returns 2 parts

@pytest.mark.asyncio
async def test_add_set_not_found(db_session, mock_bricklink_client):
    # Configure mock to return None
    mock_bricklink_client.fetch_set_metadata = lambda x: None

    service = InventoryService(..., mock_bricklink_client)

    with pytest.raises(SetNotFoundError):
        await service.add_set("99999")
```

**Repository Test**:
```python
def test_add_set_to_database(db_session):
    repo = SqliteSetsRepository(db_session)

    lego_set = LegoSet(
        set_no="75192",
        name="Millennium Falcon",
        year=2017,
        assembled=True
    )

    result = repo.add(lego_set)

    assert result.set_no == "75192"
    assert repo.get("75192") is not None
```

**API Test**:
```python
from fastapi.testclient import TestClient
from app.main import app

def test_add_set_endpoint_success(client: TestClient, monkeypatch):
    # Mock the service dependency
    def mock_service():
        mock = MagicMock()
        mock.add_set.return_value = LegoSet(set_no="75192", name="Test")
        return mock

    monkeypatch.setattr("app.api.sets_router.get_inventory_service", mock_service)

    response = client.post("/sets/", json={
        "set_no": "75192",
        "assembled": False
    })

    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_add_set_endpoint_not_found(client: TestClient, monkeypatch):
    def mock_service():
        mock = MagicMock()
        mock.add_set.side_effect = SetNotFoundError("Set not found")
        return mock

    monkeypatch.setattr("app.api.sets_router.get_inventory_service", mock_service)

    response = client.post("/sets/", json={"set_no": "99999"})

    assert response.status_code == 404
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_core/test_services.py

# Run tests matching pattern
pytest -k "test_add_set"

# Verbose output
pytest -v
```

## Bricklink API Integration

### Authentication

Bricklink uses OAuth 1.0a authentication. Implementation:

```python
from requests_oauthlib import OAuth1Session

class BricklinkClient:
    def __init__(self, consumer_key: str, consumer_secret: str,
                 token: str, token_secret: str):
        self.base_url = "https://api.bricklink.com/api/store/v1"
        self.session = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret
        )

    async def fetch_set_metadata(self, set_no: str):
        url = f"{self.base_url}/items/SET/{set_no}"
        response = await self._request("GET", url)
        return response["data"]

    async def _request(self, method: str, url: str):
        # Add retry logic with exponential backoff
        pass
```

### Rate Limiting & Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class BricklinkClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _request(self, method: str, url: str):
        response = self.session.request(method, url)

        if response.status_code == 429:  # Rate limited
            raise BricklinkAPIError("Rate limit exceeded")

        if response.status_code >= 500:  # Server error
            raise BricklinkAPIError(f"Server error: {response.status_code}")

        response.raise_for_status()
        return response.json()
```

### API Endpoints

1. **Get Set Metadata**: `GET /items/SET/{set_no}`
2. **Get Set Inventory**: `GET /items/SET/{set_no}/subsets`
3. **Get Part Info**: `GET /items/PART/{part_no}`

### Caching Strategy

```python
from functools import lru_cache
import asyncio

class BricklinkClient:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour

    async def fetch_set_metadata(self, set_no: str):
        cache_key = f"set:{set_no}"

        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_data

        data = await self._request("GET", f"/items/SET/{set_no}")
        self._cache[cache_key] = (data, time.time())
        return data
```

## Performance Considerations for Raspberry Pi 5

### Hardware Constraints

- **RAM**: 4-8GB available
- **CPU**: 4 ARM Cortex-A76 cores @ 2.4GHz
- **Storage**: SD card (slower I/O than SSD)
- **Network**: 1 Gbps Ethernet or WiFi 6

### Optimization Strategies

1. **Database Indexing**
```python
# Add indexes to frequently queried columns
Index('ix_inventory_set_no', inventory_table.c.set_no)
Index('ix_inventory_state', inventory_table.c.state)
Index('ix_sets_set_no', sets_table.c.set_no)
```

2. **Query Optimization**
```python
# Use select specific columns instead of SELECT *
stmt = select(inventory_table.c.part_no, inventory_table.c.qty)

# Limit results
stmt = stmt.limit(100)

# Use joins instead of N+1 queries
stmt = select(inventory_table).join(sets_table)
```

3. **Connection Pooling**
```python
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Check connections before use
)
```

4. **Async I/O for External APIs**
```python
# Use httpx for async HTTP requests
import httpx

async def fetch_multiple_sets(set_numbers: list[str]):
    async with httpx.AsyncClient() as client:
        tasks = [fetch_set(client, set_no) for set_no in set_numbers]
        return await asyncio.gather(*tasks)
```

### SD Card Wear Management

- Minimize write operations
- Use write-ahead logging (WAL) mode for SQLite
- Consider moving database to USB SSD if heavy writes

```python
# Enable WAL mode
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
    execution_options={"isolation_level": "AUTOCOMMIT"}
)

with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
```

## Security Checklist

### Environment & Secrets

- [ ] Never commit `.env` file
- [ ] Use environment variables for all secrets
- [ ] Rotate API keys periodically
- [ ] Use `.env.example` as template (no real values)

### Input Validation

- [ ] Validate all user inputs with Pydantic
- [ ] Sanitize set numbers (alphanumeric only)
- [ ] Limit request payload sizes
- [ ] Validate file uploads (if added)

### API Security

- [ ] Implement rate limiting (slowapi or middleware)
- [ ] Add authentication if exposed to internet
- [ ] Use HTTPS in production (reverse proxy)
- [ ] Set appropriate CORS policies
- [ ] Add request ID tracking for debugging

### Database Security

- [ ] Use parameterized queries (SQLAlchemy handles this)
- [ ] Set appropriate file permissions on database
- [ ] Implement regular backups
- [ ] Validate data before persistence

### Example Security Middleware

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Deployment to Raspberry Pi

### Production Checklist

- [ ] Pin all dependencies with exact versions
- [ ] Set up systemd service for auto-start
- [ ] Configure log rotation
- [ ] Set up database backup script (cron job)
- [ ] Configure firewall (ufw)
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Set up monitoring (optional: Prometheus + Grafana)

### Systemd Service

Create `/etc/systemd/system/lego-inventory.service`:

```ini
[Unit]
Description=Lego Inventory Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/lego
Environment="PATH=/home/pi/lego/venv/bin"
EnvironmentFile=/home/pi/lego/.env
ExecStart=/home/pi/lego/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8081
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lego-inventory
sudo systemctl start lego-inventory
sudo systemctl status lego-inventory
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name lego.local;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Backup Script

Create `/home/pi/lego/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/pi/lego-backups"
DB_PATH="/home/pi/lego/data/lego_inventory.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/lego_inventory_$DATE.db'"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "lego_inventory_*.db" -mtime +7 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /home/pi/lego/backup.sh
```

### Log Rotation

Create `/etc/logrotate.d/lego-inventory`:

```
/var/log/lego-inventory/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 pi pi
    sharedscripts
    postrotate
        systemctl reload lego-inventory
    endscript
}
```

## Git Workflow

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring (no behavior change)
- `test:` Adding or updating tests
- `docs:` Documentation changes
- `chore:` Maintenance (dependencies, config, etc.)
- `perf:` Performance improvements

Examples:
```
feat: Add endpoint to query missing parts for a set
fix: Correct state transition for disassembled sets
refactor: Extract session management to dependency
test: Add service layer tests for add_set operation
docs: Update README with deployment instructions
```

### Branch Naming

- Feature branches: `feature/short-description`
- Bug fixes: `fix/issue-description`
- Claude sessions: `claude/description-sessionid`

### Pre-commit Hooks (Recommended)

Install pre-commit:
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]
```

Install hooks:
```bash
pre-commit install
```

## References

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic**: https://docs.pydantic.dev/latest/
- **Bricklink API**: https://www.bricklink.com/v3/api.page
- **pytest**: https://docs.pytest.org/
- **Conventional Commits**: https://www.conventionalcommits.org/

## Review History

- **2025-11-11**: Initial code review completed
  - Identified critical session management anti-pattern
  - Highlighted need for dependency injection
  - Documented missing error handling and tests
  - Overall assessment: 6/10 - Good foundation, needs refactoring
- **2025-11-11**: Documentation restructured
  - Split quick reference (CLAUDE.md) from comprehensive guide
  - Added detailed testing, deployment, and security sections
  - Improved compatibility with Claude Web and Claude Code CLI

---

**Last Updated**: 2025-11-11
