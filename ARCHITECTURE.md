# System Architecture

**Project:** LEGO Inventory Service
**Version:** 0.1.0
**Last Updated:** 2025-12-02

---

## Overview

FastAPI-based LEGO inventory management service for Raspberry Pi 5. Tracks LEGO sets, parts inventory, and integrates with Bricklink API for catalog data.

**Architecture Style:** Layered (3-tier) with Clean Architecture principles

---

## System Context

### Purpose
Manage LEGO inventory by:
- Tracking owned LEGO sets
- Managing individual parts inventory with state tracking (MISSING, OWNED_LOCKED, OWNED_FREE)
- Integrating with Bricklink API for set and part catalog information
- Running on Raspberry Pi 5 for local inventory management

### Constraints
- **Platform**: Raspberry Pi 5 (ARM64, limited resources)
- **Database**: SQLite for simplicity and portability
- **Deployment**: Self-hosted, no cloud dependencies
- **Network**: Requires internet for Bricklink API integration
- **Performance**: Low concurrency (personal use)

### Assumptions
- Single user environment
- Moderate data volume (< 10,000 sets, < 100,000 parts)
- Occasional Bricklink API access (cached aggressively)
- Runs 24/7 on Raspberry Pi

---

## Architectural Principles

Following **WAY_OF_WORK.md** standards:

### SOLID Principles
- **Single Responsibility**: Each layer (API, Core, Infrastructure) has one concern
- **Open/Closed**: Services open for extension via dependency injection
- **Liskov Substitution**: Repository interfaces are interchangeable
- **Interface Segregation**: Specific repositories per domain entity
- **Dependency Inversion**: Services depend on repository abstractions

### Additional Principles
- **Separation of Concerns**: Clean boundaries between API, domain logic, and data access
- **DRY**: Common patterns abstracted (exception handling, response models)
- **KISS**: Simple SQLite, straightforward REST API
- **YAGNI**: No premature optimization for multi-user or cloud deployment

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│     (Web Browser, Mobile App, API Consumer)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/REST
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   API Layer (app/api/)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FastAPI Application                              │  │
│  │  - sets_router: Set management endpoints          │  │
│  │  - inventory_router: Inventory endpoints          │  │
│  │  - schemas: Request/Response models (Pydantic)    │  │
│  │  - Dependency Injection (get_db, get_repos)       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           Core Layer (app/core/)                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Business Logic                                   │  │
│  │  - services.py: InventoryService                  │  │
│  │  - models.py: Domain models (LegoSet, Part)       │  │
│  │  - states.py: Part state enum                     │  │
│  │  - exceptions.py: Custom exceptions               │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│      Infrastructure Layer (app/infrastructure/)          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  External Integrations                            │  │
│  │  - db.py: SQLite repositories                     │  │
│  │  - bricklink_client.py: Bricklink API client      │  │
│  │  - bricklink_catalog.py: Catalog service          │  │
│  │  - oauth_client.py: OAuth HTTP client             │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│  SQLite Database │    │  Bricklink API   │
│  (Local)         │    │  (External)      │
└──────────────────┘    └──────────────────┘
```

### Component Diagram

```
app/
├── api/                       # API Layer (HTTP interface)
│   ├── sets_router.py        # POST /sets/ - Add sets
│   ├── inventory_router.py   # GET, PATCH /inventory/ - Manage inventory
│   └── schemas.py            # Request/Response models
│
├── core/                     # Core Business Logic
│   ├── services.py           # InventoryService
│   ├── models.py             # Domain models
│   ├── states.py             # PieceState enum
│   └── exceptions.py         # Custom exceptions
│
├── infrastructure/           # External Integrations
│   ├── db.py                 # SQLite repositories
│   ├── bricklink_client.py   # Bricklink API integration
│   ├── bricklink_catalog.py  # Catalog service with caching
│   └── oauth_client.py       # OAuth HTTP client
│
└── main.py                   # Application entry point
```

---

## Layer Responsibilities

### 1. API Layer (`app/api/`)

**Responsibility:** HTTP interface, request/response handling

**Components:**
- **sets_router.py**: Endpoints for adding LEGO sets
- **inventory_router.py**: Endpoints for listing and updating inventory
- **schemas.py**: Pydantic models for validation and serialization

**Rules:**
- No business logic here
- Only request validation and response formatting
- Delegates to service layer
- Handles HTTP concerns (status codes, exceptions)

**Example:**
```python
@router.post("/", response_model=CreateSetResponse)
async def add_set(
    req: CreateSetRequest,
    service: InventoryService = Depends(get_inventory_service),
):
    try:
        lego_set = await service.add_set(req.set_no, assembled=req.assembled)
        return {"ok": True, "set": LegoSetResponse(**lego_set.model_dump())}
    except SetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 2. Core Layer (`app/core/`)

**Responsibility:** Business logic and domain models

