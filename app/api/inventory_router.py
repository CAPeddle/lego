from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.infrastructure.db import SqliteInventoryRepository
from app.core.states import PieceState
from pydantic import BaseModel

router = APIRouter()
repo = SqliteInventoryRepository()

class UpdateStateRequest(BaseModel):
    part_no: str
    color_id: int
    qty: int
    state: PieceState

@router.get("/", response_model=List[dict])
async def list_inventory(state: PieceState = Query(None)):
    items = repo.list(state=state)
    return items

@router.patch("/", response_model=dict)
async def update_item(req: UpdateStateRequest):
    updated = repo.update_item(req.part_no, req.color_id, req.qty, req.state)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}
