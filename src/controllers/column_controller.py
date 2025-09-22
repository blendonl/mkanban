from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.core.types import ItemId, ColumnId, ParentId


class ColumnController:
    def __init__(
        self,
        board: Board,
        column: Column,
        board_service: BoardService,
        item_service: ItemService,
    ):
        self.column = column
        self.board = board
        self._board_service = board_service
        self._item_service = item_service

    @property
    def board_service(self) -> BoardService:
        return self._board_service

    @property
    def item_service(self) -> ItemService:
        return self._item_service

    def save(self) -> None:
        self._board_service.save_board(self.board)

    def add_item(
        self,
        title: str,
        parent_id: ParentId | None = None,
        description: str = "",
    ) -> Item:
        return self._item_service.create_item(
            self.board, self.column.id, title, description, parent_id
        )

    def get_item_by_id(self, item_id: ItemId) -> Item | None:
        return self.column.get_item_by_id(item_id)

    def delete_item(self, item: Item) -> bool:
        return self._item_service.delete_item(self.board, item.id)

    def move_item(self, item_id: ItemId, target_column_id: ColumnId) -> bool:
        return self._item_service.move_item_between_columns(
            self.board, item_id, target_column_id
        )

    def get_column_items(
        self, column_id: ColumnId, grouped_by_parent: bool = False
    ) -> list[Item]:
        if grouped_by_parent:
            return self._item_service.get_items_grouped_by_parent(self.board, column_id)
        else:
            return self.column.get_all_items()
