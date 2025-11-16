---
name: fastapi-review
description: Code review skill for FastAPI/Python projects. Reviews for security, performance, deployment readiness (especially Raspberry Pi), API design, and Python best practices. Use when reviewing FastAPI applications, API endpoints, Python services, or deployment configurations.
---

# FastAPI/Python Code Review

## Core Principles
- Security first: Authentication, authorization, input validation
- Deployment-ready: Works reliably on Raspberry Pi and production environments
- Maintainable: Clear, testable, well-documented code
- Production-tested: Proper error handling, logging, monitoring

## 1. Security Review

### Authentication & Authorization
**Check for:**
- [ ] Proper authentication on all protected endpoints
- [ ] Authorization checks verify user permissions, not just authentication
- [ ] JWT tokens validated properly (signature, expiration, claims)
- [ ] API keys stored securely (environment variables, never hardcoded)
- [ ] Password hashing uses bcrypt or similar (never plain text)

**Example - Good Authentication:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Verify claims, expiration, etc.
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected")
async def protected_route(user = Depends(verify_token)):
    return {"user": user}
```

### Input Validation
**Check for:**
- [ ] All user inputs validated with Pydantic models
- [ ] File uploads have size limits and type validation
- [ ] Path parameters validated (no directory traversal)
- [ ] Query parameters have proper constraints

**Example - Proper Validation:**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class UserCreate(BaseModel):
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    age: Optional[int] = Field(None, ge=0, le=150)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### SQL/Database Security
**Check for:**
- [ ] All queries use parameterized statements (ORM or prepared statements)
- [ ] No string formatting/concatenation in SQL queries
- [ ] Database credentials from environment variables
- [ ] Connection pooling configured properly

**❌ Bad:**
```python
# NEVER DO THIS - SQL Injection risk
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

**✅ Good:**
```python
# Use SQLAlchemy or parameterized queries
from sqlalchemy import select
result = await session.execute(
    select(User).where(User.email == email)
)
```

### API Security
**Check for:**
- [ ] CORS configured restrictively (not `allow_origins=["*"]` in production)
- [ ] Rate limiting on expensive endpoints
- [ ] Proper error handling (don't leak sensitive info in errors)
- [ ] HTTPS enforced in production

**Example - Proper CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ Bad - Too permissive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # NEVER in production
    allow_credentials=True,
)

# ✅ Good - Restrictive
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 2. FastAPI Best Practices

### Async/Await Usage
**Check for:**
- [ ] Use `async def` for I/O-bound operations (database, API calls)
- [ ] Use regular `def` for CPU-bound operations
- [ ] Don't mix blocking code in async functions
- [ ] Proper use of `await` for async operations

**Example:**
```python
# ✅ Good - I/O bound operations are async
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Database query is I/O bound
    user = await db.execute(select(User).where(User.id == user_id))
    return user.scalar_one_or_none()

# ✅ Good - CPU bound operations are sync
@app.post("/process")
def process_data(data: List[int]):
    # Heavy computation, not I/O bound
    return {"result": sum(data) / len(data)}

# ❌ Bad - Blocking code in async function
@app.get("/bad")
async def bad_endpoint():
    time.sleep(5)  # Blocks entire event loop!
    return {"status": "done"}

# ✅ Good - Use asyncio.sleep instead
@app.get("/good")
async def good_endpoint():
    await asyncio.sleep(5)
    return {"status": "done"}
```

### Dependency Injection
**Check for:**
- [ ] Database sessions use `Depends()` and are properly closed
- [ ] No global state (use dependency injection)
- [ ] Dependencies are reusable and testable

**Example:**
```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # Session automatically closed after request
    items = await db.execute(select(Item))
    return items.scalars().all()
```

### Response Models
**Check for:**
- [ ] All endpoints have `response_model` defined
- [ ] Sensitive fields excluded (passwords, internal IDs)
- [ ] Response models match actual returns

**Example:**
```python
class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models

class UserInDB(UserResponse):
    hashed_password: str  # Never expose this

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # hashed_password automatically excluded
    return user_from_db
```

### Error Handling
**Check for:**
- [ ] Specific exception handlers defined
- [ ] Errors return proper HTTP status codes
- [ ] Error messages don't leak sensitive information
- [ ] All exceptions logged appropriately

**Example:**
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    # Log full error for debugging
    logger.error(f"ValueError: {exc}", exc_info=True)
    # Return generic message to user
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid input provided"}
    )

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await get_item_from_db(item_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found"
        )
    return item
```

## 3. Raspberry Pi Deployment Considerations

### Service Configuration
**Check for:**
- [ ] Proper systemd service file with restart policies
- [ ] Correct user permissions (don't run as root unless necessary)
- [ ] Environment variables loaded properly
- [ ] Logs directed to appropriate location

**Example systemd service:**
```ini
[Unit]
Description= FastAPI Application
After=network.target

[Service]
Type=simple
User=cpeddle
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Network Binding
**Check for:**
- [ ] Host binding is explicit (`0.0.0.0` for external access, `127.0.0.1` for local)
- [ ] Port is configurable via environment variable
- [ ] No hardcoded localhost references that prevent external access

