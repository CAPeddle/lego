# Architectural Decision Records (ADR)

**Project:** LEGO Inventory Service
**Last Updated:** 2025-12-02

---

## Purpose

This document records significant architectural and design decisions made during the project lifecycle. Each decision includes context, options considered, and rationale.

**ADR Format:** Based on Michael Nygard's ADR template

---

## Decision Index

Quick reference to all decisions:

| ADR # | Title | Status | Date |
|-------|-------|--------|------|
| 0001 | Use Clean Layered Architecture | Accepted | 2024-11-11 |
| 0002 | SQLite for Database | Accepted | 2024-11-11 |
| 0003 | FastAPI Web Framework | Accepted | 2024-11-11 |
| 0004 | Repository Pattern for Data Access | Accepted | 2024-11-11 |
| 0005 | Bricklink API Integration | Accepted | 2024-11-11 |
| 0006 | Part State Management | Accepted | 2024-11-11 |
| 0007 | Raspberry Pi 5 Target Platform | Accepted | 2024-11-11 |
| 0008 | Playwright for E2E Testing | Accepted | 2025-12-02 |

---

## Active Decisions

### ADR-0001: Use Clean Layered Architecture

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need to structure the FastAPI application for maintainability, testability, and clarity. The application integrates external APIs (Bricklink), manages database state, and exposes REST endpoints.

#### Decision
Implement a clean 3-layer architecture:
- **API Layer** (`app/api/`): HTTP interface, request/response handling
- **Core Layer** (`app/core/`): Business logic, domain models
- **Infrastructure Layer** (`app/infrastructure/`): External integrations (DB, APIs)

#### Consequences

**Positive:**
- Clear separation of concerns
- Each layer is independently testable
- Easy to mock dependencies for testing
- Changes to external systems isolated to infrastructure layer
- Follows SOLID principles

**Negative:**
- More boilerplate than a simple flat structure
- Requires discipline to maintain layer boundaries
- Slightly more complex dependency injection

**Risks:**
- Team members might bypass layers if not properly documented
- Over-engineering for a simple personal project

#### Alternatives Considered

1. **Flat Structure** (all in `app/`)
   - Pros: Simple, less boilerplate
   - Cons: Poor separation of concerns, hard to test
   - Reason for rejection: Doesn't scale, mixes concerns

2. **Microservices**
   - Pros: Ultimate separation
   - Cons: Massive overkill for personal project
   - Reason for rejection: Too complex for single user

#### Implementation Notes
- Use FastAPI's `Depends()` for dependency injection
- Repository interfaces defined in core, implemented in infrastructure
- Services in core orchestrate business logic
- API layer converts exceptions to HTTP responses

#### Related Decisions
- Related to ADR-0004 (Repository Pattern)
- Related to ADR-0003 (FastAPI)

---

### ADR-0002: SQLite for Database

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need persistent storage for LEGO inventory data. Requirements:
- Store sets (metadata from Bricklink)
- Store parts inventory with state tracking
- Run on Raspberry Pi 5
- Low maintenance
- Personal use (single user)

#### Decision
Use SQLite as the primary database.

#### Consequences

**Positive:**
- Zero configuration (no separate DB server)
- Embedded (perfect for Raspberry Pi)
- Sufficient for personal use (<10k sets)
- Easy backups (single file)
- Excellent Python support (SQLAlchemy)
- No network overhead
- Low resource usage

**Negative:**
- Limited concurrency (write locks entire DB)
- Not suitable for multi-user scenarios
- No built-in replication

**Risks:**
- If project grows beyond personal use, will need migration
- Concurrent writes could cause contention

#### Alternatives Considered

1. **PostgreSQL**
   - Pros: Better concurrency, production-grade
   - Cons: Requires separate server, overkill for personal use
   - Reason for rejection: Too complex for single user

2. **MongoDB**
   - Pros: Flexible schema
   - Cons: Poor relational support, resource heavy
   - Reason for rejection: Data is inherently relational

#### Implementation Notes
- Use SQLAlchemy 2.0 as ORM
- Store database in `data/lego_inventory.db`
- Configure path via `LEGO_DB_PATH` environment variable
- Repository pattern allows swapping to PostgreSQL later if needed

#### Related Decisions
- Related to ADR-0004 (Repository Pattern)
- Related to ADR-0007 (Raspberry Pi deployment)

---

### ADR-0003: FastAPI Web Framework

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need a Python web framework for REST API. Requirements:
- Async support (for Bricklink API calls)
- Type safety (Pydantic)
- OpenAPI documentation
- Modern Python features
- Good performance