**Components:**
- **services.py**: `InventoryService` orchestrates set/inventory operations
- **models.py**: Domain models (`LegoSet`, `InventoryItem`)
- **states.py**: `PieceState` enum (MISSING, OWNED_LOCKED, OWNED_FREE)
- **exceptions.py**: Custom exceptions

**Rules:**
- Contains all business logic
- Coordinates between repositories and external services
- No direct database access (uses repositories)
- Returns domain models

**Example:**
```python
class InventoryService:
    async def add_set(
        self, set_no: str, assembled: bool
    ) -> LegoSet:
        # Fetch from Bricklink
        set_info = await self.bricklink_client.get_set_info(set_no)

        # Save set
        lego_set = self.sets_repo.add_set(set_info, assembled)

        # Fetch and save inventory
        inventory = await self.bricklink_client.get_set_inventory(set_no)
        state = PieceState.OWNED_LOCKED if assembled else PieceState.OWNED_FREE
        self.inventory_repo.add_or_update_parts(inventory, state)

        return lego_set
```

### 3. Infrastructure Layer (`app/infrastructure/`)

**Responsibility:** External integrations (database, APIs)

**Components:**
- **db.py**: SQLite repositories for sets and inventory
- **bricklink_client.py**: High-level Bricklink API client
- **bricklink_catalog.py**: Catalog service with caching and retry logic
- **oauth_client.py**: OAuth 1.0a HTTP client

**Rules:**
- Only layer that touches external systems
- No business logic
- Returns domain models
- Implements retry, caching, error handling

---

## Data Flow

### Request Flow: Add Set (Write Operation)

```
1. Client sends POST /sets/ {set_no: "75192-1", assembled: false}
   ↓
2. API Layer (sets_router.py)
   - Validates request (CreateSetRequest schema)
   - Injects InventoryService via FastAPI Depends
   ↓
3. Service Layer (InventoryService)
   - Calls Bricklink API to fetch set info
   - Calls Bricklink API to fetch inventory
   - Saves set to database via sets_repo
   - Saves parts to inventory via inventory_repo
   - Determines part state based on assembled flag
   ↓
4. Infrastructure Layer (Repositories)
   - SqliteSetsRepository creates set record
   - SqliteInventoryRepository adds/updates parts
   ↓
5. Returns through layers
   - Repository → Service → API
   ↓
6. API Layer serializes response
   - Returns CreateSetResponse with set details
   ↓
7. Client receives 200 OK with set data
```

### Request Flow: List Inventory (Read Operation)

```
1. Client sends GET /inventory/?state=OWNED_FREE
   ↓
2. API Layer (inventory_router.py)
   - Validates query params (state filter)
   - Injects SqliteInventoryRepository
   ↓
3. Repository Layer (SqliteInventoryRepository)
   - Queries database with state filter
   - Maps rows to InventoryItemResponse models
   ↓
4. Returns through layers
   - Repository → API
   ↓
5. API Layer serializes response
   - Returns InventoryListResponse {items: [...], count: N}
   ↓
6. Client receives 200 OK with inventory list
```

---

## Key Architectural Decisions

See `DECISIONS.md` for detailed ADRs.

### Decision: Clean Layered Architecture

**Rationale:**
- Clear separation of concerns (API, Core, Infrastructure)
- Testable (can mock each layer)
- Maintainable (changes isolated to layers)
- Follows SOLID principles

### Decision: Repository Pattern

**Rationale:**
- Abstracts data access
- Easier to test (mock repositories)
- Can swap SQLite for PostgreSQL if needed
- Follows dependency inversion principle

### Decision: Dependency Injection (FastAPI)

**Rationale:**
- Loose coupling between components
- Easier testing (inject mocks)
- FastAPI native support via `Depends()`
- Clear dependency graph

### Decision: SQLite Database

**Rationale:**
- Zero configuration
- Perfect for Raspberry Pi (embedded)
- No separate DB server needed
- Sufficient for personal use (<10k sets)
- Can migrate to PostgreSQL if needed

### Decision: Bricklink API Integration

**Rationale:**
- Authoritative source for LEGO catalog data
- OAuth 1.0a authentication
- Cached aggressively (cachetools)
- Retry logic with exponential backoff (tenacity)

---

## Integration Points

### External Services

```
┌────────────────┐
│  LEGO Inventory│
│  Service       │
└────────┬───────┘
         │
         └─────→ [Bricklink API] (OAuth 1.0a)
                 - GET /items/SET/{set_no}
                 - GET /items/SET/{set_no}/subsets
                 - Rate limited, cached (30 min TTL)
```

### Database Schema

```sql
-- Sets table
CREATE TABLE sets (
    set_no TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    year INTEGER,
    theme TEXT,
    pieces INTEGER,
    assembled BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory table
CREATE TABLE inventory (
    part_no TEXT NOT NULL,
    color_id INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('MISSING', 'OWNED_LOCKED', 'OWNED_FREE')),
    PRIMARY KEY (part_no, color_id)
);

-- Part state transitions:
-- MISSING → OWNED_FREE (acquired part)
-- OWNED_FREE → OWNED_LOCKED (used in set)
-- OWNED_LOCKED → OWNED_FREE (disassembled set)
```

