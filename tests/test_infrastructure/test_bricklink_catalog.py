"""
Unit tests for Bricklink catalog service implementation.

Tests the Bricklink-specific catalog service that uses OAuth client.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.catalog_interface import InventoryPart, SetMetadata, SetSearchResult
from app.core.exceptions import (
    CatalogAPIError,
    CatalogAuthError,
    CatalogNotFoundError,
    CatalogRateLimitError,
    CatalogTimeoutError,
)
from app.infrastructure.bricklink_catalog import BricklinkCatalogService
from app.infrastructure.oauth_client import OAuthHTTPClient


@pytest.fixture
def mock_oauth_client():
    """Provide a mocked OAuth HTTP client."""
    client = Mock(spec=OAuthHTTPClient)
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client


@pytest.fixture
def bricklink_service(mock_oauth_client):
    """Provide a Bricklink catalog service with mocked OAuth client."""
    return BricklinkCatalogService(
        oauth_client=mock_oauth_client,
        cache_ttl=60,  # Short TTL for testing
    )


class TestBricklinkCatalogService:
    """Test Bricklink catalog service implementation."""

    def test_initialization(self, mock_oauth_client):
        """Test that service initializes correctly."""
        service = BricklinkCatalogService(mock_oauth_client, cache_ttl=3600)
        assert service.oauth_client == mock_oauth_client
        assert service.cache_ttl == 3600
        assert len(service.metadata_cache) == 0
        assert len(service.inventory_cache) == 0

    @pytest.mark.asyncio
    async def test_fetch_set_metadata_success(
        self, bricklink_service, mock_oauth_client
    ):
        """Test successful metadata fetch."""
        mock_response = {
            "data": {
                "no": "75192",
                "name": "Millennium Falcon",
                "year_released": 2017,
                "category_name": "Star Wars",
                "image_url": "https://example.com/image.jpg",
                "weight": 1000.0,
                "dim": {"length": 10, "width": 20, "height": 30},
            }
        }
        mock_oauth_client.get.return_value = mock_response

        result = await bricklink_service.fetch_set_metadata("75192")

        assert isinstance(result, SetMetadata)
        assert result.set_no == "75192"
        assert result.name == "Millennium Falcon"
        assert result.year == 2017
        assert result.theme == "Star Wars"
        assert result.image_url == "https://example.com/image.jpg"
        assert result.weight == 1000.0

        # Verify correct API endpoint called
        mock_oauth_client.get.assert_called_once()
        call_args = mock_oauth_client.get.call_args
        assert "items/SET/75192" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_fetch_set_metadata_cached(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that metadata is cached on second request."""
        mock_response = {
            "data": {
                "no": "75192",
                "name": "Millennium Falcon",
                "year_released": 2017,
                "category_name": "Star Wars",
            }
        }
        mock_oauth_client.get.return_value = mock_response

        # First call - should hit API
        result1 = await bricklink_service.fetch_set_metadata("75192")
        assert mock_oauth_client.get.call_count == 1

        # Second call - should use cache
        result2 = await bricklink_service.fetch_set_metadata("75192")
        assert mock_oauth_client.get.call_count == 1  # Still 1, not 2

        assert result1.set_no == result2.set_no
        assert result1.name == result2.name

    @pytest.mark.asyncio
    async def test_fetch_set_inventory_success(
        self, bricklink_service, mock_oauth_client
    ):
        """Test successful inventory fetch."""
        mock_response = {
            "data": [
                {
                    "entries": [
                        {
                            "item": {
                                "type": "PART",
                                "no": "3001",
                                "name": "Brick 2 x 4",
                            },
                            "color_id": 1,
                            "quantity": 10,
                            "is_alternate": False,
                            "is_counterpart": False,
                        },
                        {
                            "item": {
                                "type": "PART",
                                "no": "3020",
                                "name": "Plate 2 x 4",
                            },
                            "color_id": 5,
                            "quantity": 5,
                            "is_alternate": True,
                            "is_counterpart": False,
                        },
                    ]
                }
            ]
        }
        mock_oauth_client.get.return_value = mock_response

        result = await bricklink_service.fetch_set_inventory("75192")

        assert len(result) == 2
        assert all(isinstance(part, InventoryPart) for part in result)

        # Check first part
        assert result[0].part_no == "3001"
        assert result[0].name == "Brick 2 x 4"
        assert result[0].color_id == 1
        assert result[0].qty == 10
        assert result[0].is_spare is False

        # Check second part
        assert result[1].part_no == "3020"
        assert result[1].is_spare is True

        # Verify API call
        mock_oauth_client.get.assert_called_once()
        call_args = mock_oauth_client.get.call_args
        assert "items/SET/75192/subsets" in call_args[0][0]
        assert call_args[1]["params"]["break_minifigs"] == "true"

    @pytest.mark.asyncio
    async def test_fetch_set_inventory_cached(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that inventory is cached."""
        mock_response = {
            "data": [
                {
                    "entries": [
                        {
                            "item": {"type": "PART", "no": "3001", "name": "Brick"},
                            "color_id": 1,
                            "quantity": 5,
                        }
                    ]
                }
            ]
        }
        mock_oauth_client.get.return_value = mock_response

        # First call
        result1 = await bricklink_service.fetch_set_inventory("75192")
        assert mock_oauth_client.get.call_count == 1

        # Second call - should use cache
        result2 = await bricklink_service.fetch_set_inventory("75192")
        assert mock_oauth_client.get.call_count == 1  # Not incremented

        assert len(result1) == len(result2)

    @pytest.mark.asyncio
    async def test_fetch_set_inventory_filters_non_parts(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that non-PART items are filtered out."""
        mock_response = {
            "data": [
                {
                    "entries": [
                        {
                            "item": {"type": "PART", "no": "3001", "name": "Brick"},
                            "color_id": 1,
                            "quantity": 5,
                        },
                        {
                            "item": {"type": "MINIFIG", "no": "sw001", "name": "Luke"},
                            "color_id": 0,
                            "quantity": 1,
                        },
                        {
                            "item": {"type": "SET", "no": "75192", "name": "Set"},
                            "color_id": 0,
                            "quantity": 1,
                        },
                    ]
                }
            ]
        }
        mock_oauth_client.get.return_value = mock_response

        result = await bricklink_service.fetch_set_inventory("75192")

        # Should only include the PART type
        assert len(result) == 1
        assert result[0].part_no == "3001"

    @pytest.mark.asyncio
    async def test_fetch_set_inventory_error(
        self, bricklink_service, mock_oauth_client
    ):
        """Test inventory fetch handles errors correctly."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogNotFoundError):
            await bricklink_service.fetch_set_inventory("nonexistent")

    @pytest.mark.asyncio
    async def test_health_check_success(self, bricklink_service, mock_oauth_client):
        """Test health check when API is accessible."""
        mock_oauth_client.get.return_value = {"data": {}}

        result = await bricklink_service.health_check()

        assert result is True
        mock_oauth_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, bricklink_service, mock_oauth_client):
        """Test health check when API is not accessible."""
        mock_oauth_client.get.side_effect = Exception("Connection failed")

        result = await bricklink_service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_convert_exception_404(self, bricklink_service, mock_oauth_client):
        """Test that 404 errors are converted to CatalogNotFoundError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogNotFoundError):
            await bricklink_service.fetch_set_metadata("99999")

    @pytest.mark.asyncio
    async def test_convert_exception_401(self, bricklink_service, mock_oauth_client):
        """Test that 401 errors are converted to CatalogAuthError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 401
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogAuthError):
            await bricklink_service.fetch_set_metadata("75192")

    @pytest.mark.asyncio
    async def test_convert_exception_429(self, bricklink_service, mock_oauth_client):
        """Test that 429 errors are converted to CatalogRateLimitError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 429
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogRateLimitError):
            await bricklink_service.fetch_set_metadata("75192")

    @pytest.mark.asyncio
    async def test_convert_exception_timeout(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that timeout errors are converted to CatalogTimeoutError."""
        import requests

        timeout_error = requests.exceptions.Timeout()
        mock_oauth_client.get.side_effect = timeout_error

        with pytest.raises(CatalogTimeoutError):
            await bricklink_service.fetch_set_metadata("75192")

    @pytest.mark.asyncio
    async def test_convert_exception_connection(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that connection errors are converted to CatalogAPIError."""
        import requests

        connection_error = requests.exceptions.ConnectionError()
        mock_oauth_client.get.side_effect = connection_error

        with pytest.raises(CatalogAPIError):
            await bricklink_service.fetch_set_metadata("75192")

    def test_clear_cache(self, bricklink_service):
        """Test that clear_cache() clears both caches."""
        # Add some data to caches
        bricklink_service.metadata_cache["75192"] = SetMetadata(
            set_no="75192",
            name="Test",
        )
        bricklink_service.inventory_cache["75192"] = []

        assert len(bricklink_service.metadata_cache) == 1
        assert len(bricklink_service.inventory_cache) == 1

        bricklink_service.clear_cache()

        assert len(bricklink_service.metadata_cache) == 0
        assert len(bricklink_service.inventory_cache) == 0

    @pytest.mark.asyncio
    async def test_search_sets_success(self, bricklink_service, mock_oauth_client):
        """Test successful set search."""
        mock_response = {
            "data": [
                {
                    "no": "75192",
                    "name": "Millennium Falcon",
                    "year_released": 2017,
                    "category_name": "Star Wars",
                    "thumbnail_url": "https://example.com/thumb.jpg",
                },
                {
                    "no": "10221",
                    "name": "Super Star Destroyer",
                    "year_released": 2011,
                    "category_name": "Star Wars",
                    "thumbnail_url": "https://example.com/thumb2.jpg",
                },
            ]
        }
        mock_oauth_client.get.return_value = mock_response

        results = await bricklink_service.search_sets("Falcon")

        assert len(results) == 2
        assert all(isinstance(r, SetSearchResult) for r in results)
        assert results[0].set_no == "75192"
        assert results[0].name == "Millennium Falcon"
        assert results[0].year == 2017
        assert results[0].theme == "Star Wars"
        assert results[0].image_url == "https://example.com/thumb.jpg"

        # Verify API call
        mock_oauth_client.get.assert_called_once()
        call_args = mock_oauth_client.get.call_args
        assert "items/SET" in call_args[0][0]
        assert call_args[1]["params"]["type"] == "SET"

    @pytest.mark.asyncio
    async def test_search_sets_with_limit(self, bricklink_service, mock_oauth_client):
        """Test set search respects limit parameter."""
        # Return more items than the limit
        mock_response = {
            "data": [
                {"no": f"set{i}", "name": f"Set {i}", "year_released": 2020}
                for i in range(50)
            ]
        }
        mock_oauth_client.get.return_value = mock_response

        results = await bricklink_service.search_sets("test", limit=10)

        # Should only return up to the limit
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_search_sets_empty_results(
        self, bricklink_service, mock_oauth_client
    ):
        """Test search with no results."""
        mock_response = {"data": []}
        mock_oauth_client.get.return_value = mock_response

        results = await bricklink_service.search_sets("nonexistent")

        assert len(results) == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_search_sets_error(self, bricklink_service, mock_oauth_client):
        """Test search handles errors correctly."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogAPIError):
            await bricklink_service.search_sets("test")

    @pytest.mark.asyncio
    async def test_convert_exception_403(self, bricklink_service, mock_oauth_client):
        """Test that 403 errors are converted to CatalogAuthError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 403
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogAuthError):
            await bricklink_service.fetch_set_metadata("75192")

    @pytest.mark.asyncio
    async def test_convert_exception_500(self, bricklink_service, mock_oauth_client):
        """Test that 500 errors are converted to CatalogAPIError."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_oauth_client.get.side_effect = http_error

        with pytest.raises(CatalogAPIError) as exc_info:
            await bricklink_service.fetch_set_metadata("75192")

        assert "status 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_convert_exception_generic(
        self, bricklink_service, mock_oauth_client
    ):
        """Test that generic exceptions are converted to CatalogAPIError."""
        mock_oauth_client.get.side_effect = ValueError("Something went wrong")

        with pytest.raises(CatalogAPIError) as exc_info:
            await bricklink_service.fetch_set_metadata("75192")

        assert "Something went wrong" in str(exc_info.value)
