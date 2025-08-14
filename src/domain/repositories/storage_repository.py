from abc import ABC, abstractmethod
from typing import Optional
from ...core.types import ItemId, ColumnId, BoardId
from ..entities.board import Board
from ..entities.column import Column
from ..entities.item import Item


class StorageRepository(ABC):
    @abstractmethod
    def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
        pass

    @abstractmethod
    def move_item_between_columns(
        self, board: Board, item: Item, old_column: Column, new_column: Column
    ) -> bool:
        pass

    @abstractmethod
    def save_board_to_storage(self, board: Board) -> None:
        pass