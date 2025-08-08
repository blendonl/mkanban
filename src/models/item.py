from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    parent_id: str | None = None
    column_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def move_to_column(self, column_id: str) -> None:
        self.column_id = column_id
        self.updated_at = datetime.now()

    def set_parent(self, parent_id: str | None) -> None:
        self.parent_id = parent_id
        self.updated_at = datetime.now()

    @property
    def has_parent(self) -> bool:
        return self.parent_id is not None
