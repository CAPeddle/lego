import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.services import InventoryService
from app.core.exceptions import SetNotFoundError, BricklinkAPIError
from app.api.schemas import CreateSetResponse, LegoSetResponse
from app.infrastructure.bricklink_client import BricklinkClient
from app.infrastructure.db import (
    SqliteSetsRepository,
    SqliteInventoryRepository,
    get_db,
)
from app.api.schemas import CreateSetResponse, LegoSetResponse

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateSetRequest(BaseModel):
    set_no: str = Field(..., pattern=r"^[0-9A-Za-z-]{3,20}$")
    assembled: bool = False

def get_bricklink_client() -> BricklinkClient:
    return BricklinkClient()

def get_sets_repo(db: Session = Depends(get_db)) -> SqliteSetsRepository:
    return SqliteSetsRepository(db)

def get_inventory_repo(db: Session = Depends(get_db)) -> SqliteInventoryRepository:
    return SqliteInventoryRepository(db)

def get_inventory_service(
    sets_repo: SqliteSetsRepository = Depends(get_sets_repo),
    inventory_repo: SqliteInventoryRepository = Depends(get_inventory_repo),
    bricklink_client: BricklinkClient = Depends(get_bricklink_client),
) -> InventoryService:
    return InventoryService(inventory_repo, sets_repo, bricklink_client)

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
    except BricklinkAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        logger.exception("Unexpected error in add_set endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")
