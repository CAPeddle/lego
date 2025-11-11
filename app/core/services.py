from app.core.models import LegoSet, Part
from app.core.states import PieceState
from typing import List

class InventoryService:
    def __init__(self, inventory_repo, sets_repo, bricklink_client):
        self.inventory_repo = inventory_repo
        self.sets_repo = sets_repo
        self.bricklink_client = bricklink_client

    async def add_set(self, set_no: str, assembled: bool = False) -> LegoSet:
        # Fetch set metadata and parts from bricklink client
        set_meta = await self.bricklink_client.fetch_set_metadata(set_no)
        parts = await self.bricklink_client.fetch_set_inventory(set_no)

        lego_set = LegoSet(set_no=set_no, name=set_meta.get("name",""), assembled=assembled)
        # store set
        self.sets_repo.add(lego_set)
        state = PieceState.OWNED_LOCKED if assembled else PieceState.OWNED_FREE
        # add parts to inventory
        inventory_items = []
        for p in parts:
            part = Part(part_no=p["part_no"], color_id=p["color_id"], name=p.get("name",""))
            self.inventory_repo.add_part(lego_set.set_no, part, qty=p.get("qty",1), state=state)
            inventory_items.append(p)
        return lego_set
