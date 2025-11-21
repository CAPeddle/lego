# Code Review & Audit Findings

Date: 2025-11-21  
Scope: Full pass over current repository (`app/` code, infrastructure, configuration, and documentation).  
Objective: Capture actionable refactor tasks for next Copilot/AI sessions; align with architecture principles in `copilot-guidelines.md` and `.claude` docs.

---
## Summary
Status: Foundational scaffold present. Multiple critical issues block production readiness: session management, global state, missing error handling, lack of tests, unpinned dependencies, deprecated startup lifecycle, absence of logging and health checks.

---
## Critical Issues (Must Address First)
1. Session Management Anti-Pattern
   - Repositories open/close `SessionLocal()` inside each method (`db.py`).
   - Risks: resource leaks, impossible test injection, inefficient connection churn.
   - Fix: Introduce `get_db()` dependency; pass `Session` via DI; remove manual calls.

2. Global State in Routers
   - `sets_router.py`, `inventory_router.py` instantiate repositories & service at module load.
   - Blocks test isolation/mocking; couples API layer tightly to infra.
   - Fix: Provide factory dependencies (`get_sets_repo`, `get_inventory_service`, etc.).

3. Missing Domain Exceptions & Error Mapping
   - All failures currently become generic 500 responses; raw exception text leaked.
   - Fix: Add `app/core/exceptions.py`; catch & map to HTTP status codes (404, 400, 502, 500).

4. No Validation on Inputs
   - `CreateSetRequest` lacks regex/format constraints; inventory updates allow arbitrary values.
   - Fix: Add Pydantic validators (set number pattern, qty > 0, enforce enum usage).

5. No Tests
   - No `tests/` directory; behavior unverified. Refactoring is risky.
   - Fix: Scaffold unit (service), integration (repositories), and API tests; adopt fixtures.

6. Unpinned Dependencies
   - `requirements.txt` lists packages without versions; reproducibility risk.
   - Fix: Pin versions; add test/dev dependencies (pytest, pytest-asyncio).

7. Deprecated Startup Event
   - Uses `@app.on_event("startup")`; FastAPI recommends lifespan context.
   - Fix: Implement `lifespan` async contextmanager in `main.py`.

8. No Logging Strategy
   - Absence of logging prevents operational diagnostics.
   - Fix: Central logging config module; structured logs for errors & lifecycle.

9. Missing Health Endpoint
   - No `/health` route; deployment & monitoring hindered.
   - Fix: Add simple DB connectivity check endpoint.

10. Performance / Indexing
    - No indexes defined; queries may degrade with scale.
    - Fix: Add indexes for `set_no`, `(part_no, color_id)`, `state`.

---
## High Impact Improvements (After Critical)
1. Bricklink Client Productionization
   - Real OAuth 1.0a, retries, rate limiting, caching.
2. Structured Logging & Request Context
   - JSON format in prod; correlation IDs.
3. Async Considerations
   - Current sync DB usage inside async endpoints may block event loop; evaluate need for async SQLAlchemy or thread offloading.
4. Configuration Management
   - Introduce `Settings` via `pydantic-settings`; centralize env loading.

---
## Security Findings
| Area | Issue | Recommended Action |
|------|-------|--------------------|
| Secrets | No settings module / env management | Add `.env.example`; never commit real `.env` |
| Error Leakage | Raw exception messages returned | Map domain exceptions; generic 500 message |
| Input Validation | Missing field constraints | Regex for set numbers; qty validation |
| Auth | None implemented | For public exposure, add auth or at least rate limit |
| Rate Limiting | Absent | Integrate middleware (e.g., `slowapi`) when exposed externally |
| Logging | Missing | Add structured logging w/ sanitization |

---
## Refactor Sequence Plan (Incremental Commits)
1. Session & DI foundation (repositories + get_db).
2. Exceptions module + router error mapping.
3. Request model validation improvements.
4. Lifespan context replacement; remove deprecated startup event.
5. Logging configuration integration.
6. Health endpoint implementation.
7. Dependency pinning & requirements update.
8. DB indexing additions.
9. Test scaffolding & initial coverage (service + API).
10. Optional: Config module & prepare Bricklink client enhancements.

Each step followed by: add/adjust tests → run pytest → ensure green.

---
## Initial Test Coverage Targets
- Service layer (`InventoryService`): 100% of add_set logic (success path, invalid set number, Bricklink failure).
- Repositories: add/list/update core functions.
- API: set creation endpoint + inventory listing & update.
- Goal: ≥ 80% overall after foundational refactor.

---
## Data Integrity Improvements
| Current | Issue | Improvement |
|---------|-------|------------|
| Raw dict inventory rows | No schema enforcement | Introduce response models | 
| State stored as string | Risk of mismatched values | Use Enum consistently & convert on persistence |
| No qty constraint | Negative or large values possible | Validate `qty > 0` & sensible upper bound |

---
## Risk Assessment
- Highest Risk: Continuing feature development without DI & tests will compound technical debt.
- Medium Risk: Sync DB in async context may cause latency under load; acceptable short-term for low concurrency (Pi/local usage).
- Low Risk: Absence of migrations until schema evolves.

---
## Immediate Action Items (Next Session Startup Checklist)
1. Implement DI & session changes.
2. Add exceptions & error translation.
3. Pin dependencies.
4. Scaffold tests early—ensure failing tests exist before fixes (where logical).

---
## Tracking
Refer to `TODO.md` for granular task checkboxes. Update completion percentages after each commit.

---
Last Updated: 2025-11-21
