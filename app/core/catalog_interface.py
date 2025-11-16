"""
Abstract interface for LEGO parts catalog services.

This defines the contract that any catalog service (Bricklink, Rebrickable, etc.)
must implement. Allows swapping catalog providers without changing business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class SetSearchResult(BaseModel):
    """Result from searching for a set in a catalog."""
    set_no: str
    name: str
    year: Optional[int] = None
    theme: Optional[str] = None
    num_parts: Optional[int] = None
    image_url: Optional[str] = None


class SetMetadata(BaseModel):
    """Detailed metadata about a LEGO set."""
    set_no: str
    name: str
    year: Optional[int] = None
    theme: Optional[str] = None
    num_parts: Optional[int] = None
    image_url: Optional[str] = None
    weight: Optional[float] = None  # in grams
    dimensions: Optional[dict] = None  # {"length": x, "width": y, "height": z}


class InventoryPart(BaseModel):
    """A part in a set's inventory."""
    part_no: str
    color_id: int
    qty: int
    name: str
    is_spare: bool = False
    is_counterpart: bool = False


class CatalogServiceInterface(ABC):
    """
    Abstract interface for LEGO parts catalog services.

    Implementations: BricklinkCatalogService, RebrickableCatalogService, etc.
    """

    @abstractmethod
    async def search_sets(self, query: str, limit: int = 20) -> List[SetSearchResult]:
        """
        Search for sets by name or description.

        Args:
            query: Search term (e.g., "Millennium Falcon" or "75192")
            limit: Maximum number of results to return

        Returns:
            List of matching sets with basic metadata

        Raises:
            CatalogAPIError: If the catalog service is unavailable
            CatalogAuthError: If authentication fails
        """
        pass

    @abstractmethod
    async def fetch_set_metadata(self, set_no: str) -> SetMetadata:
        """
        Fetch detailed metadata for a specific set.

        Args:
            set_no: LEGO set number (e.g., "75192")

        Returns:
            Detailed set metadata

        Raises:
            CatalogNotFoundError: If set doesn't exist in catalog
            CatalogAPIError: If the catalog service is unavailable
        """
        pass

    @abstractmethod
    async def fetch_set_inventory(self, set_no: str) -> List[InventoryPart]:
        """
        Fetch the complete parts inventory for a set.

        Args:
            set_no: LEGO set number (e.g., "75192")

        Returns:
            List of all parts in the set with quantities

        Raises:
            CatalogNotFoundError: If set doesn't exist in catalog
            CatalogAPIError: If the catalog service is unavailable
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the catalog service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        pass
