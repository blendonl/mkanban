"""Board controller for managing board operations."""

from typing import Optional, List
from ..models import Board, Item, Column, Parent
from ..storage import MarkdownStorage


class BoardController:
    """Controller for board operations."""
    
    def __init__(self, board: Board, storage: MarkdownStorage):
        """Initialize controller with board and storage."""
        self.board = board
        self.storage = storage
    
    def save(self) -> None:
        """Save the current board."""
        self.storage.save_board(self.board)
    
    def add_item(self, title: str, column_id: str, parent_id: Optional[str] = None, description: str = "") -> Item:
        """Add a new item to the board."""
        item = self.board.add_item(title, column_id, parent_id)
        if description:
            item.description = description
        
        # Save the new item to its column folder
        self.storage.save_item_in_column(self.board, item)
        # Save the board to update the item references
        self.storage.save_board(self.board)
        
        return item
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the board and its file."""
        # Find the item first to delete from correct location
        item = None
        for board_item in self.board.items:
            if board_item.id == item_id:
                item = board_item
                break
        
        success = self.board.remove_item(item_id)
        if success and item:
            # Try to delete from column folder first, fallback to legacy
            if not self.storage.delete_item_from_column(self.board, item):
                self.storage.delete_item(item_id)
        return success
    
    def move_item(self, item_id: str, target_column_id: str) -> bool:
        """Move an item to a different column."""
        for item in self.board.items:
            if item.id == item_id:
                item.move_to_column(target_column_id)
                
                # Save the updated item to its column folder
                self.storage.save_item_in_column(self.board, item)
                # Save the board to update column references
                self.storage.save_board(self.board)
                
                return True
        return False
    
    def update_item(self, item_id: str, **kwargs) -> bool:
        """Update an item's properties."""
        for item in self.board.items:
            if item.id == item_id:
                item.update(**kwargs)
                
                # Save the updated item to its column folder
                self.storage.save_item_in_column(self.board, item)
                # Save the board in case title or other references changed
                self.storage.save_board(self.board)
                
                return True
        return False
    
    def set_item_parent(self, item_id: str, parent_id: Optional[str]) -> bool:
        """Set or remove an item's parent."""
        for item in self.board.items:
            if item.id == item_id:
                item.set_parent(parent_id)
                
                # Save the updated item to its column folder
                self.storage.save_item_in_column(self.board, item)
                # Save the board to update parent references
                self.storage.save_board(self.board)
                
                return True
        return False
    
    def add_column(self, name: str, position: Optional[int] = None) -> Column:
        """Add a new column to the board."""
        return self.board.add_column(name, position)
    
    def delete_column(self, column_id: str) -> bool:
        """Delete a column and all its items."""
        return self.board.remove_column(column_id)
    
    def add_parent(self, name: str, color: str = "blue") -> Parent:
        """Add a new parent group."""
        return self.board.add_parent(name, color)
    
    def delete_parent(self, parent_id: str) -> bool:
        """Delete a parent group and unlink its items."""
        return self.board.remove_parent(parent_id)
    
    def get_column_items(self, column_id: str, grouped_by_parent: bool = False) -> List[Item]:
        """Get items in a column, optionally grouped by parent."""
        items = self.board.get_column_items(column_id)
        
        if not grouped_by_parent:
            return items
        
        # Group items by parent
        orphaned_items = [item for item in items if item.parent_id is None]
        parent_groups = {}
        
        for item in items:
            if item.parent_id:
                if item.parent_id not in parent_groups:
                    parent_groups[item.parent_id] = []
                parent_groups[item.parent_id].append(item)
        
        # Return grouped structure (this is simplified - UI will handle proper grouping)
        grouped_items = orphaned_items[:]
        for parent_id, parent_items in parent_groups.items():
            grouped_items.extend(parent_items)
        
        return grouped_items