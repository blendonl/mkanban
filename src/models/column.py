from datetime import datetime
from pydantic import BaseModel, Field
import re

from .item import Item


class Column(BaseModel):
    id: str = Field(default="")
    name: str
    position: int = 0
    limit: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    items: list[Item] = Field(default_factory=list)
    file_path: str | None = None

    def model_post_init(self, __context) -> None:
        # For columns, if we have a file_path, use the directory name as both id and name
        if self.file_path and not self.id:
            from pathlib import Path

            dir_name = Path(self.file_path).parent.name
            self.id = dir_name
            self.name = dir_name
        elif not self.id:
            self.id = self._generate_id_from_name(self.name)

    def _generate_id_from_name(self, name: str) -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        safe_name = re.sub(r"\s+", "_", safe_name.strip())
        return safe_name or "unnamed_column"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def add_item(self, title: str, parent_id: str | None = None) -> Item:
        item = Item(title=title, parent_id=parent_id, column_id=self.id)
        self.items.append(item)
        self.updated_at = datetime.now()
        return item

    def move_item_to_end_of_column(self, item: Item) -> bool:
        item.move_to_column(self.id)

        self.items.append(item)

        self.updated_at = datetime.now()

        return True

    def remove_item(self, item_id: str) -> bool:
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        if len(self.items) < original_count:
            self.updated_at = datetime.now()
            return True
        return False

    def get_all_items(self) -> list[Item]:
        return self.items
