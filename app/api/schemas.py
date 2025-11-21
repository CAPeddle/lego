from pydantic import BaseModel
from app.core.states import PieceState


class LegoSetResponse(BaseModel):
    set_no: str
    name: str
    assembled: bool


class CreateSetResponse(BaseModel):
    ok: bool
    set: LegoSetResponse


class InventoryItemResponse(BaseModel):
    set_no: str
    part_no: str
    color_id: int
    qty: int
    state: PieceState


class InventoryListResponse(BaseModel):
    items: list[InventoryItemResponse]
    count: int


class UpdateInventoryResponse(BaseModel):
    ok: bool