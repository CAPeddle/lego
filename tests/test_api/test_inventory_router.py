import pytest
from fastapi.testclient import TestClient
from app.core.states import PieceState

@pytest.mark.asyncio
async def test_list_inventory_initial(client: TestClient):
    # Initially empty inventory
    resp = client.get("/inventory/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []

@pytest.mark.asyncio
async def test_add_set_and_list_inventory(client: TestClient):
    # Add a set which populates inventory
    create = client.post("/sets/", json={"set_no": "8888", "assembled": False})
    assert create.status_code == 200
    inv = client.get("/inventory/")
    assert inv.status_code == 200
    data = inv.json()
    assert data["count"] == 2
    states = {item["state"] for item in data["items"]}
    assert states == {PieceState.OWNED_FREE}

@pytest.mark.asyncio
async def test_update_inventory_item(client: TestClient):
    # Ensure a set is present
    client.post("/sets/", json={"set_no": "12345", "assembled": True})
    listing = client.get("/inventory/")
    item = listing.json()["items"][0]
    update = client.patch(
        "/inventory/",
        json={
            "part_no": item["part_no"],
            "color_id": item["color_id"],
            "qty": item["qty"] + 1,
            "state": "OWNED_LOCKED",
        },
    )
    assert update.status_code == 200
    # Verify change
    after = client.get("/inventory/").json()
    updated = [i for i in after["items"] if i["part_no"] == item["part_no"]][0]
    assert updated["qty"] == item["qty"] + 1
    assert updated["state"] == "OWNED_LOCKED"
