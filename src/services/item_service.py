from typing import Optional, List
from core.exceptions import ItemNotFoundError, ColumnNotFoundError, ValidationError
from core.types import ItemId, ColumnId, ParentId
from domain.entities.board import Board
from domain.entities.item import Item
from domain.repositories.storage_repository import StorageRepository
from services.validation_service import ValidationService


class ItemService:
    def __init__(
        self,
        storage_repository: StorageRepository,
        validation_service: ValidationService,
    ):
        self._storage = storage_repository
        self._validator = validation_service

    def create_item(
        self,
        board: Board,
        column_id: ColumnId,
        title: str,
        description: str = "",
        parent_id: Optional[ParentId] = None,
    ) -> Item:
        self._validator.validate_item_title(title)

        column = board.get_column_by_id(column_id)
        if not column:
            raise ColumnNotFoundError(f"Column with id '{column_id}' not found")

        # Check if column is at capacity before adding
        self._validator.validate_column_capacity(column)

        if parent_id:
            parent = board.get_parent_by_id(parent_id)
            if not parent:
                raise ValidationError(f"Parent with id '{parent_id}' not found")

        item = column.add_item(title, parent_id)
        if description:
            item.description = description

        return item

    def update_item(self, board: Board, item_id: ItemId, **kwargs) -> bool:
        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                if "title" in kwargs:
                    self._validator.validate_item_title(kwargs["title"])

                item.update(**kwargs)
                return True

        raise ItemNotFoundError(f"Item with id '{item_id}' not found")

    def delete_item(self, board: Board, item_id: ItemId) -> bool:
        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                if not self._storage.delete_item_from_column(board, item, column):
                    raise ValidationError("Failed to delete item from storage")

                success = column.remove_item(item_id)
                if success:
                    self._storage.save_board_to_storage(board)
                return success

        raise ItemNotFoundError(f"Item with id '{item_id}' not found")

    def move_item_between_columns(
        self, board: Board, item_id: ItemId, target_column_id: ColumnId
    ) -> bool:
        item_to_move = None
        source_column = None

        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                item_to_move = item
                source_column = column
                break

        if not item_to_move or not source_column:
            raise ItemNotFoundError(f"Item with id '{item_id}' not found")

        if source_column.id == target_column_id:
            return False

        target_column = board.get_column_by_id(target_column_id)
        if not target_column:
            raise ColumnNotFoundError(
                f"Target column with id '{target_column_id}' not found"
            )

        # Check if target column is at capacity before moving
        self._validator.validate_column_capacity(target_column)

        if not self._storage.move_item_between_columns(
            board, item_to_move, source_column, target_column
        ):
            return False

        if not source_column.remove_item(item_id):
            raise ValidationError("Failed to remove item from source column")

        item_to_move.move_to_column(target_column_id)
        target_column.move_item_to_end(item_to_move)

        self._storage.save_board_to_storage(board)
        return True

    def set_item_parent(
        self, board: Board, item_id: ItemId, parent_id: Optional[ParentId]
    ) -> bool:
        if parent_id:
            parent = board.get_parent_by_id(parent_id)
            if not parent:
                raise ValidationError(f"Parent with id '{parent_id}' not found")

        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                item.set_parent(parent_id)
                return True

        raise ItemNotFoundError(f"Item with id '{item_id}' not found")

    def get_items_grouped_by_parent(
        self, board: Board, column_id: ColumnId
    ) -> List[Item]:
        column = board.get_column_by_id(column_id)
        if not column:
            raise ColumnNotFoundError(f"Column with id '{column_id}' not found")

        items = column.get_all_items()
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
