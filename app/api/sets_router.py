from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.services import InventoryService
from app.infrastructure.bricklink_client import BricklinkClient
from app.infrastructure.db import SqliteSetsRepository, SqliteInventoryRepository

router = APIRouter()

class CreateSetRequest(BaseModel):
    set_no: str
    assembled: bool = False

# repositories and client instances (simple DI)
sets_repo = SqliteSetsRepository()
inventory_repo = SqliteInventoryRepository()
bricklink_client = BricklinkClient()
service = InventoryService(inventory_repo, sets_repo, bricklink_client)

@router.post("/")
async def add_set(req: CreateSetRequest):
    try:
        lego_set = await service.add_set(req.set_no, assembled=req.assembled)
        return {"ok": True, "set": lego_set.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
