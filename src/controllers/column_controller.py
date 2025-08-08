from csv import Error
from datetime import datetime
from ..storage.markdown_storage import MarkdownStorage

from ..models.board import Board
from ..models.column import Column
from ..models.item import Item


class ColumnController:
    def __init__(self, board: Board, column: Column, storage: MarkdownStorage):
        self.column = column
        self.board = board
        self.storage = storage

    def save(self) -> None:
        self.storage.save_board(self.board)

    def add_item(
        self,
        title: str,
        column_id: str,
        parent_id: str | None = None,
        description: str = "",
    ) -> Item:
        item = self.column.add_item(title, column_id, parent_id)
        if description:
            item.description = description

        self.storage.save_board(self.board)

        return item

    def get_item_by_id(self, id: str) -> Item | None:
        for item in self.column.items:
            if item.id == id:
                return item

        return None

    def delete_item(self, item: Item) -> bool:
        if not self.storage.delete_item_from_column(self.board, item):
            raise Error("Delete failed")

        success = self.column.remove_item(item.id)

        if success:
            self.storage.save_board(self.board)

        return success

    def move_item(self, item_id: str, target_column_id: str) -> bool:
        item_to_move = None
        old_column_id = None

        for column in self.board.columns:
            for item in column.items:
                if item.id == item_id:
                    item_to_move = item
                    old_column_id = column.id
                    break
            if item_to_move:
                break

        if not item_to_move or not old_column_id:
            return False

        if old_column_id == target_column_id:
            return False

        target_column = self.board.get_column_by_id(target_column_id)
        if not target_column:
            return False

        file_moved = self.storage.move_item_between_columns(
            self.board, item_to_move, old_column_id, target_column_id
        )

        if not file_moved:
            return False

        old_column = self.board.get_column_by_id(old_column_id)
        if old_column:
            if not old_column.remove_item(item_id):
                raise Error()

        target_column.items.append(item_to_move)
        target_column.updated_at = datetime.now()

        self.storage.save_board(self.board)

        return True

    def get_column_items(
        self, column_id: str, grouped_by_parent: bool = False
    ) -> list[Item]:
        items = self.column.get_column_items(column_id)

        if not grouped_by_parent:
            return items

        orphaned_items = [item for item in items if item.parent_id is None]
        parent_groups: dict[str, list[Item]] = {}

        for item in items:
            if item.parent_id:
                if item.parent_id not in parent_groups:
                    parent_groups[item.parent_id] = []
                parent_groups[item.parent_id].append(item)

        grouped_items = orphaned_items[:]
        for parent_id, parent_items in parent_groups.items():
            grouped_items.extend(parent_items)

        return grouped_items
