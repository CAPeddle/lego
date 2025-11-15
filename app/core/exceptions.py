"""
Custom exception hierarchy for the LEGO inventory service.

All domain exceptions inherit from LegoServiceError.
Convert these to HTTPException in the API layer.
"""


class LegoServiceError(Exception):
    """Base exception for all LEGO service errors."""
    pass


# Catalog Service Exceptions
class CatalogServiceError(LegoServiceError):
    """Base exception for catalog service errors."""
    pass


class CatalogAPIError(CatalogServiceError):
    """Catalog API is unavailable or returned an error."""
    pass


class CatalogAuthError(CatalogServiceError):
    """Authentication with catalog service failed."""
    pass


class CatalogNotFoundError(CatalogServiceError):
    """Requested resource not found in catalog."""
    pass


class CatalogRateLimitError(CatalogServiceError):
    """Catalog service rate limit exceeded."""
    pass


class CatalogTimeoutError(CatalogServiceError):
    """Catalog service request timed out."""
    pass


# Domain Exceptions
class SetNotFoundError(LegoServiceError):
    """Set not found in local database."""
    pass


class InvalidSetNumberError(LegoServiceError):
    """Set number format is invalid."""
    pass


class DatabaseError(LegoServiceError):
    """Database operation failed."""
    pass


class PartNotFoundError(LegoServiceError):
    """Part not found in inventory."""
    pass


class InvalidStateTransitionError(LegoServiceError):
    """Invalid state transition requested."""
    pass
