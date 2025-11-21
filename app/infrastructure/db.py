import os
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    MetaData,
    Table,
    Index,
    select,
    update,
)
from sqlalchemy.orm import registry, sessionmaker, Session
from app.core.models import LegoSet, Part
from app.core.states import PieceState

DB_PATH = os.getenv("LEGO_DB_PATH", "./data/lego_inventory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
mapper_registry = registry()

metadata = MetaData()

sets_table = Table(
    "sets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("set_no", String, unique=True, index=True, nullable=False),
    Column("name", String),
    Column("assembled", Boolean, default=False),
)

parts_table = Table(
    "parts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("part_no", String, nullable=False),
    Column("color_id", Integer, nullable=False),
    Column("name", String),
)

inventory_table = Table(
    "inventory",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("set_no", String, nullable=False, index=True),
    Column("part_no", String, nullable=False),
    Column("color_id", Integer, nullable=False),
    Column("qty", Integer, default=0),
    Column("state", String, nullable=False, index=True),
    Index("ix_inventory_part_color", "part_no", "color_id"),
)

def init_db():
    metadata.create_all(engine)

def get_db():
    """FastAPI dependency to provide a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple repository implementations

class SqliteSetsRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, lego_set: LegoSet) -> None:
        self.db.execute(
            sets_table.insert().values(
                set_no=lego_set.set_no,
                name=lego_set.name,
                assembled=lego_set.assembled,
            )
        )
        self.db.commit()

    def get(self, set_no: str) -> Optional[dict]:
        r = self.db.execute(
            select(sets_table).where(sets_table.c.set_no == set_no)
        ).first()
        return dict(r._mapping) if r else None

class SqliteInventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_part(
        self,
        set_no: str,
        part: Part,
        qty: int = 1,
        state: PieceState = PieceState.OWNED_FREE,
    ) -> None:
        existing = self.db.execute(
            select(inventory_table).where(
                (inventory_table.c.set_no == set_no)
                & (inventory_table.c.part_no == part.part_no)
                & (inventory_table.c.color_id == part.color_id)
            )
        ).first()
        if existing:
            self.db.execute(
                update(inventory_table)
                .where(inventory_table.c.id == existing.id)
                .values(qty=existing.qty + qty, state=state.value)
            )
        else:
            self.db.execute(
                inventory_table.insert().values(
                    set_no=set_no,
                    part_no=part.part_no,
                    color_id=part.color_id,
                    qty=qty,
                    state=state.value,
                )
            )
        self.db.commit()

    def list(self, state: Optional[PieceState] = None) -> List[dict]:
        if state:
            rows = self.db.execute(
                select(inventory_table).where(inventory_table.c.state == state.value)
            ).fetchall()
        else:
            rows = self.db.execute(select(inventory_table)).fetchall()
        return [dict(r._mapping) for r in rows]

    def update_item(
        self, part_no: str, color_id: int, qty: int, state: PieceState
    ) -> bool:
        row = self.db.execute(
            select(inventory_table).where(
                (inventory_table.c.part_no == part_no)
                & (inventory_table.c.color_id == color_id)
            )
        ).first()
        if not row:
            return False
        self.db.execute(
            update(inventory_table)
            .where(inventory_table.c.id == row.id)
            .values(qty=qty, state=state.value)
        )
        self.db.commit()
        return True
