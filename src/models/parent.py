"""Parent model for grouping kanban items."""

from datetime import datetime
from typing import List, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class Parent(BaseModel):
    """Represents a parent group for kanban items."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    color: str = "blue"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update(self, **kwargs) -> None:
        """Update parent fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()