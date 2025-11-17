# TODO: Lego Inventory Service

**Last Updated**: 2025-11-17
**Current Status**: 67% test coverage (38 tests passing), infrastructure layer complete, critical refactoring needed before production

---

## 🧪 Test-Driven Development (TDD) Approach

**IMPORTANT**: For each todo item below, tests should be written BEFORE implementing the feature. This ensures:
- Features are designed for testability
- Tests document expected behavior
- Implementation is guided by test requirements
- Regression prevention from day one

---

## 🔴 CRITICAL PRIORITY (Do First)

These issues must be resolved before the service is production-ready. They represent fundamental design problems that affect reliability, maintainability, and testability.

### 1. Fix Session Management Anti-Pattern

**TDD: Write tests FIRST** (create `tests/test_infrastructure/test_repositories.py`):
- [ ] Test `get_db()` dependency function yields and closes session
- [ ] Test repository with injected session (no manual SessionLocal creation)
- [ ] Test session is closed after repository operations
- [ ] Test concurrent requests don't share sessions
- [ ] Test session rollback on error

**Implementation tasks**:
- [ ] Create `get_db()` dependency generator in `app/infrastructure/db.py`
- [ ] Refactor `SqliteSetsRepository` to accept session in constructor
- [ ] Refactor `SqliteInventoryRepository` to accept session in constructor
- [ ] Update all repository methods to use injected session
- [ ] Remove manual `SessionLocal()` calls from repository methods
- [ ] Verify all tests pass

**Files**: `app/infrastructure/db.py`, `app/api/sets_router.py`, `app/api/inventory_router.py`
**Estimated Effort**: 3-4 hours (including tests)
**Impact**: Prevents resource leaks, database connection exhaustion, and race conditions

---

### 2. Implement Dependency Injection

**TDD: Write tests FIRST** (create `tests/test_api/test_dependency_injection.py`):
- [ ] Test repository dependencies can be injected into endpoints
- [ ] Test service dependencies can be injected into endpoints
- [ ] Test mock repositories can be injected for testing
- [ ] Test no global state exists (test isolation)

**Implementation tasks**:
- [ ] Remove global repository instances from `app/api/sets_router.py`
- [ ] Remove global repository instances from `app/api/inventory_router.py`
- [ ] Create `get_sets_repository()` dependency function
- [ ] Create `get_inventory_repository()` dependency function
- [ ] Create `get_inventory_service()` dependency function
- [ ] Update all router endpoints to use `Depends()`
- [ ] Verify no global state remains in API layer
- [ ] Verify all tests pass

**Files**: `app/api/sets_router.py`, `app/api/inventory_router.py`, `app/infrastructure/db.py`
**Estimated Effort**: 2-3 hours (including tests)
**Impact**: Makes code testable, follows DI principles, enables mocking

---

### 3. Add Comprehensive Error Handling

**Status**: ✅ Exception hierarchy exists (100% coverage) | ⚠️ Error handling in routers/services incomplete

**TDD: Write tests FIRST** (update existing test files):
- [ ] `tests/test_core/test_services.py`: Test service error handling
  - [ ] Test `add_set()` with CatalogNotFoundError
  - [ ] Test `add_set()` with CatalogAPIError
  - [ ] Test `add_set()` with database errors
- [ ] `tests/test_api/test_error_handling.py`: Test API error responses
  - [ ] Test 404 response for SetNotFoundError
  - [ ] Test 502 response for CatalogAPIError
  - [ ] Test 400 response for InvalidSetNumberError
  - [ ] Test consistent error response format

**Implementation tasks**:
- [x] ~~Create `app/core/exceptions.py` with custom exception hierarchy~~ (COMPLETE)
- [ ] Add error handling in `InventoryService.add_set()`
- [ ] Add error handling in repository methods
- [ ] Create exception handler in `app/api/exception_handlers.py`
- [ ] Update routers to convert domain exceptions to HTTPException
- [ ] Add proper HTTP status codes (404, 502, 400, etc.)
- [ ] Add error response models with consistent format
- [ ] Verify all tests pass

**Files**: `app/core/services.py`, `app/api/*.py`, new `app/api/exception_handlers.py`
**Estimated Effort**: 2-3 hours (including tests)
**Impact**: Better debugging, user experience, and error tracking

---

### 4. Complete Test Coverage (Current: 67%)

**Status**: ✅ Infrastructure tests complete (100% coverage) | ⚠️ API/repositories untested (0% coverage)

**Current Test Status**:
- ✅ 38 tests passing
- ✅ `tests/` directory structure exists
- ✅ `tests/conftest.py` with OAuth fixtures
- ✅ `tests/test_infrastructure/test_oauth_client.py` (16 tests, 100% coverage)
- ✅ `tests/test_infrastructure/test_bricklink_catalog.py` (22 tests, 100% coverage)
- ✅ `app/core/exceptions.py` (100% coverage from existing tests)
- ✅ `pytest.ini` configured
- ✅ `pytest-cov` installed

