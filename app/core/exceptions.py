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
