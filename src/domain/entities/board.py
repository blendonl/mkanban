from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from src.core.types import BoardId, ColumnId, ParentId, Timestamp, FilePath
from src.utils.string_utils import generate_id_from_name
from src.utils.date_utils import now
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.domain.entities.parent import Parent


class Board(BaseModel):
    id: BoardId = Field(default="")
    name: str
    description: str = ""
    file_path: Optional[FilePath] = None
    columns: list[Column] = Field(default_factory=list)
    parents: list[Parent] = Field(default_factory=list)
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)

    def model_post_init(self, __context) -> None:
        if self.file_path and not self.id:
            dir_name = Path(self.file_path).parent.name
            self.id = dir_name
            if not self.name or self.name == dir_name:
                self.name = dir_name
        elif not self.id:
            self.id = generate_id_from_name(self.name) or "unnamed_board"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()

    def add_column(self, name: str, position: Optional[int] = None) -> Column:
        if position is None:
            position = len(self.columns)

        column = Column(name=name, position=position)
        self.columns.append(column)
        self.columns.sort(key=lambda c: (c.position, c.name))
        self.updated_at = now()
        return column

    def remove_column(self, column_id: ColumnId) -> bool:
        original_count = len(self.columns)
        self.columns = [col for col in self.columns if col.id != column_id]
        if len(self.columns) < original_count:
            self.updated_at = now()
            return True
        return False

    def get_column_by_id(self, column_id: ColumnId) -> Optional[Column]:
        for column in self.columns:
            if column.id == column_id:
                return column
        return None

    def get_first_column(self) -> Optional[Column]:
        if not self.columns:
            return None
        return min(self.columns, key=lambda c: c.position)

    def get_orphaned_items(self) -> list[Item]:
        items: list[Item] = []
        for column in self.columns:
            items.extend([item for item in column.items if item.parent_id is None])
        return items

    def add_parent(self, name: str, color: str = "blue") -> Parent:
        parent = Parent(name=name, color=color)
        self.parents.append(parent)
        self.updated_at = now()
        return parent

    def remove_parent(self, parent_id: ParentId) -> bool:
        original_count = len(self.parents)
        self.parents = [parent for parent in self.parents if parent.id != parent_id]
        if len(self.parents) < original_count:
            self.updated_at = now()
            return True
        return False

    def get_parent_by_id(self, parent_id: ParentId) -> Optional[Parent]:
        for parent in self.parents:
            if parent.id == parent_id:
                return parent
        return None
