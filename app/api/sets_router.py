"""
API router for LEGO sets management.

Provides endpoints for adding sets and querying set information.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
import os
import re
import logging

from app.core.services import InventoryService
from app.core.models import LegoSet
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
logger = logging.getLogger(__name__)


class CreateSetRequest(BaseModel):
    """Request model for creating a new set."""
    set_no: str
    assembled: bool = False

    @field_validator('set_no')
    @classmethod
    def validate_set_no(cls, v: str) -> str:
        """
        Validate set number format.

        Set numbers should be alphanumeric with optional hyphens.
        Examples: 75192, 10255-1, 21042
        """
        if not v:
            raise ValueError("Set number cannot be empty")

        # Allow alphanumeric and hyphens only (prevents injection attacks)
        if not re.match(r'^[a-zA-Z0-9\-]+$', v):
            raise ValueError(
                "Set number must contain only letters, numbers, and hyphens"
            )

        # Reasonable length limit
        if len(v) > 20:
            raise ValueError("Set number is too long")

        return v.strip()


class SetResponse(BaseModel):
    """Response model for set operations."""
    ok: bool
    set: LegoSet
    parts_count: int | None = None

    class Config:
        # Allow Pydantic models as fields
        from_attributes = True


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
            set=lego_set,
            parts_count=None,  # Could be added if we track it
        )
    except CatalogNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Set {req.set_no} not found in catalog"
        )
    except CatalogAuthError:
        # Don't expose auth details to client
        logger.error(f"Bricklink authentication failed for set {req.set_no}")
        raise HTTPException(
            status_code=502,
            detail="Catalog service authentication failed. Please contact administrator.",
        )
    except CatalogRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
        )
    except CatalogAPIError as e:
        # Log full error but return generic message
        logger.error(f"Catalog API error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Catalog service temporarily unavailable",
        )
    except Exception as e:
        # Log full error for debugging but don't expose to client
        logger.exception(f"Unexpected error adding set {req.set_no}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please contact support."
        )
