from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from src.core.types import ColumnId, ParentId, Timestamp, FilePath
from src.utils.string_utils import generate_id_from_name
from src.utils.date_utils import now
from src.domain.entities.item import Item


class Column(BaseModel):
    id: ColumnId = Field(default="")
    name: str
    position: int = 0
    limit: Optional[int] = None
    created_at: Timestamp = Field(default_factory=now)
    items: list[Item] = Field(default_factory=list)
    file_path: Optional[FilePath] = None

    def model_post_init(self, __context) -> None:
        if self.file_path and not self.id:
            dir_name = Path(self.file_path).parent.name
            self.id = dir_name
            if not self.name or self.name == dir_name:
                self.name = dir_name.replace("-", " ").replace("_", " ").title()
        elif not self.id:
            self.id = generate_id_from_name(self.name) or "unnamed_column"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_item(self, title: str, parent_id: Optional[ParentId] = None, item_id: Optional[str] = None) -> Item:
        """Add a new item to the column.

        Args:
            title: Item title
            parent_id: Optional parent ID for grouping
            item_id: Optional pre-generated item ID (used by service layer)

        Returns:
            The created Item
        """
        item = Item(id=item_id or "", title=title, parent_id=parent_id, column_id=self.id)
        self.items.append(item)
        return item

    def move_item_to_end(self, item: Item) -> bool:
        item.move_to_column(self.id)
        self.items.append(item)
        return True

    def remove_item(self, item_id: str) -> bool:
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        return len(self.items) < original_count

    def get_all_items(self) -> list[Item]:
        return self.items

    def get_item_by_id(self, item_id: str) -> Optional[Item]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "limit": self.limit,
            "created_at": self.created_at,
        }
