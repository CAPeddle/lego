"""
Pytest configuration and shared fixtures.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.infrastructure.oauth_client import OAuthConfig


@pytest.fixture
def oauth_config():
    """Provide a valid OAuth configuration for testing."""
    return OAuthConfig(
        consumer_key="test_consumer_key",
        consumer_secret="test_consumer_secret",
        resource_owner_key="test_token",
        resource_owner_secret="test_token_secret",
    )


@pytest.fixture
def mock_oauth_response():
    """Provide a mock OAuth API response."""
    def _create_response(data, status_code=200):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data
        response.raise_for_status = Mock()
        if status_code >= 400:
            import requests
            response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
        return response
    return _create_response
