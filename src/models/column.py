from datetime import datetime
from uuid import uuid4

from .item import Item
from pydantic import BaseModel, Field


class Column(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    position: int = 0
    limit: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    items: list[Item] = Field(default_factory=list)

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def add_item(
        self, title: str, column_id: str, parent_id: str | None = None
    ) -> Item:
        item = Item(title=title, column_id=column_id, parent_id=parent_id)
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

    def get_column_items(self, column_id: str) -> list[Item]:
        return [item for item in self.items if item.column_id == column_id]
