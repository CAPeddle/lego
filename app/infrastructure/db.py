import os
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData, Table
from sqlalchemy.orm import registry, sessionmaker
from app.core.models import LegoSet, Part, InventoryItem
from app.core.states import PieceState

DB_PATH = os.getenv("LEGO_DB_PATH", "./data/lego_inventory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
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
    Column("set_no", String, nullable=False),
    Column("part_no", String, nullable=False),
    Column("color_id", Integer, nullable=False),
    Column("qty", Integer, default=0),
    Column("state", String, nullable=False),
)

def init_db():
    metadata.create_all(engine)

# Simple repository implementations

class SqliteSetsRepository:
    def add(self, lego_set: LegoSet):
        db = SessionLocal()
        try:
            db.execute(sets_table.insert().values(set_no=lego_set.set_no, name=lego_set.name, assembled=lego_set.assembled))
            db.commit()
        finally:
            db.close()

    def get(self, set_no: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            r = db.execute(sets_table.select().where(sets_table.c.set_no == set_no)).first()
            return dict(r) if r else None
        finally:
            db.close()

class SqliteInventoryRepository:
    def add_part(self, set_no: str, part: Part, qty: int = 1, state: PieceState = PieceState.OWNED_FREE):
        db = SessionLocal()
        try:
            # check exists
            existing = db.execute(
                inventory_table.select().where(
                    (inventory_table.c.set_no == set_no) &
                    (inventory_table.c.part_no == part.part_no) &
                    (inventory_table.c.color_id == part.color_id)
                )
            ).first()
            if existing:
                db.execute(
                    inventory_table.update().where(inventory_table.c.id == existing.id).values(
                        qty=existing.qty + qty, state=state.value
                    )
                )
            else:
                db.execute(
                    inventory_table.insert().values(
                        set_no=set_no, part_no=part.part_no, color_id=part.color_id, qty=qty, state=state.value
                    )
                )
            db.commit()
        finally:
            db.close()

    def list(self, state: Optional[PieceState] = None):
        db = SessionLocal()
        try:
            if state:
                rows = db.execute(inventory_table.select().where(inventory_table.c.state == state.value)).fetchall()
            else:
                rows = db.execute(inventory_table.select()).fetchall()
            return [dict(r) for r in rows]
        finally:
            db.close()

    def update_item(self, part_no: str, color_id: int, qty: int, state: PieceState):
        db = SessionLocal()
        try:
            row = db.execute(inventory_table.select().where(
                (inventory_table.c.part_no == part_no) &
                (inventory_table.c.color_id == color_id)
            )).first()
            if not row:
                return False
            db.execute(inventory_table.update().where(inventory_table.c.id == row.id).values(qty=qty, state=state.value))
            db.commit()
            return True
        finally:
            db.close()
