"""Column model for kanban columns."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Column(BaseModel):
    """Represents a kanban column."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    position: int = 0
    limit: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update(self, **kwargs) -> None:
        """Update column fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()