**Missing Tests** (write these following TDD for other tasks):
- [ ] Add `db_session` fixture to `tests/conftest.py` (in-memory SQLite)
- [ ] Add `test_app` fixture to `tests/conftest.py` (FastAPI TestClient)
- [ ] Create `tests/test_infrastructure/test_repositories.py`
  - [ ] Test `SqliteSetsRepository.add()` and `get()`
  - [ ] Test `SqliteInventoryRepository.add_part()`
  - [ ] Test `SqliteInventoryRepository.list()` with state filters
  - [ ] Test `SqliteInventoryRepository.update_item()`
- [ ] Create `tests/test_core/test_services.py`
  - [ ] Test `InventoryService.add_set()` with valid data
  - [ ] Test `InventoryService.add_set()` with catalog failures
  - [ ] Test part state logic (assembled vs unassembled)
- [ ] Create `tests/test_api/test_sets_router.py`
  - [ ] Test POST `/sets/` success case
  - [ ] Test POST `/sets/` error cases
  - [ ] Test GET `/sets/{set_no}` endpoint
- [ ] Create `tests/test_api/test_inventory_router.py`
  - [ ] Test GET `/inventory/` without filters
  - [ ] Test GET `/inventory/` with state filter
  - [ ] Test PATCH `/inventory/` update
- [ ] Achieve minimum 80% code coverage

