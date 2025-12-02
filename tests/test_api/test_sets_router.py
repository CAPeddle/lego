import pytest


@pytest.mark.asyncio
async def test_create_set_endpoint(client):
    response = client.post("/sets/", json={"set_no": "7777", "assembled": False})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["set"]["set_no"] == "7777"


@pytest.mark.asyncio
async def test_create_set_not_found(client):
    response = client.post("/sets/", json={"set_no": "BAD", "assembled": False})
    assert response.status_code == 404
