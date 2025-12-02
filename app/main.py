import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from app.api import inventory_router, sets_router
from app.infrastructure.db import get_db, init_db

logger = logging.getLogger("lego")

health_router = APIRouter()


@health_router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        # Simple connectivity check
        next(db.execute("SELECT 1"))  # type: ignore
        return {"status": "ok"}
    except Exception:
        return {"status": "error"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application - initializing database")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app = FastAPI(title="Lego Inventory Service", lifespan=lifespan)
    app.include_router(sets_router.router, prefix="/sets", tags=["sets"])
    app.include_router(inventory_router.router, prefix="/inventory", tags=["inventory"])
    app.include_router(health_router, tags=["health"])
    app.include_router(health_router, tags=["health"])
    return app


app = create_app()