**Files**: Expand `tests/` directory
**Estimated Effort**: 4-6 hours total (but spread across implementing items #1-2)
**Impact**: Prevents regressions, enables refactoring, documents expected behavior

---

### 5. Pin Dependency Versions

**Status**: ✅ COMPLETE

- [x] ~~Research compatible versions for all dependencies~~
- [x] ~~Update `requirements.txt` with pinned versions (`==`)~~
- [x] ~~Test application with pinned versions~~ (38 tests passing)
- [ ] Document Python version requirement (3.11+) in README
- [ ] Consider creating `requirements-dev.txt` for test dependencies (currently in main requirements.txt)

**Files**: `requirements.txt`, `README.md`
**Estimated Effort**: 15 minutes (documentation only)
**Impact**: Ensures reproducible builds, prevents unexpected breakage

---

### 6. Fix Deprecated Lifespan Events

**TDD: Write tests FIRST** (create `tests/test_main.py`):
- [ ] Test database is initialized on startup
- [ ] Test app starts successfully with lifespan
- [ ] Test cleanup logic on shutdown (if applicable)

**Implementation tasks**:
- [ ] Remove `@app.on_event("startup")` decorator
- [ ] Create `@asynccontextmanager` lifespan function
- [ ] Initialize database in lifespan startup
- [ ] Add cleanup logic in lifespan shutdown (if needed)
- [ ] Update `create_app()` to use lifespan parameter
- [ ] Verify all tests pass

**Files**: `app/main.py`
**Estimated Effort**: 45 minutes (including tests)
**Impact**: Future compatibility with FastAPI, proper resource management

---

## 🟡 HIGH PRIORITY (Do Next)

These items significantly improve code quality, performance, and functionality but aren't blocking production deployment.

### 7. Resolve Async/Sync Mismatch
- [ ] Research async SQLAlchemy options for SQLite
  - Option A: Use `sqlalchemy[asyncio]` with `aiosqlite`
  - Option B: Use `asyncio.to_thread()` for sync operations
  - Option C: Accept sync limitation for single-user Raspberry Pi deployment
- [ ] Make decision on approach
- [ ] If async: Migrate to `AsyncSession` and async repository methods
- [ ] If sync: Document why sync is acceptable for this use case
- [ ] Update all database calls to be consistent

**Files**: `app/infrastructure/db.py`, all repositories
**Estimated Effort**: 3-5 hours (if going async), 30 min (if documenting sync decision)
**Impact**: Improved concurrency, proper async/await patterns

---

### 8. Implement Real Bricklink API Client
- [ ] Research Bricklink API v3 documentation
- [ ] Set up OAuth 1.0a authentication using `requests-oauthlib` or `httpx`
- [ ] Implement `fetch_set_metadata()` with real API call
- [ ] Implement `fetch_set_inventory()` with real API call
- [ ] Handle pagination for large inventories
- [ ] Add rate limiting (use `tenacity` or custom implementation)
- [ ] Add retry logic with exponential backoff
- [ ] Add comprehensive error handling
- [ ] Add response caching to reduce API calls
- [ ] Test with real Bricklink credentials in `.env`

**Files**: `app/infrastructure/bricklink_client.py`
**Estimated Effort**: 4-6 hours
**Impact**: Core functionality, enables actual use of the service

---

### 9. Add Structured Logging
- [ ] Create `app/core/logger.py` with logging configuration
- [ ] Use Python's `logging` module
- [ ] Configure different log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Add log rotation for production
- [ ] Add logging to all service methods (entry/exit, errors)
- [ ] Add logging to Bricklink client (API calls, rate limits)
- [ ] Add logging to database operations (slow queries)
- [ ] Configure log output format (JSON for production, readable for dev)
- [ ] Add request ID tracking for distributed tracing

**Files**: New `app/core/logger.py`, update all modules
**Estimated Effort**: 2-3 hours
**Impact**: Essential for debugging production issues

---

### 10. Add Database Migrations with Alembic
- [ ] Install `alembic` dependency
- [ ] Run `alembic init alembic`
- [ ] Configure `alembic.ini` for SQLite path
- [ ] Update `env.py` to use existing metadata
- [ ] Generate initial migration with current schema
- [ ] Remove `metadata.create_all()` from startup
- [ ] Update deployment docs to include migration step
- [ ] Test migrations on fresh database
- [ ] Test rollback functionality

**Files**: New `alembic/` directory, `alembic.ini`, `app/main.py`
**Estimated Effort**: 2 hours
**Impact**: Enables schema evolution, version control for database

---

### 11. Add Input Validation
- [ ] Validate set_no format (e.g., regex pattern)
- [ ] Add Pydantic validators to request models
- [ ] Validate color_id range
- [ ] Validate qty > 0
- [ ] Add database constraints (CHECK, UNIQUE, NOT NULL)
- [ ] Add meaningful validation error messages
- [ ] Test validation with invalid inputs

**Files**: `app/core/models.py`, `app/api/*.py`, `app/infrastructure/db.py`
**Estimated Effort**: 1-2 hours
**Impact**: Data integrity, better error messages

---

## 🟢 MEDIUM PRIORITY (Nice to Have)

These improvements enhance code quality and developer experience but aren't essential for initial deployment.

### 12. Add Comprehensive Docstrings
- [ ] Add module docstrings to all Python files
- [ ] Add docstrings to all classes
- [ ] Add docstrings to all public functions (Google or NumPy style)
- [ ] Document parameters and return types
- [ ] Add usage examples in docstrings
- [ ] Consider using `pydoc` or Sphinx for generated docs

**Estimated Effort**: 2-3 hours
**Impact**: Better code understanding, onboarding

---

### 13. Migrate to ORM Models
- [ ] Convert Table definitions to ORM classes
- [ ] Define relationships between models
- [ ] Use `relationship()` for set-to-inventory associations
- [ ] Update repositories to use ORM queries instead of Core
- [ ] Add lazy loading where appropriate
- [ ] Test performance impact

**Files**: `app/infrastructure/db.py`, repository methods
**Estimated Effort**: 3-4 hours
**Impact**: More Pythonic, better type safety, easier relationships

---

### 14. Add Health Check Endpoint
- [ ] Create `/health` endpoint
- [ ] Check database connectivity
- [ ] Check Bricklink API availability (optional)
- [ ] Return service status, version, uptime
- [ ] Add `/ready` endpoint for Kubernetes readiness probes

**Files**: New `app/api/health_router.py`, `app/main.py`
**Estimated Effort**: 1 hour
**Impact**: Monitoring, deployment orchestration

---

### 15. Implement Configuration Management
- [ ] Create `app/core/config.py` with `pydantic-settings`
- [ ] Define `Settings` class for all config
- [ ] Load from environment variables with prefix
- [ ] Support `.env` file loading
- [ ] Add validation for required config
- [ ] Inject settings via dependency
- [ ] Document all required environment variables

**Files**: New `app/core/config.py`, update all modules
**Estimated Effort**: 1-2 hours
**Impact**: Cleaner configuration, easier deployment

---

### 16. Add API Documentation Examples
- [ ] Add OpenAPI examples to request models
- [ ] Add OpenAPI descriptions to endpoints
- [ ] Customize Swagger UI
- [ ] Add API usage guide in `docs/api.md`
- [ ] Add example cURL commands

**Files**: `app/api/*.py`, new `docs/api.md`
**Estimated Effort**: 1-2 hours
**Impact**: Better API discoverability

---

### 17. Add Selling Feature for Parts and Sets
- [ ] Design selling workflow and states
  - [ ] Add `FOR_SALE` state to parts (or separate selling table)
  - [ ] Track which parts/sets are flagged for sale
  - [ ] Track sale price, listing date, sold date
- [ ] Create selling API endpoints
  - [ ] POST `/selling/parts` - Flag parts as for sale
  - [ ] POST `/selling/sets` - Flag entire sets as for sale
  - [ ] GET `/selling/listings` - List items for sale
  - [ ] PATCH `/selling/{id}/sold` - Mark item as sold
  - [ ] DELETE `/selling/{id}` - Remove from sale listings
- [ ] Add Bricklink listing integration (optional)
  - [ ] Research Bricklink selling API
  - [ ] Auto-create Bricklink listings
  - [ ] Sync sold status from Bricklink
- [ ] Add UI/reporting for sales tracking
  - [ ] Sales history report
  - [ ] Profit/loss tracking
  - [ ] Inventory turnover metrics

**Files**: New `app/api/selling_router.py`, `app/core/models.py`, database schema updates
**Estimated Effort**: 6-8 hours
**Impact**: Enables monetization of unwanted inventory, completes inventory lifecycle

---

## ⚪ LOW PRIORITY (Future Enhancements)

These are nice-to-have improvements for long-term maintainability and scalability.

### 18. Modernize Packaging with pyproject.toml
- [ ] Create `pyproject.toml`
- [ ] Define project metadata
- [ ] Move dependencies from requirements.txt
- [ ] Configure build system
- [ ] Add development dependencies
- [ ] Configure tool settings (ruff, mypy, pytest)

**Estimated Effort**: 1 hour
**Impact**: Modern Python packaging standards

---

### 19. Add Pre-commit Hooks
- [ ] Install `pre-commit` framework
- [ ] Configure `.pre-commit-config.yaml`
- [ ] Add ruff linting hook
- [ ] Add ruff formatting hook
- [ ] Add mypy type checking hook
- [ ] Add trailing whitespace removal
- [ ] Add commit message linting
- [ ] Document setup for contributors

**Estimated Effort**: 1 hour
**Impact**: Automated code quality enforcement

---

### 20. Set Up CI/CD Pipeline
- [ ] Create `.github/workflows/test.yml`
- [ ] Run tests on push and PR
- [ ] Run linting checks
- [ ] Run type checking
- [ ] Generate coverage report
- [ ] Add status badges to README
- [ ] Consider deployment automation

**Estimated Effort**: 2-3 hours
**Impact**: Automated testing, quality gates

---

### 21. Add CLI Interface
- [ ] Create `app/cli/` directory
- [ ] Use `typer` or `click` for CLI framework
- [ ] Add commands for common operations
  - `lego add-set <set_no>`
  - `lego list-sets`
  - `lego inventory --state MISSING`
- [ ] Add to `pyproject.toml` as console script
- [ ] Add CLI documentation

**Estimated Effort**: 3-4 hours
**Impact**: Easier local management, scriptability

---

### 22. Add Docker Support
- [ ] Create `Dockerfile` for service
- [ ] Create `docker-compose.yml` for local development
- [ ] Configure volume for database persistence
- [ ] Add environment variable passing
- [ ] Document Docker deployment
- [ ] Consider multi-stage builds for smaller images

**Estimated Effort**: 2-3 hours
**Impact**: Easier deployment, consistency across environments

---

### 23. Add Monitoring and Metrics
- [ ] Add Prometheus metrics endpoint
- [ ] Track request counts, latency
- [ ] Track Bricklink API call metrics
- [ ] Track database query performance
- [ ] Consider Grafana dashboard
- [ ] Add alerting for errors

**Estimated Effort**: 3-4 hours
**Impact**: Production observability

---

## Progress Tracking

**Test Coverage**: 67% (38 tests passing)
- ✅ Infrastructure layer: 100% coverage
- ✅ Core exceptions: 100% coverage
- ⚠️ API layer: 0% coverage (needs tests)
- ⚠️ Repositories: Partially tested
- ⚠️ Core services: Needs tests

**Critical Tasks**: 1.5/6 complete
- ✅ Item #5: Dependency versions pinned
- ✅ Item #3: Exception hierarchy created (error handling incomplete)
- ✅ Item #4: Test infrastructure established (API/repository tests needed)
- ⚠️ Items #1-2, #6: Need implementation

**High Priority Tasks**: 0/5 complete
**Medium Priority Tasks**: 0/7 complete
**Low Priority Tasks**: 0/6 complete

**Overall Completion**: 1.5/24 (6.25%)

---

## Notes

- **TDD Approach**: Write tests FIRST for each feature before implementing
- Items can be reordered based on actual development priorities
- Estimated efforts are rough guidelines for a single developer and include test writing time
- Some tasks have dependencies (e.g., API tests require DI to be fixed first)
- Consider tackling critical tasks in order for maximum impact
- Review and update this TODO regularly as work progresses
- Current test coverage: 67% (target: 80%+)

**Next recommended task**: Start with item #1 (Session Management) as it's foundational for items #2-4.

**TDD Workflow**:
1. Write failing tests that define expected behavior
2. Run tests to confirm they fail (`pytest -v`)
3. Implement minimal code to make tests pass
4. Refactor while keeping tests green
5. Commit with tests and implementation together
