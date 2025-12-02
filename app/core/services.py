"""
Business logic for LEGO inventory management.

The InventoryService orchestrates operations across repositories and
external catalog services (Bricklink, Rebrickable, etc.).
"""


from app.core.exceptions import BricklinkAPIError, SetNotFoundError
from app.core.models import LegoSet, Part
from app.core.states import PieceState


class InventoryService:
    def __init__(
        self,
        inventory_repo,
        sets_repo,
        bricklink_client,
    ) -> None:
        self.inventory_repo = inventory_repo  # SqliteInventoryRepository
        self.sets_repo = sets_repo  # SqliteSetsRepository
        self.bricklink_client = bricklink_client  # BricklinkClient

    async def add_set(self, set_no: str, assembled: bool = False) -> LegoSet:
        try:
            set_meta = await self.bricklink_client.fetch_set_metadata(set_no)
        except Exception as e:  # refine with real client errors later
            raise BricklinkAPIError(f"Failed to fetch set metadata: {e}") from e

        if not set_meta or not set_meta.get("name"):
            raise SetNotFoundError(f"Set '{set_no}' not found")

        try:
            parts = await self.bricklink_client.fetch_set_inventory(set_no)
        except Exception as e:
            raise BricklinkAPIError(f"Failed to fetch inventory: {e}") from e

        lego_set = LegoSet(
            set_no=set_no, name=set_meta.get("name", ""), assembled=assembled
        )
        self.sets_repo.add(lego_set)
        state = PieceState.OWNED_LOCKED if assembled else PieceState.OWNED_FREE
        for p in parts:
            part = Part(
                part_no=p["part_no"],
                color_id=p["color_id"],
                name=p.get("name", ""),
            )
            self.inventory_repo.add_part(
                lego_set.set_no, part, qty=p.get("qty", 1), state=state
            )
        return lego_set