**Example:**
```python
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),  # Allow external connections
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV") == "development"
    )
```

### Resource Constraints
**Check for:**
- [ ] Worker count appropriate for Pi's CPU cores (usually 2-4)
- [ ] Memory-intensive operations are paginated
- [ ] Database connection pool size is reasonable
- [ ] File uploads have size limits

**Example:**
```python
# Configure for limited resources
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # Not too many for Pi
    max_overflow=10,
    pool_pre_ping=True,   # Check connections before use
    pool_recycle=3600,    # Recycle connections hourly
)
```

### Process Management
**Check for:**
- [ ] Gunicorn/Uvicorn configured appropriately for Pi
- [ ] Graceful shutdown handling
- [ ] No memory leaks in long-running processes

**Example Uvicorn config:**
```python
# For Raspberry Pi - limited workers
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \          # Match CPU cores
  --timeout-keep-alive 30 \
  --limit-concurrency 100
```

## 4. Python Environment & Dependencies

### Virtual Environment
**Check for:**
- [ ] Requirements.txt or pyproject.toml is up to date
- [ ] Pinned versions for critical dependencies
- [ ] No unnecessary dependencies

**Example requirements.txt:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
asyncpg==0.29.0  # For PostgreSQL
python-jose[cryptography]==3.3.0  # For JWT
passlib[bcrypt]==1.7.4
python-multipart==0.0.6  # For file uploads
```

### Configuration Management
**Check for:**
- [ ] Settings use Pydantic BaseSettings
- [ ] Secrets loaded from environment variables
- [ ] Different configs for dev/staging/production

**Example:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "API"
    database_url: str
    secret_key: str
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

## 5. Testing

### Test Coverage
**Check for:**
- [ ] Unit tests for business logic
- [ ] Integration tests for API endpoints
- [ ] Test database fixtures properly isolated
- [ ] Async tests use pytest-asyncio

**Example:**
```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            json={"email": "test@gmail.com", "password": "secure123"}
        )
    assert response.status_code == 201
    assert response.json()["email"] == "test@gmail.com"

@pytest.mark.asyncio
async def test_unauthorized_access():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/protected")
    assert response.status_code == 401
```

## 6. Logging & Monitoring

### Logging
**Check for:**
- [ ] Structured logging (JSON format preferred)
- [ ] Appropriate log levels used
- [ ] No sensitive data in logs (passwords, tokens)
- [ ] Request IDs for tracing

**Example:**
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logger
logger = logging.getLogger("cpeddle")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Health Checks
**Check for:**
- [ ] Health check endpoint exists
- [ ] Checks database connectivity
- [ ] Returns appropriate status codes

**Example:**
```python
from fastapi import status

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )
```

## 7. Common Pitfalls to Watch For

### Memory Leaks
```python
# ❌ Bad - Accumulates in memory
@app.get("/bad")
async def bad_endpoint():
    global cache  # Global cache never cleared
    cache[request_id] = large_data
    return {"status": "ok"}

# ✅ Good - Use TTL cache or Redis
from cachetools import TTLCache
cache = TTLCache(maxsize=100, ttl=300)
```

### Blocking Operations
```python
# ❌ Bad - Blocks event loop
@app.post("/process-file")
async def process_file(file: UploadFile):
    content = file.file.read()  # Blocking I/O
    process_large_file(content)  # Blocking CPU work

# ✅ Good - Use background tasks or task queue
from fastapi import BackgroundTasks

@app.post("/process-file")
async def process_file(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    content = await file.read()  # Non-blocking
    background_tasks.add_task(process_large_file, content)
    return {"status": "processing"}
```

### Database Connection Leaks
```python
# ❌ Bad - Connection not closed on error
@app.get("/bad")
async def bad_endpoint():
    db = get_db_connection()
    result = db.query("SELECT * FROM table")
    return result
    # Connection never closed if error occurs

# ✅ Good - Use dependency injection with cleanup
@app.get("/good")
async def good_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Table))
    return result.scalars().all()
    # Dependency system ensures cleanup
```

## When to Use This Skill

Use this skill when:
- Reviewing pull requests for FastAPI applications
- Conducting security audits
- Preparing for production deployment
- Onboarding new developers to  standards
- Troubleshooting deployment issues on Raspberry Pi
- Updating existing services from Gunicorn to FastAPI

## Pre-Review Checklist

Before requesting code review:
- [ ] All tests passing
- [ ] No hardcoded credentials or secrets
- [ ] Environment variables documented in README
- [ ] Deployment instructions updated if needed
- [ ] Logging appropriately covers key operations
- [ ] Error handling covers edge cases
- [ ] API documentation (OpenAPI) is accurate
- [ ] Code passes linting (black, ruff, mypy)

## Review Priority Levels

**🔴 Critical (Must Fix):**
- Security vulnerabilities
- Data corruption risks
- Service crashes/instability

**🟡 Important (Should Fix):**
- Performance issues
- Incorrect error handling
- Missing tests for critical paths

**🟢 Nice to Have (Optional):**
- Code style improvements
- Optimization opportunities
- Additional documentation