#### Decision
Use FastAPI as the web framework.

#### Consequences

**Positive:**
- Built-in Pydantic validation
- Automatic OpenAPI documentation
- Native async/await support
- Excellent type hints integration
- Fast (comparable to Node.js/Go)
- Dependency injection via `Depends()`
- Active development and community

**Negative:**
- Younger than Flask/Django
- Fewer third-party integrations
- Learning curve for async patterns

**Risks:**
- Framework maturity (though now considered stable)

#### Alternatives Considered

1. **Flask**
   - Pros: Mature, large ecosystem
   - Cons: No built-in async, manual validation
   - Reason for rejection: Lacks modern features

2. **Django REST Framework**
   - Pros: Batteries included, ORM, admin panel
   - Cons: Overkill for this use case, slower
   - Reason for rejection: Too heavyweight

#### Implementation Notes
- Use Pydantic 2.x for all schemas
- Leverage dependency injection for services/repos
- Implement lifespan events for DB initialization
- Use async/await for all endpoints

#### Related Decisions
- Related to ADR-0001 (Architecture)
- Related to ADR-0005 (Bricklink integration)

---

### ADR-0004: Repository Pattern for Data Access

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need to abstract database access to:
- Make business logic testable
- Allow swapping SQLite for PostgreSQL
- Follow clean architecture principles
- Separate data access from business logic

#### Decision
Implement Repository Pattern with:
- `SqliteSetsRepository`: Manages sets
- `SqliteInventoryRepository`: Manages inventory
- Repositories injected via FastAPI `Depends()`

#### Consequences

**Positive:**
- Business logic independent of database
- Easy to test (mock repositories)
- Can swap database implementation
- Follows dependency inversion principle
- Clear data access layer

**Negative:**
- Additional abstraction layer
- More code to maintain
- Potential over-engineering

**Risks:**
- Team might bypass repositories and access DB directly

#### Alternatives Considered

1. **Active Record Pattern**
   - Pros: Simpler, less code
   - Cons: Tight coupling to database
   - Reason for rejection: Violates clean architecture

2. **Direct SQLAlchemy in Services**
   - Pros: Less abstraction
   - Cons: Hard to test, tight coupling
   - Reason for rejection: Poor testability

#### Implementation Notes
- Repository classes in `app/infrastructure/db.py`
- Accept SQLAlchemy `Session` in constructor
- Return domain models (from `app/core/models.py`)
- Methods named semantically (`add_set`, `list`, `update_item`)

#### Related Decisions
- Related to ADR-0001 (Architecture)
- Related to ADR-0002 (SQLite)

---

### ADR-0005: Bricklink API Integration

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need authoritative LEGO catalog data:
- Set information (name, year, pieces)
- Set inventory (parts list)
- Part details (colors, names)

Options: Scrape Bricklink, use Rebrickable API, use Bricklink API.

#### Decision
Integrate with official Bricklink API using OAuth 1.0a authentication.

#### Consequences

**Positive:**
- Official, authoritative data source
- Comprehensive catalog
- Supports sets, parts, colors
- Well-documented API
- Legal and ethical (no scraping)

**Negative:**
- Requires OAuth 1.0a setup
- Rate limited (unknown limits)
- API can be slow
- Requires internet connection

**Risks:**
- API changes could break integration
- Rate limiting could impact user experience

#### Alternatives Considered

1. **Rebrickable API**
   - Pros: Free, good documentation
   - Cons: Community-maintained, less authoritative
   - Reason for rejection: Prefer official source

2. **Web Scraping**
   - Pros: No API limits
   - Cons: Illegal, fragile, unethical
   - Reason for rejection: Legal/ethical concerns

#### Implementation Notes
- OAuth 1.0a client in `app/infrastructure/oauth_client.py`
- Bricklink catalog service in `app/infrastructure/bricklink_catalog.py`
- Aggressive caching (30 min TTL) with `cachetools`
- Retry logic with exponential backoff using `tenacity`
- Error handling for rate limits, timeouts

#### Related Decisions
- Related to ADR-0003 (FastAPI async support)

---

### ADR-0006: Part State Management

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need to track part states:
- Some parts needed but not owned (shopping list)
- Some parts owned but locked in assembled sets
- Some parts owned and available (free pool)

Need to support disassembling sets to free parts.

#### Decision
Implement 3-state system for parts:
- `MISSING`: Part needed but not owned
- `OWNED_LOCKED`: Part owned but assembled in set
- `OWNED_FREE`: Part owned and available

