# Quick Reference Guide

Common code patterns and snippets for this project.

## Database Session Management

### ✅ Correct Pattern
```python
# app/infrastructure/db.py
def get_db():
    """Dependency that provides database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app/api/sets_router.py
from sqlalchemy.orm import Session
from fastapi import Depends

@router.post("/")
async def add_set(
    req: CreateSetRequest,
    db: Session = Depends(get_db)
):
    repo = SqliteSetsRepository(db)
    # use repo
```

### ❌ Wrong Pattern
```python
# DON'T DO THIS
repo = SqliteSetsRepository()  # Global instance

def add(self):
    db = SessionLocal()  # Manual session creation
    try:
        # operations
        db.commit()
    finally:
        db.close()
```

## Dependency Injection

### ✅ Correct Pattern
```python
# Dependencies
def get_sets_repository(db: Session = Depends(get_db)):
    return SqliteSetsRepository(db)

def get_inventory_service(
    db: Session = Depends(get_db),
    bricklink: BricklinkClient = Depends(get_bricklink_client)
):
    sets_repo = SqliteSetsRepository(db)
    inv_repo = SqliteInventoryRepository(db)
    return InventoryService(inv_repo, sets_repo, bricklink)

# Router
@router.post("/")
async def add_set(
    req: CreateSetRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    return await service.add_set(req.set_no, req.assembled)
```

## Error Handling

### ✅ Correct Pattern
```python
# app/core/exceptions.py
class LegoServiceError(Exception):
    """Base exception"""

class SetNotFoundError(LegoServiceError):
    """Set not found in Bricklink"""

# app/core/services.py
async def add_set(self, set_no: str):
    try:
        data = await self.bricklink_client.fetch_set_metadata(set_no)
    except aiohttp.ClientError as e:
        raise BricklinkAPIError(f"Failed to fetch set {set_no}: {e}")

    if not data:
        raise SetNotFoundError(f"Set {set_no} not found")

    return self.sets_repo.add(LegoSet(**data))

# app/api/sets_router.py
@router.post("/")
async def add_set(req: CreateSetRequest, service = Depends(get_service)):
    try:
        result = await service.add_set(req.set_no)
        return {"ok": True, "set": result}
    except SetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BricklinkAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Async Patterns

### Database with Async SQLAlchemy
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///./data/lego.db")

async def get_db():
    async with AsyncSession(engine) as session:
        yield session

# Repository
class SqliteSetsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, lego_set: LegoSet):
        self.db.add(lego_set)
        await self.db.commit()
```

### Parallel Operations
```python
import asyncio

async def fetch_multiple_sets(set_numbers: list[str]):
    tasks = [fetch_set_metadata(set_no) for set_no in set_numbers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Testing Patterns

### Fixture Setup
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from app.infrastructure.db import Base, SessionLocal

@pytest.fixture
def db_session():
    """Provide test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session
    session.close()

@pytest.fixture
def mock_bricklink_client():
    """Mock Bricklink client."""
    class MockClient:
        async def fetch_set_metadata(self, set_no):
            return {"set_no": set_no, "name": "Test Set"}

        async def fetch_set_inventory(self, set_no):
            return [{"part_no": "3001", "color_id": 1, "qty": 4}]

    return MockClient()
```

### Service Test
```python
# tests/test_core/test_services.py
import pytest
from app.core.services import InventoryService

@pytest.mark.asyncio
async def test_add_set_success(db_session, mock_bricklink_client):
    sets_repo = SqliteSetsRepository(db_session)
    inv_repo = SqliteInventoryRepository(db_session)
    service = InventoryService(inv_repo, sets_repo, mock_bricklink_client)

    result = await service.add_set("75192", assembled=False)

    assert result.set_no == "75192"
    assert result.name == "Test Set"
    assert result.assembled is False
```

### API Test
```python
# tests/test_api/test_sets_router.py
from fastapi.testclient import TestClient

def test_add_set_endpoint(client: TestClient):
    response = client.post(
        "/sets/",
        json={"set_no": "75192", "assembled": false}
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
```

## Configuration Pattern

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_path: str = "./data/lego_inventory.db"
    bricklink_consumer_key: str
    bricklink_consumer_secret: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "LEGO_"

settings = Settings()

# Usage
from app.core.config import settings

engine = create_engine(f"sqlite:///{settings.db_path}")
```

## Logging Pattern

```python
# app/core/logger.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# Usage in modules
import logging
logger = logging.getLogger(__name__)

logger.info("Starting operation")
logger.error("Operation failed", exc_info=True)
```

## Lifespan Pattern

```python
# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database")
    init_db()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(lifespan=lifespan)
```

## Common SQLAlchemy Patterns

### Insert or Update
```python
async def add_part(self, set_no: str, part: Part, qty: int):
    stmt = select(inventory_table).where(
        (inventory_table.c.set_no == set_no) &
        (inventory_table.c.part_no == part.part_no)
    )
    existing = await self.db.execute(stmt)
    row = existing.first()

    if row:
        # Update
        stmt = (
            update(inventory_table)
            .where(inventory_table.c.id == row.id)
            .values(qty=row.qty + qty)
        )
    else:
        # Insert
        stmt = insert(inventory_table).values(
            set_no=set_no,
            part_no=part.part_no,
            qty=qty
        )

    await self.db.execute(stmt)
    await self.db.commit()
```

### Query with Filter
```python
async def list_by_state(self, state: PieceState):
    stmt = select(inventory_table).where(
        inventory_table.c.state == state.value
    )
    result = await self.db.execute(stmt)
    return [dict(row) for row in result.fetchall()]
```

## Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator

class CreateSetRequest(BaseModel):
    set_no: str = Field(..., pattern=r"^\d{4,6}(-\d)?$")
    assembled: bool = False

    @field_validator("set_no")
    @classmethod
    def validate_set_no(cls, v: str) -> str:
        if not v:
            raise ValueError("set_no cannot be empty")
        return v.upper()

# Usage in router automatically validates
@router.post("/")
async def add_set(req: CreateSetRequest):
    # req.set_no is already validated
    pass
```