---

## Scalability Considerations

### Current Scale
- Expected sets: 100-1,000
- Expected parts: 10,000-100,000
- Requests/day: <1,000 (personal use)
- Data volume: <100MB

### Scaling Strategy

**Current (Phase 1): Single Raspberry Pi**
- SQLite for simplicity
- Single uvicorn process
- No caching infrastructure needed (cachetools in-memory)

**Future (if needed):**
- **Database**: Migrate to PostgreSQL for concurrency
- **Caching**: Add Redis for shared cache across processes
- **API**: Add nginx reverse proxy + multiple uvicorn workers
- **Monitoring**: Add Prometheus + Grafana

---

## Security Architecture

### Authentication & Authorization
- Currently: No authentication (local network only)
- Future: Consider API keys or OAuth if exposed externally

### Data Security
- Bricklink OAuth credentials in `.env` file
- No user data stored (personal inventory only)
- SQLite file permissions restricted

### API Security
- Input validation via Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- Rate limiting (future): Consider if exposing externally

---

## Deployment Architecture

### Current: Raspberry Pi 5

```
┌─────────────────────────────────────┐
│       Raspberry Pi 5 (ARM64)        │
│  ┌───────────────────────────────┐  │
│  │  Uvicorn Server (port 8081)   │  │
│  │  - FastAPI application        │  │
│  │  - In-memory cache            │  │
│  └─────────────┬─────────────────┘  │
│                ↓                     │
│  ┌───────────────────────────────┐  │
│  │  SQLite Database              │  │
│  │  data/lego_inventory.db       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
           ↓ (outbound HTTPS)
   ┌──────────────────┐
   │  Bricklink API   │
   └──────────────────┘
```

### Environment Configuration

- **Development**: Local machine (WSL2/Windows)
- **Production**: Raspberry Pi 5 (systemd service)
- Config via `.env` file (see `.env.example`)

---

## Monitoring & Observability

### Logging
- Python logging module (INFO level)
- Format: `%(asctime)s %(levelname)s [%(name)s] %(message)s`
- Logs HTTP requests, Bricklink API calls, errors

### Health Checks
- `GET /health` endpoint
  - Returns `{"status": "ok"}` if DB accessible
  - Returns `{"status": "error"}` if DB unavailable

### Metrics (Future)
- Request rate, latency, error rate
- Bricklink API call rate and cache hit ratio
- Database query performance

---

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+ (3.12+ recommended)
- **Framework**: FastAPI 0.109.0
- **Database**: SQLite 3
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.5
- **HTTP Client**: aiohttp 3.9 (async)
- **OAuth**: requests-oauthlib 1.3

### Development Tools
- **Code Formatting**: Black
- **Linting**: Ruff
- **Type Checking**: mypy
- **Security Scanning**: Bandit
- **Testing**: pytest + pytest-asyncio + pytest-playwright
- **Pre-commit**: pre-commit hooks

### Infrastructure
- **Platform**: Raspberry Pi OS (Debian-based)
- **Process Manager**: systemd (future)
- **Reverse Proxy**: None (direct uvicorn access)

---

## Testing Strategy

### Test Coverage: 67% (Target: 80%+)

**Test Structure:**
```
tests/
├── unit/                     # Unit tests (TBD)
├── integration/              # Integration tests (TBD)
├── e2e/                      # End-to-end tests (Playwright)
│   ├── test_sets_e2e.py
│   └── test_inventory_e2e.py
├── test_core/                # Core layer tests
│   └── test_services.py
└── test_infrastructure/      # Infrastructure tests
    ├── test_bricklink_catalog.py
    └── test_oauth_client.py
```

**Test Types:**
1. **Unit Tests**: Test individual functions/classes
2. **Integration Tests**: Test layer interactions
3. **E2E Tests**: Test complete workflows (Playwright)

---

## Future Considerations

### Potential Improvements
- Add authentication (API keys or OAuth)
- Implement WebSocket for real-time updates
- Add barcode scanning for easier data entry
- Create mobile app (React Native)
- Add backup/restore functionality
- Implement data export (CSV, Excel)

### Known Limitations
- Single user only
- No authentication/authorization
- SQLite concurrency limits
- No real-time updates
- Manual Bricklink OAuth setup

---

## References

- **WAY_OF_WORK.md**: Universal development methodology
- **DECISIONS.md**: Architectural decision records
- **RESEARCH_LOG.md**: Technical investigations
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Bricklink API**: https://www.bricklink.com/v3/api.page

---

**Note:** This architecture document is living documentation. Update when:
- Adding new components
- Making architectural changes
- Scaling the system
- Learning new patterns

Keep it current! 🏗️
