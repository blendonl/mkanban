from typing import Optional
from ..models.board import Board
from ..models.board import Parent
from ..models.board import Item
from ..storage.markdown_storage import MarkdownStorage


class ItemController:
    def __init__(self, board: Board, item: Item, storage: MarkdownStorage):
        self.board = board
        self.item = item
        self.storage = storage

    def save(self) -> None:
        self.storage.save_board(self.board)

    def update_item(self, item_id: str, **kwargs) -> bool:
        for item in self.board.items:
            if item.id == item_id:
                item.update(**kwargs)

                self.storage.save_board(self.board)

                return True
        return False

    def set_item_parent(self, item_id: str, parent_id: Optional[str]) -> bool:
        for item in self.board.items:
            if item.id == item_id:
                item.set_parent(parent_id)

                self.storage.save_board(self.board)

                return True
        return False

    def add_parent(self, name: str, color: str = "blue") -> Parent:
        return self.board.add_parent(name, color)

    def delete_parent(self, parent_id: str) -> bool:
        return self.board.remove_parent(parent_id)
