from fastapi import FastAPI, status
from datetime import datetime
from app.api import sets_router, inventory_router
from app.infrastructure.db import init_db, get_engine, Base

def create_app() -> FastAPI:
    app = FastAPI(title="Lego Inventory Service")

    app.include_router(sets_router.router, prefix="/sets", tags=["sets"])
    app.include_router(inventory_router.router, prefix="/inventory", tags=["inventory"])

    @app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health_check():
        """
        Health check endpoint for monitoring.

        Returns service status and timestamp.
        Can be extended to check database and external service connectivity.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "lego-inventory"
        }

    @app.on_event("startup")
    async def startup():
        init_db()

    return app

app = create_app()
