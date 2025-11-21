import pytest
from app.core.services import InventoryService
from app.core.exceptions import SetNotFoundError
from app.infrastructure.db import SqliteSetsRepository, SqliteInventoryRepository
from app.core.states import PieceState

@pytest.mark.asyncio
async def test_add_set_success(db_session, mock_bricklink_client):
    sets_repo = SqliteSetsRepository(db_session)
    inv_repo = SqliteInventoryRepository(db_session)
    service = InventoryService(inv_repo, sets_repo, mock_bricklink_client)

    lego_set = await service.add_set("1234", assembled=False)
    assert lego_set.set_no == "1234"
    assert lego_set.assembled is False

    items = inv_repo.list()
    assert len(items) == 2
    assert all(i["state"] == PieceState.OWNED_FREE.value for i in items)

@pytest.mark.asyncio
async def test_add_set_not_found(db_session, mock_bricklink_client):
    sets_repo = SqliteSetsRepository(db_session)
    inv_repo = SqliteInventoryRepository(db_session)
    service = InventoryService(inv_repo, sets_repo, mock_bricklink_client)

    with pytest.raises(SetNotFoundError):
        await service.add_set("BAD", assembled=False)
