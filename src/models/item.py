from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class Item(BaseModel):
    """Represents a single kanban item/card."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    parent_id: Optional[str] = None
    column_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update(self, **kwargs) -> None:
        """Update item fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def move_to_column(self, column_id: str) -> None:
        """Move item to a different column."""
        self.column_id = column_id
        self.updated_at = datetime.now()

    def set_parent(self, parent_id: Optional[str]) -> None:
        """Set or remove parent relationship."""
        self.parent_id = parent_id
        self.updated_at = datetime.now()

    @property
    def has_parent(self) -> bool:
        """Check if item has a parent."""
        return self.parent_id is not None

