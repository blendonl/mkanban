from ..domain.entities.board import Board
from ..domain.entities.parent import Parent
from ..domain.entities.item import Item
from ..services.board_service import BoardService
from ..services.item_service import ItemService
from ..core.types import ItemId, ParentId


class ItemController:
    def __init__(
        self, 
        board: Board, 
        item: Item, 
        board_service: BoardService, 
        item_service: ItemService
    ):
        self.board = board
        self.item = item
        self._board_service = board_service
        self._item_service = item_service

    def save(self) -> None:
        self._board_service.save_board(self.board)

    def update_item(self, item_id: ItemId, **kwargs) -> bool:
        return self._item_service.update_item(self.board, item_id, **kwargs)

    def set_item_parent(self, item_id: ItemId, parent_id: ParentId | None) -> bool:
        return self._item_service.set_item_parent(self.board, item_id, parent_id)

    def add_parent(self, name: str, color: str = "blue") -> Parent:
        return self.board.add_parent(name, color)

    def delete_parent(self, parent_id: ParentId) -> bool:
        return self.board.remove_parent(parent_id)