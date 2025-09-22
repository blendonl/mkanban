from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.services.board_service import BoardService
from src.core.types import ColumnId


class BoardController:
    def __init__(self, board: Board, board_service: BoardService):
        self.board = board
        self._board_service = board_service

    def save(self) -> None:
        self._board_service.save_board(self.board)

    def add_column(self, name: str, position: int | None = None) -> Column:
        return self._board_service.add_column_to_board(self.board, name, position)

    def delete_column(self, column_id: ColumnId) -> bool:
        return self._board_service.remove_column_from_board(self.board, column_id)
