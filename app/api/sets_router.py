"""
API router for LEGO sets management.

Provides endpoints for adding sets and querying set information.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from app.core.services import InventoryService
from app.core.exceptions import (
    CatalogNotFoundError,
    CatalogAuthError,
    CatalogAPIError,
    CatalogRateLimitError,
)
from app.infrastructure.bricklink_catalog import BricklinkCatalogService
from app.infrastructure.oauth_client import OAuthHTTPClient, OAuthConfig
from app.infrastructure.db import SqliteSetsRepository, SqliteInventoryRepository

router = APIRouter()


class CreateSetRequest(BaseModel):
    """Request model for creating a new set."""
    set_no: str
    assembled: bool = False


class SetResponse(BaseModel):
    """Response model for set operations."""
    ok: bool
    set: dict
    parts_count: int | None = None


# Initialize OAuth config from environment
# NOTE: This will be moved to proper dependency injection in TODO #2
oauth_config = OAuthConfig(
    consumer_key=os.getenv("LEGO_BRICKLINK_CONSUMER_KEY", ""),
    consumer_secret=os.getenv("LEGO_BRICKLINK_CONSUMER_SECRET", ""),
    resource_owner_key=os.getenv("LEGO_BRICKLINK_TOKEN", ""),
    resource_owner_secret=os.getenv("LEGO_BRICKLINK_TOKEN_SECRET", ""),
)

# Initialize OAuth client and catalog service
# NOTE: This global state will be refactored to use FastAPI DI in TODO #2
oauth_client = OAuthHTTPClient(oauth_config)
catalog_service = BricklinkCatalogService(oauth_client)

# Repositories
# NOTE: These global instances will be refactored to use DI in TODO #2
sets_repo = SqliteSetsRepository()
inventory_repo = SqliteInventoryRepository()

# Service
service = InventoryService(inventory_repo, sets_repo, catalog_service)


@router.post("/", response_model=SetResponse)
async def add_set(req: CreateSetRequest):
    """
    Add a new LEGO set to the inventory.

    Fetches set metadata and parts list from Bricklink,
    stores the set, and adds all parts to inventory.

    Args:
        req: Set number and assembly status

    Returns:
        Created set with metadata

    Raises:
        404: Set not found in Bricklink catalog
        401/403: Bricklink authentication failed
        429: Bricklink rate limit exceeded
        502: Bricklink API unavailable
        500: Internal server error
    """
    try:
        lego_set = await service.add_set(req.set_no, assembled=req.assembled)
        return SetResponse(
            ok=True,
            set=lego_set.dict(),
            parts_count=None,  # Could be added if we track it
        )
    except CatalogNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Set not found: {str(e)}")
    except CatalogAuthError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Bricklink authentication failed: {str(e)}",
        )
    except CatalogRateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {str(e)}",
        )
    except CatalogAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Bricklink API error: {str(e)}",
        )
    except Exception as e:
        # Log the error in production
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
