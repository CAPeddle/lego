from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.infrastructure.db import SqliteInventoryRepository, get_db
from app.core.states import PieceState
from app.api.schemas import (
    InventoryItemResponse,
    UpdateInventoryResponse,
    InventoryListResponse,
)

router = APIRouter()
def get_inventory_repo(db: Session = Depends(get_db)) -> SqliteInventoryRepository:
    return SqliteInventoryRepository(db)

class UpdateStateRequest(BaseModel):
    part_no: str = Field(..., pattern=r"^[0-9A-Za-z-]{2,20}$")
    color_id: int = Field(..., ge=0, le=9999)
    qty: int = Field(..., gt=0, le=10000)
    state: PieceState

@router.get("/", response_model=InventoryListResponse)
async def list_inventory(
    state: PieceState = Query(None),
    repo: SqliteInventoryRepository = Depends(get_inventory_repo),
):
    rows = repo.list(state=state)
    items = [InventoryItemResponse(**r) for r in rows]
    return {"items": items, "count": len(items)}

@router.patch("/", response_model=UpdateInventoryResponse)
async def update_item(
    req: UpdateStateRequest,
    repo: SqliteInventoryRepository = Depends(get_inventory_repo),
):
    updated = repo.update_item(req.part_no, req.color_id, req.qty, req.state)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}
