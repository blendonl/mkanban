from typing import List, Optional
from core.exceptions import BoardNotFoundError, ValidationError
from core.types import BoardId, ColumnId
from domain.entities.board import Board
from domain.entities.column import Column
from domain.repositories.board_repository import BoardRepository
from services.validation_service import ValidationService


class BoardService:
    def __init__(self, board_repository: BoardRepository, validation_service: ValidationService):
        self._repository = board_repository
        self._validator = validation_service

    def get_all_boards(self) -> List[Board]:
        return self._repository.load_all_boards()

    def get_board_by_id(self, board_id: BoardId) -> Board:
        board = self._repository.load_board_by_id(board_id)
        if not board:
            raise BoardNotFoundError(f"Board with id '{board_id}' not found")
        return board

    def get_board_by_name(self, board_name: str) -> Board:
        board = self._repository.load_board_by_name(board_name)
        if not board:
            raise BoardNotFoundError(f"Board with name '{board_name}' not found")
        return board

    def create_board(self, name: str, description: str = "") -> Board:
        self._validator.validate_board_name(name)
        
        existing_board = self._repository.load_board_by_name(name)
        if existing_board:
            raise ValidationError(f"Board with name '{name}' already exists")
        
        board = Board(name=name, description=description)
        self._repository.save_board(board)
        return board

    def save_board(self, board: Board) -> None:
        self._validator.validate_board(board)
        self._repository.save_board(board)

    def delete_board(self, board_id: BoardId) -> bool:
        return self._repository.delete_board(board_id)

    def add_column_to_board(self, board: Board, column_name: str, position: Optional[int] = None) -> Column:
        self._validator.validate_column_name(column_name)
        
        for existing_column in board.columns:
            if existing_column.name.lower() == column_name.lower():
                raise ValidationError(f"Column '{column_name}' already exists in board")
        
        return board.add_column(column_name, position)

    def remove_column_from_board(self, board: Board, column_id: ColumnId) -> bool:
        column = board.get_column_by_id(column_id)
        if not column:
            return False
        
        if len(column.items) > 0:
            raise ValidationError("Cannot delete column that contains items")
        
        return board.remove_column(column_id)

    def list_board_names(self) -> List[str]:
        return self._repository.list_board_names()

    def get_or_create_sample_board(self, name: str = "default") -> Board:
        try:
            return self.get_board_by_name(name)
        except BoardNotFoundError:
            board = self._repository.create_sample_board(name)
            self._repository.save_board(board)
            return board