import pytest
from unittest.mock import Mock
from typing import Any, Dict, Generator, Callable
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.api import sets_router
from app.infrastructure.db import metadata, get_db
from app.infrastructure.bricklink_client import BricklinkClient
from app.infrastructure.oauth_client import OAuthConfig

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

class MockBricklinkClient(BricklinkClient):
    async def fetch_set_metadata(self, set_no: str):
        if set_no == "BAD":
            return None
        return {"set_no": set_no, "name": f"Test Set {set_no}"}

    async def fetch_set_inventory(self, set_no: str) -> list[Dict[str, Any]]:
        return [
            {"part_no": "3001", "color_id": 1, "qty": 4, "name": "Brick 2 x 4"},
            {"part_no": "3020", "color_id": 1, "qty": 2, "name": "Plate 2 x 4"},
        ]

@pytest.fixture(scope="function")
def mock_bricklink_client():
    return MockBricklinkClient()

@pytest.fixture(scope="function")
def test_app(db_session: Session, mock_bricklink_client: MockBricklinkClient) -> FastAPI:
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Override bricklink client to use mock behavior
    app.dependency_overrides[sets_router.get_bricklink_client] = lambda: mock_bricklink_client
    # inventory & sets repos will still use injected db session
    return app

@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)

@pytest.fixture(scope="function")
def oauth_config():
    return OAuthConfig(
        consumer_key="key",
        consumer_secret="secret",
        resource_owner_key="token",
        resource_owner_secret="token_secret",
    )

@pytest.fixture(scope="function")
def mock_oauth_response() -> Callable[[Dict[str, Any], int], Mock]:
    def _factory(data: Dict[str, Any], status_code: int) -> Mock:
        from requests import exceptions
        response = Mock()
        response.status_code = status_code
        def raise_for_status():
            if status_code >= 400:
                raise exceptions.HTTPError(f"Status {status_code}")
        response.raise_for_status = raise_for_status
        response.json = lambda: data
        return response
    return _factory
