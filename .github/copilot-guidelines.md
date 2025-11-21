# Copilot Session Guidelines for Lego Inventory Service

Purpose: Provide concise, enforceable instructions for AI pair programming sessions (GitHub Copilot / GPT) aligned with project architecture and quality standards. This distills `.claude` folder guidance into actionable rules.

## 1. Core Architecture Constraints
- Layers: API (`app/api`) -> Services & Domain (`app/core`) -> Infrastructure (`app/infrastructure`).
- API routers: no business logic, only request/response + error translation.
- Services: orchestrate repositories + external clients; contain business rules.
- Infrastructure: pure side‑effects (DB, external APIs). No domain decisions.
- Directional dependency: upper layers depend on lower via abstractions (inject instances, never import upward).

## 2. Mandatory Refactors (If Touching Related Code)
1. Replace manual `SessionLocal()` calls in repositories with injected `Session` via FastAPI `Depends(get_db)`. 
2. Remove global repository/service instances from routers; use dependency factories. 
3. Introduce domain exception classes and map them to HTTP status codes in routers. 
4. Add tests before large refactors (service tests first). 
5. Pin dependency versions in `requirements.txt`.

## 3. Dependency Injection Pattern
```python
# db dependency
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# repository dependency
def get_sets_repo(db: Session = Depends(get_db)):
    return SqliteSetsRepository(db)

# service dependency
def get_inventory_service(
    db: Session = Depends(get_db),
    bricklink: BricklinkClient = Depends(get_bricklink_client)
):
    return InventoryService(SqliteInventoryRepository(db), SqliteSetsRepository(db), bricklink)
```
Use this exact pattern in new/modified endpoints.

## 4. Error Handling Standard
- Define domain exceptions in `app/core/exceptions.py` (e.g., `SetNotFoundError`, `BricklinkAPIError`, `InvalidSetNumberError`).
- Routers catch specific domain exceptions -> raise `HTTPException` with precise status codes.
- Log unexpected exceptions, return generic 500 message.

## 5. Data & Validation
- All request bodies: Pydantic models with constraints (e.g., regex for `set_no`, positive qty). 
- Use Enums for state (`PieceState`) in API schemas; never expose raw strings that drift from enum.
- Avoid returning internal DB rows directly; map to response models.

## 6. Testing Priorities
Minimum required before scaling features:
- Service tests for `InventoryService.add_set()` covering success + not found.
- Repository tests (in‑memory SQLite) for add/list/update semantics.
- API endpoint tests with dependency overrides for service.
Use fixtures: `db_session`, `mock_bricklink_client`.

## 7. Security & Operational Essentials
- No hardcoded secrets; use `.env` + `pydantic-settings` for configuration.
- Input validation on all external parameters. 
- Plan for rate limiting middleware if exposed publicly.
- Prepare lifespan context instead of deprecated `@on_event` startup.
- Add indices for frequent queries: `set_no`, `(part_no, color_id)`, `state`.

## 8. Performance (Raspberry Pi Focus)
- Keep worker count modest (2–4). 
- Minimize session churn (use per-request injected session). 
- Consider WAL mode for SQLite if write frequency increases. 
- Avoid N+1 patterns; batch queries when listing inventory.

## 9. Logging & Observability
- Introduce a shared logger per module (`logger = logging.getLogger(__name__)`).
- Log at INFO for lifecycle events, WARNING for recoverable issues, ERROR with stack for unexpected exceptions.
- Add `/health` endpoint (DB connectivity check) before deployment.

## 10. Commit & Branch Conventions
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `perf:`.
- Branch naming: `feature/...`, `fix/...`, `refactor/...`.
- Large refactors: create incremental PRs (session mgmt, then error handling, then tests).

## 11. Copilot Prompting Hints
When requesting code:
- Specify layer ("service layer", "router", "repository").
- State injection needs ("session passed in", "no globals").
- Ask for Pydantic model with explicit validators if input-related.
- Require exception mapping if endpoint returns errors.
- Mention test scaffold needs if generating logic.

Example prompt: 
"Generate a FastAPI router endpoint to add a set using injected `InventoryService`, validating set number format, mapping `SetNotFoundError` to 404, and returning a response model without internal IDs. Include dependency functions."

## 12. Do NOT
- Create global `Sqlite*Repository()` or `InventoryService()` instances. 
- Open sessions inside every repository method. 
- Swallow exceptions silently. 
- Return raw SQLAlchemy rows or unconstrained dicts. 
- Add blocking calls (`time.sleep`) in async contexts. 
- Introduce new dependencies without rationale or pinning.

## 13. Immediate Backlog (High-Value for AI Assistance)
1. Implement DI + session fix. 
2. Add exceptions + router error translation. 
3. Add service + repo tests. 
4. Pin dependencies. 
5. Replace startup event with lifespan. 
6. Introduce validation on request models.

## 14. Quick Commands
```bash
# Dev server
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

# Tests (after adding)
pytest -v --cov=app

# Lint (after adding tools)
ruff check . && ruff format .

# Pin requirements
pip freeze > requirements.txt
```

## 15. Future Enhancements (Not Blocking Now)
- OAuth Bricklink client with retry & caching.
- Async SQLAlchemy migration (optional). 
- Structured JSON logging. 
- Rate limiting & auth for public exposure.

---
Last updated: 2025-11-21
Source: Consolidated from `.claude/instructions.md`, `quick-reference.md`, and `skills/fastapi-review/SKILL.md`.
