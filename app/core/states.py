from enum import Enum


class PieceState(str, Enum):
    MISSING = "MISSING"
    OWNED_LOCKED = "OWNED_LOCKED"
    OWNED_FREE = "OWNED_FREE"
