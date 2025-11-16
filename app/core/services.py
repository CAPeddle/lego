"""
Business logic for LEGO inventory management.

The InventoryService orchestrates operations across repositories and
external catalog services (Bricklink, Rebrickable, etc.).
"""

from app.core.models import LegoSet, Part
from app.core.states import PieceState
from app.core.catalog_interface import CatalogServiceInterface
from typing import List


class InventoryService:
    """
    Service for managing LEGO sets and inventory.

    Coordinates between repositories and catalog services to add sets,
    track inventory, and manage part states.
    """

    def __init__(
        self,
        inventory_repo,
        sets_repo,
        catalog_service: CatalogServiceInterface,
    ):
        """
        Initialize inventory service.

        Args:
            inventory_repo: Repository for inventory operations
            sets_repo: Repository for set operations
            catalog_service: Catalog service implementation (Bricklink, etc.)
        """
        self.inventory_repo = inventory_repo
        self.sets_repo = sets_repo
        self.catalog_service = catalog_service

    async def add_set(self, set_no: str, assembled: bool = False) -> LegoSet:
        """
        Add a LEGO set to the database with its parts inventory.

        Fetches set metadata and parts list from the catalog service,
        stores the set, and adds all parts to inventory with appropriate state.

        Args:
            set_no: LEGO set number (e.g., "75192")
            assembled: Whether the set is assembled (affects part state)

        Returns:
            The created LegoSet with metadata

        Raises:
            CatalogNotFoundError: If set doesn't exist in catalog
            CatalogAPIError: If catalog service is unavailable
        """
        # Fetch set metadata and parts from catalog service
        set_meta = await self.catalog_service.fetch_set_metadata(set_no)
        parts = await self.catalog_service.fetch_set_inventory(set_no)

        # Create set record
        lego_set = LegoSet(
            set_no=set_no,
            name=set_meta.name,
            assembled=assembled,
        )

        # Store set in database
        self.sets_repo.add(lego_set)

        # Determine part state based on assembly status
        state = PieceState.OWNED_LOCKED if assembled else PieceState.OWNED_FREE

        # Add all parts to inventory
        for inventory_part in parts:
            part = Part(
                part_no=inventory_part.part_no,
                color_id=inventory_part.color_id,
                name=inventory_part.name,
            )
            self.inventory_repo.add_part(
                lego_set.set_no,
                part,
                qty=inventory_part.qty,
                state=state,
            )

        return lego_set
