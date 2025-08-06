"""Board controller for managing board operations."""

from typing import Optional, List
from ..models import Board, Item, Column, Parent
from ..storage import MarkdownStorage


class BoardController:
    def __init__(self, board: Board, storage: MarkdownStorage):
        """Initialize controller with board and storage."""
        self.board = board
        self.storage = storage

    def save(self) -> None:
        """Save the current board."""
        self.storage.save_board(self.board)

    def add_item(self, title: str, column_id: str, parent_id: Optional[str] = None, description: str = "") -> Item:
        """Add a new item to the board."""
        item = self.board.get_column_by_id(
            column_id).add_item(title, column_id, parent_id)
        if description:
            item.description = description

        # Save the board to update the item references and files
        self.storage.save_board(self.board)

        return item

    def delete_item(self, item: Item) -> bool:
        self.storage.delete_item_from_column(self.board, item)

        success = self.board.get_column_by_id(
            item.column_id).remove_item(item.id)

        if success:
            # Save the board to update references
            self.storage.save_board(self.board)

        return success

    def move_item(self, item_id: str, target_column_id: str) -> bool:
        column = self.board.get_column_by_id(target_column_id)
        success = column.move_item_to_end_of_column(item_id)

        if success:
            moved_item = None
            for item in column.items:
                if item.id == item_id:
                    moved_item = item
                    break

            if moved_item:
                self.storage.save_board(self.board)

        return success

    def update_item(self, item_id: str, **kwargs) -> bool:
        """Update an item's properties."""
        for item in self.board.items:
            if item.id == item_id:
                item.update(**kwargs)

                # Save the board to update item files and references
                self.storage.save_board(self.board)

                return True
        return False

    def set_item_parent(self, item_id: str, parent_id: Optional[str]) -> bool:
        """Set or remove an item's parent."""
        for item in self.board.items:
            if item.id == item_id:
                item.set_parent(parent_id)

                # Save the board to update item files and parent references
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
        items = self.board.get_column_by_id(
            column_id).get_column_items(column_id)

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

        grouped_items = orphaned_items[:]
        for parent_id, parent_items in parent_groups.items():
            grouped_items.extend(parent_items)

        return grouped_items
