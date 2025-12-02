import asyncio
from typing import Any

# Minimal stub for Bricklink client. Replace with real OAuth calls.


class BricklinkClient:
    async def fetch_set_metadata(self, set_no: str) -> dict[str, Any] | None:
        await asyncio.sleep(0.01)
        return {"set_no": set_no, "name": f"Set {set_no}"}

    async def fetch_set_inventory(self, set_no: str) -> list[dict[str, Any]]:
        await asyncio.sleep(0.01)
        return [
            {"part_no": "3001", "color_id": 1, "qty": 4, "name": "Brick 2 x 4"},
            {"part_no": "3020", "color_id": 1, "qty": 2, "name": "Plate 2 x 4"},
        ]
