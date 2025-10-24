from typing import Optional, List
import re
from src.core.exceptions import ItemNotFoundError, ColumnNotFoundError, ValidationError
from src.core.types import ItemId, ColumnId, ParentId
from src.domain.entities.board import Board
from src.domain.entities.item import Item
from src.domain.repositories.storage_repository import StorageRepository
from src.services.validation_service import ValidationService
from src.utils.logger_factory import ContextAwareLogger
from src.utils.string_utils import generate_manual_item_id, get_board_prefix
from src.config.configuration_manager import ConfigurationManager
from src.core.event_bus import get_event_bus


class ItemService:
    def __init__(
        self,
        storage_repository: StorageRepository,
        validation_service: ValidationService,
        logger: ContextAwareLogger,
        config_manager: ConfigurationManager
    ):
        self._storage = storage_repository
        self._validator = validation_service
        self._logger = logger
        self._config = config_manager
        self._event_bus = get_event_bus()

    def create_item(
        self,
        board: Board,
        column_id: ColumnId,
        title: str,
        description: str = "",
        parent_id: Optional[ParentId] = None,
    ) -> Item:
        self._logger.info("Creating item", board=board.name, column=column_id, item=title)
        self._validator.validate_item_title(title)

        column = board.get_column_by_id(column_id)
        if not column:
            self._logger.warning("Column not found", board=board.name, column=column_id)
            raise ColumnNotFoundError(f"Column with id '{column_id}' not found")

        # Check if column is at capacity before adding
        self._validator.validate_column_capacity(column)

        if parent_id:
            parent = board.get_parent_by_id(parent_id)
            if not parent:
                self._logger.warning("Parent not found", board=board.name, item=title)
                raise ValidationError(f"Parent with id '{parent_id}' not found")

        # Generate ID for manual item
        next_index = self._get_next_item_index(board)
        item_id = generate_manual_item_id(board.name, next_index)

        item = column.add_item(title, parent_id, item_id)
        if description:
            item.description = description

        # Set default issue type for manually created items
        item.metadata["issue_type"] = self._config.config.default_issue_type

        self._logger.info("Successfully created item", board=board.name, column=column.name, item=title, item_id=item_id)

        # Emit task state change event
        self._event_bus.publish("task_state_change", {
            "event": "created",
            "task": item,
            "board": board,
            "column_id": column_id
        })

        return item

    def _get_next_item_index(self, board: Board) -> int:
        """Calculate the next sequential index for manual items on this board.

        Scans all items across all columns to find the highest index for this board's prefix,
        then returns the next index.

        Args:
            board: The board to calculate the next index for

        Returns:
            The next available index (starting from 1)
        """
        board_prefix = get_board_prefix(board.name)
        pattern = re.compile(rf"^{re.escape(board_prefix)}-(\d+)$")
        max_index = 0

        # Scan all items across all columns
        for column in board.columns:
            for item in column.items:
                match = pattern.match(item.id)
                if match:
                    index = int(match.group(1))
                    max_index = max(max_index, index)

        return max_index + 1

    def update_item(self, board: Board, item_id: ItemId, **kwargs) -> bool:
        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                if "title" in kwargs:
                    self._validator.validate_item_title(kwargs["title"])

                item.update(**kwargs)

                # Emit task state change event
                self._event_bus.publish("task_state_change", {
                    "event": "updated",
                    "task": item,
                    "board": board,
                    "column_id": column.id,
                    "updates": kwargs
                })

                return True

        raise ItemNotFoundError(f"Item with id '{item_id}' not found")

    def delete_item(self, board: Board, item_id: ItemId) -> bool:
        self._logger.info("Deleting item", board=board.name, item=item_id)

        for column in board.columns:
            item = column.get_item_by_id(item_id)
            if item:
                self._logger.debug("Found item to delete", board=board.name, column=column.name, item=item.title)

                if not self._storage.delete_item_from_column(board, item, column):
                    self._logger.error("Failed to delete item from storage", board=board.name, column=column.name, item=item.title)
                    raise ValidationError("Failed to delete item from storage")

                success = column.remove_item(item_id)
                if success:
                    self._storage.save_board_to_storage(board)
                    self._logger.info("Successfully deleted item", board=board.name, column=column.name, item=item.title)

                    # Emit task state change event
                    self._event_bus.publish("task_state_change", {
                        "event": "deleted",
                        "task": item,
                        "board": board,
                        "column_id": column.id
                    })

                return success

        self._logger.warning("Item not found for deletion", board=board.name, item=item_id)
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

        # Emit task state change event
        self._event_bus.publish("task_state_change", {
            "event": "moved",
            "task": item_to_move,
            "board": board,
            "source_column_id": source_column.id,
            "target_column_id": target_column_id
        })

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
