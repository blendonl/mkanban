from datetime import datetime
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field

from .column import Column
from .item import Item
from .parent import Parent


class Board(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    file_path: Path | None = None
    columns: list[Column] = Field(default_factory=list)
    parents: list[Parent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def add_column(self, name: str, position: int | None = None) -> Column:
        if position is None:
            position = len(self.columns)

        column = Column(name=name, position=position)
        self.columns.append(column)
        self.columns.sort(key=lambda c: c.position)
        self.updated_at = datetime.now()
        return column

    def remove_column(self, column_id: str) -> bool:
        self.columns = [col for col in self.columns if col.id != column_id]
        self.updated_at = datetime.now()
        return True

    def get_column_by_id(self, column_id: str) -> Column | None:
        for column in self.columns:
            if column.id == column_id:
                return column
        return None

    def get_orphaned_items(self) -> list[Item]:
        items: list[Item] = []
        for column in self.columns:
            items.extend([item for item in column.items if item.parent_id is None])
        return items

    def add_parent(self, name: str, color: str = "blue") -> Parent:
        parent = Parent(name=name, color=color)
        self.parents.append(parent)
        self.updated_at = datetime.now()
        return parent

    def remove_parent(self, parent_id: str) -> bool:
        original_count = len(self.parents)
        self.parents = [parent for parent in self.parents if parent.id != parent_id]
        if len(self.parents) < original_count:
            self.updated_at = datetime.now()
            return True
        return False
