
from pydantic import BaseModel


class LegoSet(BaseModel):
    set_no: str
    name: str
    assembled: bool = False


class Part(BaseModel):
    part_no: str
    color_id: int
    name: str


class InventoryItem(BaseModel):
    set_no: str
    part_no: str
    color_id: int
    qty: int
    state: str
