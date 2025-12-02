"""
Bricklink implementation of the catalog service interface.

Uses OAuth 1.0a client for authentication and implements the
CatalogServiceInterface for interacting with Bricklink API v3.

API Documentation: https://www.bricklink.com/v3/api.page
"""

import logging

import requests
from cachetools import TTLCache

from app.core.catalog_interface import (
    CatalogServiceInterface,
    InventoryPart,
    SetMetadata,
    SetSearchResult,
)
from app.core.exceptions import (
    CatalogAPIError,
    CatalogAuthError,
    CatalogNotFoundError,
    CatalogRateLimitError,
    CatalogTimeoutError,
)
from app.infrastructure.oauth_client import OAuthHTTPClient

logger = logging.getLogger(__name__)


class BricklinkCatalogService(CatalogServiceInterface):
    """
    Bricklink-specific implementation of the catalog service.

    Uses injected OAuth client for authentication.
    Implements caching to reduce API calls and respect rate limits.
    """

    BASE_URL = "https://api.bricklink.com/api/store/v1"

    def __init__(
        self,
        oauth_client: OAuthHTTPClient,
        cache_ttl: int = 86400,  # 24 hours
        max_cache_size: int = 100,  # Tuned for Raspberry Pi memory constraints
    ):
        """
        Initialize Bricklink catalog service.

        Args:
            oauth_client: Configured OAuth HTTP client
            cache_ttl: Cache time-to-live in seconds (default 24h)
            max_cache_size: Maximum number of items in each cache (default 100)
        """
        self.oauth_client = oauth_client
        self.cache_ttl = cache_ttl

        # Cache for set metadata (keyed by set_no)
        # Reduced size for Raspberry Pi deployment
        self.metadata_cache = TTLCache(maxsize=max_cache_size, ttl=cache_ttl)

        # Cache for set inventory (keyed by set_no)
        # Inventory data is larger, so use smaller cache
        self.inventory_cache = TTLCache(
            maxsize=max_cache_size // 2, ttl=cache_ttl * 7  # 7 days
        )

    async def search_sets(self, query: str, limit: int = 20) -> list[SetSearchResult]:
        """
        Search for sets in Bricklink catalog.

        Uses Bricklink catalog search API.
        Note: Bricklink search is limited - may need to search by set number prefix.

        Args:
            query: Search term (set number or name)
            limit: Maximum results

        Returns:
            List of matching sets

        Raises:
            CatalogAPIError: If API request fails
            CatalogAuthError: If authentication fails
        """
        try:
            # Bricklink API endpoint for catalog item search
            url = f"{self.BASE_URL}/items/SET"

            # If query looks like a set number, search by number
            # Otherwise, this is limited - Bricklink doesn't have great text search
            params = {
                "type": "SET",
            }

            logger.info(f"Searching Bricklink for: {query}")

            # Note: Bricklink's search API is limited
            # For now, we'll try to get the specific set if it looks like a set number
            # A real implementation might need to use /items/SET endpoint differently
            # or implement custom search logic

            response = await self.oauth_client.get(url, params=params)

            results = []
            for item in response.get("data", [])[:limit]:
                results.append(
                    SetSearchResult(
                        set_no=item.get("no", ""),
                        name=item.get("name", ""),
                        year=item.get("year_released"),
                        theme=item.get("category_name"),
                        num_parts=None,  # Not in search results
                        image_url=item.get("thumbnail_url"),
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Bricklink search failed: {e}")
            raise self._convert_exception(e)

    async def fetch_set_metadata(self, set_no: str) -> SetMetadata:
        """
        Fetch detailed metadata for a specific set.

        Uses Bricklink catalog item endpoint.
        Results are cached for 24 hours.

        Args:
            set_no: LEGO set number (e.g., "75192")

        Returns:
            Detailed set metadata

        Raises:
            CatalogNotFoundError: If set doesn't exist
            CatalogAPIError: If API request fails
        """
        # Check cache first
        if set_no in self.metadata_cache:
            logger.debug(f"Cache hit for set metadata: {set_no}")
            return self.metadata_cache[set_no]

        try:
            # GET /items/{type}/{no}
            url = f"{self.BASE_URL}/items/SET/{set_no}"

            logger.info(f"Fetching metadata for set: {set_no}")
            response = await self.oauth_client.get(url)

            data = response.get("data", {})

            metadata = SetMetadata(
                set_no=data.get("no", set_no),
                name=data.get("name", ""),
                year=data.get("year_released"),
                theme=data.get("category_name"),
                num_parts=None,  # Need to get from subsets endpoint
                image_url=data.get("image_url"),
                weight=data.get("weight"),
                dimensions=data.get("dim"),
            )

            # Cache the result
            self.metadata_cache[set_no] = metadata

            return metadata

        except Exception as e:
            logger.error(f"Failed to fetch metadata for {set_no}: {e}")
            raise self._convert_exception(e)

    async def fetch_set_inventory(self, set_no: str) -> list[InventoryPart]:
        """
        Fetch the complete parts inventory for a set.

        Uses Bricklink subsets endpoint which returns all parts.
        Results are cached for 7 days (inventories rarely change).

        Args:
            set_no: LEGO set number (e.g., "75192")

        Returns:
            List of all parts with quantities

        Raises:
            CatalogNotFoundError: If set doesn't exist
            CatalogAPIError: If API request fails
        """
        # Check cache first
        if set_no in self.inventory_cache:
            logger.debug(f"Cache hit for set inventory: {set_no}")
            return self.inventory_cache[set_no]

        try:
            # GET /items/{type}/{no}/subsets
            url = f"{self.BASE_URL}/items/SET/{set_no}/subsets"

            logger.info(f"Fetching inventory for set: {set_no}")

            # Request includes parts breakdown
            params = {
                "break_minifigs": "true",  # Break down minifigures into parts
                "break_subsets": "true",  # Break down subsets
            }

            response = await self.oauth_client.get(url, params=params)

            # Parse parts from response
            parts = []
            for entry in response.get("data", []):
                for item in entry.get("entries", []):
                    # Only include actual parts (type 'PART')
                    if item.get("item", {}).get("type") == "PART":
                        parts.append(
                            InventoryPart(
                                part_no=item.get("item", {}).get("no", ""),
                                color_id=item.get("color_id", 0),
                                qty=item.get("quantity", 1),
                                name=item.get("item", {}).get("name", ""),
                                is_spare=item.get("is_alternate", False),
                                is_counterpart=item.get("is_counterpart", False),
                            )
                        )

            logger.info(f"Retrieved {len(parts)} parts for set {set_no}")

            # Cache the result
            self.inventory_cache[set_no] = parts

            return parts

        except Exception as e:
            logger.error(f"Failed to fetch inventory for {set_no}: {e}")
            raise self._convert_exception(e)

    async def health_check(self) -> bool:
        """
        Check if Bricklink API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try to access a simple endpoint
            url = f"{self.BASE_URL}/items/SET/75192"  # Known set
            await self.oauth_client.get(url)
            return True
        except Exception as e:
            logger.warning(f"Bricklink health check failed: {e}")
            return False

    def _convert_exception(self, exc: Exception) -> Exception:
        """
        Convert generic exceptions to catalog-specific exceptions.

        Args:
            exc: Original exception

        Returns:
            Catalog-specific exception
        """
        if isinstance(exc, requests.exceptions.HTTPError):
            status_code = exc.response.status_code

            if status_code == 401 or status_code == 403:
                return CatalogAuthError(f"Bricklink authentication failed: {exc}")
            elif status_code == 404:
                return CatalogNotFoundError(
                    f"Set not found in Bricklink catalog: {exc}"
                )
            elif status_code == 429:
                return CatalogRateLimitError(f"Bricklink rate limit exceeded: {exc}")
            else:
                return CatalogAPIError(
                    f"Bricklink API error (status {status_code}): {exc}"
                )

        elif isinstance(exc, requests.exceptions.Timeout):
            return CatalogTimeoutError(f"Bricklink request timed out: {exc}")

        elif isinstance(exc, (requests.exceptions.ConnectionError, ConnectionError)):
            return CatalogAPIError(f"Failed to connect to Bricklink: {exc}")

        else:
            return CatalogAPIError(f"Bricklink API error: {exc}")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.metadata_cache.clear()
        self.inventory_cache.clear()
        logger.info("Bricklink cache cleared")
