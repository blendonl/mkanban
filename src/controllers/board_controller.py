from ..models.board import Board
from ..models.column import Column
from ..storage.markdown_storage import MarkdownStorage


class BoardController:
    def __init__(self, board: Board, storage: MarkdownStorage):
        self.board = board
        self.storage = storage

    def save(self) -> None:
        self.storage.save_board(self.board)

    def add_column(self, name: str, position: int | None = None) -> Column:
        return self.board.add_column(name, position)

    def delete_column(self, column_id: str) -> bool:
        return self.board.remove_column(column_id)
