"""Board model for kanban boards."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field

from .column import Column
from .item import Item


class Board(BaseModel):
    """Represents a kanban board."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    file_path: Optional[Path] = None
    columns: List[Column] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def add_column(self, name: str, position: Optional[int] = None) -> Column:
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

    def get_column_by_id(self, column_id: str) -> Optional[Column]:
        for column in self.columns:
            if column.id == column_id:
                return column
        return None

    def get_orphaned_items(self) -> List[Item]:
        items = []
        for column in self.columns:
            items.extend(
                [item for item in column.items if item.parent_id is None])
        return items
