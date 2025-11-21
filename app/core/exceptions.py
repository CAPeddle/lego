class LegoServiceError(Exception):
    """Base exception for domain errors."""


class SetNotFoundError(LegoServiceError):
    """Raised when a requested set cannot be found."""


class BricklinkAPIError(LegoServiceError):
    """Raised when Bricklink API interaction fails."""


class InvalidSetNumberError(LegoServiceError):
    """Raised when a set number format is invalid."""


class DatabaseError(LegoServiceError):
    """Raised for database persistence/retrieval issues."""


class InventoryItemNotFoundError(LegoServiceError):
    """Raised when an inventory item update targets a non-existent record."""


# Catalog-related exceptions (used by legacy infrastructure tests)
class CatalogServiceError(LegoServiceError):
    """Base exception for external catalog service errors."""


class CatalogAPIError(CatalogServiceError):
    """External catalog API error or unexpected response."""


class CatalogAuthError(CatalogServiceError):
    """Authentication with catalog service failed."""


class CatalogNotFoundError(CatalogServiceError):
    """Resource not found in external catalog."""


class CatalogRateLimitError(CatalogServiceError):
    """External catalog rate limit exceeded."""


class CatalogTimeoutError(CatalogServiceError):
    """External catalog request timed out."""