State transitions:
- `MISSING → OWNED_FREE`: Acquire part
- `OWNED_FREE → OWNED_LOCKED`: Use in set
- `OWNED_LOCKED → OWNED_FREE`: Disassemble set

#### Consequences

**Positive:**
- Clear part availability tracking
- Supports shopping list generation
- Handles set assembly/disassembly
- Simple state machine

**Negative:**
- Doesn't track which set a locked part belongs to
- Can't handle parts shared across multiple sets
- State transitions must be manual

**Risks:**
- State management bugs could corrupt inventory

#### Alternatives Considered

1. **Boolean (owned/not owned)**
   - Pros: Simpler
   - Cons: Can't distinguish locked vs free
   - Reason for rejection: Insufficient granularity

2. **Track per-set inventory**
   - Pros: Full traceability
   - Cons: Much more complex, storage overhead
   - Reason for rejection: Over-engineering for v1

#### Implementation Notes
- `PieceState` enum in `app/core/states.py`
- Stored as TEXT in SQLite with CHECK constraint
- Default state for new set: `OWNED_LOCKED` if assembled, else `OWNED_FREE`
- Update state via PATCH /inventory/

#### Related Decisions
- Related to ADR-0001 (Architecture)

---

### ADR-0007: Raspberry Pi 5 Target Platform

**Date:** 2024-11-11
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need to decide deployment platform for personal inventory service. Requirements:
- Always-on availability
- Low power consumption
- Cost-effective
- Sufficient performance

#### Decision
Deploy on Raspberry Pi 5 (4GB RAM model).

#### Consequences

**Positive:**
- Low power consumption (~5-10W)
- Affordable one-time cost
- ARM64 Python support excellent
- Sufficient for SQLite + FastAPI
- Can run 24/7
- Local control (no cloud dependencies)

**Negative:**
- Limited compute resources
- SD card failure risk
- No built-in redundancy
- Remote access requires network setup

**Risks:**
- SD card corruption (needs regular backups)
- Hardware failure (single point of failure)

#### Alternatives Considered

1. **Cloud VM (AWS/GCP)**
   - Pros: Scalable, reliable
   - Cons: Ongoing cost, overkill
   - Reason for rejection: Too expensive for personal use

2. **Desktop PC**
   - Pros: More powerful
   - Cons: High power consumption, noise
   - Reason for rejection: Not designed for 24/7 operation

#### Implementation Notes
- Use systemd for process management
- Store database on external USB drive (more reliable than SD)
- Regular backups to cloud storage
- Python 3.11+ available on Raspberry Pi OS

#### Related Decisions
- Related to ADR-0002 (SQLite choice)

---

### ADR-0008: Playwright for E2E Testing

**Date:** 2025-12-02
**Status:** Accepted
**Deciders:** Development Team

#### Context
Need end-to-end testing for REST API to verify complete workflows. Requirements:
- Test real HTTP requests
- Verify response structures
- Validate error handling
- Support CI/CD integration

#### Decision
Use Playwright (pytest-playwright) for end-to-end API testing.

#### Consequences

**Positive:**
- Modern, well-maintained tool
- Excellent Python integration
- Can test both API and future web UI
- Built-in fixtures for server lifecycle
- Multi-browser support (if web UI added)
- Great documentation

**Negative:**
- Heavier than pure pytest + httpx
- Requires browser installation
- Slight learning curve

**Risks:**
- Event loop conflicts with pytest-asyncio (mitigated by running separately)

#### Alternatives Considered

1. **httpx + pytest**
   - Pros: Lightweight, native async
   - Cons: More manual setup, no browser testing
   - Reason for rejection: Playwright provides more features

2. **Selenium**
   - Pros: Mature, widely used
   - Cons: Older, slower, more complex
   - Reason for rejection: Playwright is modern replacement

#### Implementation Notes
- E2E tests in `tests/e2e/`
- Mark with `@pytest.mark.e2e`
- Run separately: `pytest -m e2e`
- Server fixture starts uvicorn on port 8082
- Use temporary database for isolation

#### Related Decisions
- Related to ADR-0003 (FastAPI)
- Complements unit/integration testing strategy

---

## Deprecated Decisions

None yet.

---

## Notes for Future Decisions

When adding new ADRs:
1. Use the template format above
2. Increment ADR number sequentially
3. Update the Decision Index table
4. Cross-reference related decisions
5. Document both pros and cons honestly
6. Include implementation notes

**Remember:** ADRs are immutable. If a decision changes, create a new ADR that supersedes the old one. 📝
