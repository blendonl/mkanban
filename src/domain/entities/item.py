from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from core.types import ItemId, ColumnId, ParentId, Timestamp, FilePath
from utils.string_utils import generate_id_from_name
from utils.date_utils import now


class Item(BaseModel):
    id: ItemId = Field(default="")
    title: str
    column_id: ColumnId
    description: str = ""
    parent_id: Optional[ParentId] = None
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
    file_path: Optional[FilePath] = None

    def model_post_init(self, __context) -> None:
        if self.file_path and not self.id:
            filename = Path(self.file_path).stem
            self.id = filename
            if not self.title or self.title == filename:
                self.title = filename
        elif not self.id:
            self.id = generate_id_from_name(self.title) or "unnamed_item"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()

    def move_to_column(self, column_id: ColumnId) -> None:
        self.column_id = column_id
        self.updated_at = now()

    def set_parent(self, parent_id: Optional[ParentId]) -> None:
        self.parent_id = parent_id
        self.updated_at = now()

    @property
    def has_parent(self) -> bool:
        return self.parent_id is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "column_id": self.column_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }