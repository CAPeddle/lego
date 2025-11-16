# Python FastAPI + SQLite Quick Reference

Quick reference for Python web apps with FastAPI, SQLite, and mobile app backends.

## 🔴 Critical Security (Always Check)

### Authentication & Authorization
```python
# ✅ JWT validation (not just decoding)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password)
```

### SQL Injection Prevention
```python
# ❌ NEVER use string formatting
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ ALWAYS use SQLAlchemy or parameterized queries
result = await db.execute(select(User).where(User.email == email))
```

### Input Validation
```python
from pydantic import BaseModel, Field, field_validator

class CreateRequest(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    set_no: str = Field(..., pattern=r"^\d{4,6}(-\d)?$")
    
    @field_validator("set_no")
    @classmethod
    def validate_set_no(cls, v: str) -> str:
        return v.upper()
```

## 💾 Database Patterns

### Session Management (Sync SQLAlchemy)
```python
# ✅ Correct - Dependency injection with cleanup
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/items")
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db)
):
    repo = ItemRepository(db)
    return repo.add(item)

# ❌ Wrong - Manual session management
repo = ItemRepository()  # Global instance
def add(self):
    db = SessionLocal()  # Manual session
    try:
        db.commit()
    finally:
        db.close()
```

### Async SQLAlchemy (Optional)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///./data/app.db")

async def get_db():
    async with AsyncSession(engine) as session:
        yield session

class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add(self, item):
        self.db.add(item)
        await self.db.commit()
```

### Common Queries
```python
# Insert or Update
stmt = select(table).where(table.c.id == item_id)
existing = await db.execute(stmt)
row = existing.first()

if row:
    stmt = update(table).where(table.c.id == row.id).values(qty=row.qty + 1)
else:
    stmt = insert(table).values(id=item_id, qty=1)

await db.execute(stmt)
await db.commit()

# Query with filter
stmt = select(table).where(table.c.status == "active")
result = await db.execute(stmt)
return [dict(row) for row in result.fetchall()]
```

## 🔧 Dependency Injection Pattern

```python
# Dependencies
def get_repository(db: Session = Depends(get_db)):
    return ItemRepository(db)

def get_service(
    db: Session = Depends(get_db),
    api_client: APIClient = Depends(get_api_client)
):
    repo = ItemRepository(db)
    return ItemService(repo, api_client)

# Router
@router.post("/")
async def create_item(
    req: CreateRequest,
    service: ItemService = Depends(get_service)
):
    return await service.create(req.item_id)
```

## ⚡ FastAPI Best Practices

### Async/Await
```python
# ✅ I/O operations are async
@app.get("/items")
async def get_items(db: Session = Depends(get_db)):
    return await db.execute(select(Item))

# ✅ CPU operations are sync
@app.post("/calculate")
def calculate(data: List[int]):
    return sum(data) / len(data)

# ❌ Never block async with time.sleep()
async def bad():
    time.sleep(5)  # Blocks event loop!

# ✅ Use asyncio.sleep() or run_in_executor()
async def good():
    await asyncio.sleep(5)
```

### Response Models
```python
class ItemResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models

@app.get("/items/{id}", response_model=ItemResponse)
async def get_item(id: int):
    # Automatically excludes fields not in ItemResponse
    return item_from_db
```

## 🚨 Error Handling

```python
# Custom exceptions
class AppError(Exception):
    """Base exception"""

class ItemNotFoundError(AppError):
    """Item not found"""

# Service layer
async def get_item(self, item_id: str):
    try:
        data = await self.api_client.fetch(item_id)
    except aiohttp.ClientError as e:
        raise APIError(f"Failed to fetch: {e}")
    
    if not data:
        raise ItemNotFoundError(f"Item {item_id} not found")
    
    return self.repo.add(Item(**data))

# Router layer
@router.get("/{item_id}")
async def get_item(item_id: str, service = Depends(get_service)):
    try:
        result = await service.get_item(item_id)
        return {"ok": True, "item": result}
    except ItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Internal error")
```

## 🧪 Testing Patterns

### Fixtures
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session
    session.close()

@pytest.fixture
def mock_api_client():
    class MockClient:
        async def fetch(self, id):
            return {"id": id, "name": "Test"}
    return MockClient()
```

