"""Board model for kanban boards."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field

from .column import Column
from .item import Item
from .parent import Parent


class Board(BaseModel):
    """Represents a kanban board."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    file_path: Optional[Path] = None
    columns: List[Column] = Field(default_factory=list)
    items: List[Item] = Field(default_factory=list)
    parents: List[Parent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def update(self, **kwargs) -> None:
        """Update board fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def add_column(self, name: str, position: Optional[int] = None) -> Column:
        """Add a new column to the board."""
        if position is None:
            position = len(self.columns)
        
        column = Column(name=name, position=position)
        self.columns.append(column)
        self.columns.sort(key=lambda c: c.position)
        self.updated_at = datetime.now()
        return column
    
    def remove_column(self, column_id: str) -> bool:
        """Remove a column and all its items."""
        column_items = [item for item in self.items if item.column_id == column_id]
        for item in column_items:
            self.items.remove(item)
        
        self.columns = [col for col in self.columns if col.id != column_id]
        self.updated_at = datetime.now()
        return True
    
    def add_item(self, title: str, column_id: str, parent_id: Optional[str] = None) -> Item:
        """Add a new item to the board."""
        item = Item(title=title, column_id=column_id, parent_id=parent_id)
        self.items.append(item)
        self.updated_at = datetime.now()
        return item
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the board."""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        if len(self.items) < original_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def add_parent(self, name: str, color: str = "blue") -> Parent:
        """Add a new parent group to the board."""
        parent = Parent(name=name, color=color)
        self.parents.append(parent)
        self.updated_at = datetime.now()
        return parent
    
    def remove_parent(self, parent_id: str) -> bool:
        """Remove a parent and unlink all its items."""
        for item in self.items:
            if item.parent_id == parent_id:
                item.set_parent(None)
        
        original_count = len(self.parents)
        self.parents = [parent for parent in self.parents if parent.id != parent_id]
        if len(self.parents) < original_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_column_items(self, column_id: str) -> List[Item]:
        """Get all items in a specific column."""
        return [item for item in self.items if item.column_id == column_id]
    
    def get_parent_items(self, parent_id: str) -> List[Item]:
        """Get all items with a specific parent."""
        return [item for item in self.items if item.parent_id == parent_id]
    
    def get_orphaned_items(self) -> List[Item]:
        """Get all items without a parent."""
        return [item for item in self.items if item.parent_id is None]