### Service Tests
```python
@pytest.mark.asyncio
async def test_create_item(db_session, mock_api_client):
    repo = ItemRepository(db_session)
    service = ItemService(repo, mock_api_client)
    
    result = await service.create_item("ABC123")
    
    assert result.id == "ABC123"
    assert result.name == "Test"
```

### API Tests
```python
from fastapi.testclient import TestClient

def test_create_endpoint(client: TestClient):
    response = client.post("/items/", json={"id": "ABC123"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
```

## ⚙️ Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_path: str = "./data/app.db"
    api_key: str
    api_secret: str
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "APP_"

settings = Settings()

# Usage
engine = create_engine(f"sqlite:///{settings.db_path}")
```

## 📝 Logging

```python
import logging
import sys

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# In modules
logger = logging.getLogger(__name__)
logger.info("Operation started")
logger.error("Failed", exc_info=True)
```

## 🚀 Application Startup

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database")
    init_db()
    
    yield
    
    # Shutdown
    logger.info("Shutting down")

app = FastAPI(lifespan=lifespan)
```

## 🔌 Raspberry Pi / Mobile Backend

### CORS for Mobile Apps
```python
from fastapi.middleware.cors import CORSMiddleware

# ✅ Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Production - Specific origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",
        "http://localhost:3000"  # For development
    ],
    allow_credentials=True,
)
```

### Network Binding
```python
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),  # External access
        port=int(os.getenv("PORT", "8000")),
        workers=2,  # Limited for Pi
        reload=os.getenv("ENV") == "development"
    )
```

### Health Check
```python
@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Unhealthy")
```

## 🚫 Common Pitfalls

### Memory Leaks
```python
# ❌ Global cache grows unbounded
global_cache = {}
cache[id] = large_data

# ✅ Use TTL cache
from cachetools import TTLCache
cache = TTLCache(maxsize=100, ttl=300)
```

### Database Connections
```python
# ❌ Manual connection not closed on error
db = get_connection()
result = db.query()
return result

# ✅ Dependency injection ensures cleanup
async def endpoint(db: Session = Depends(get_db)):
    return await db.execute(query)
```

### Blocking Operations
```python
# ❌ Blocks event loop
@app.post("/process")
async def process(file: UploadFile):
    content = file.file.read()  # Blocking
    heavy_processing(content)   # Blocking

# ✅ Use background tasks
from fastapi import BackgroundTasks

@app.post("/process")
async def process(file: UploadFile, bg: BackgroundTasks):
    content = await file.read()  # Non-blocking
    bg.add_task(heavy_processing, content)
    return {"status": "processing"}
```

## 📱 Mobile API Patterns

### Pagination
```python
@app.get("/items")
async def list_items(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    items = await db.execute(
        select(Item).offset(skip).limit(limit)
    )
    return {"items": items.scalars().all(), "skip": skip, "limit": limit}
```

### File Uploads
```python
from fastapi import File, UploadFile

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Validate
    if file.size > 10_000_000:  # 10MB
        raise HTTPException(400, "File too large")
    
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Invalid file type")
    
    # Save
    content = await file.read()
    path = f"./uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(content)
    
    return {"filename": file.filename, "size": file.size}
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, creds: LoginRequest):
    # Limited to 5 attempts per minute
    return authenticate(creds)
```

## 📋 Pre-Deploy Checklist

- [ ] All tests passing
- [ ] No hardcoded secrets (use .env)
- [ ] CORS configured for production
- [ ] Error handling covers edge cases
- [ ] Health check endpoint works
- [ ] Logging covers key operations
- [ ] Database migrations ready
- [ ] API documentation accurate

## 💡 Quick Commands

```bash
# Run development server
uvicorn main:app --reload --host 0.0.0.0

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=app tests/

# Lint code
black . && ruff check .

# Generate requirements
pip freeze > requirements.txt

# Start with specific config
ENV=production uvicorn main:app --host 0.0.0.0 --workers 2
```

---

**Project-Specific Notes:**
- Lego Inventory: Uses Bricklink API for metadata
- Ski Trip: TBD - add specific patterns as needed
