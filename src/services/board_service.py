from typing import List, Optional

from src.core.exceptions import BoardNotFoundError, ValidationError
from src.core.types import BoardId, ColumnId
from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.repositories.board_repository import BoardRepository
from src.services.validation_service import ValidationService
from src.utils.logger_factory import ContextAwareLogger


class BoardService:
    def __init__(
        self,
        board_repository: BoardRepository,
        validation_service: ValidationService,
        logger: ContextAwareLogger,
    ):
        self._repository = board_repository
        self._validator = validation_service
        self._logger = logger

    def get_all_boards(self) -> List[Board]:
        return self._repository.load_all_boards()

    def get_board_by_id(self, board_id: BoardId) -> Board:
        self._logger.debug("Loading board by id", board=board_id)
        board = self._repository.load_board_by_id(board_id)
        if not board:
            self._logger.warning("Board not found", board=board_id)
            raise BoardNotFoundError(f"Board with id '{board_id}' not found")
        self._logger.info("Successfully loaded board", board=board.name)
        return board

    def get_board_by_name(self, board_name: str) -> Board:
        self._logger.debug("Loading board by name", board=board_name)
        board = self._repository.load_board_by_name(board_name)
        if not board:
            self._logger.warning("Board not found", board=board_name)
            raise BoardNotFoundError(f"Board with name '{board_name}' not found")
        self._logger.info("Successfully loaded board", board=board_name)
        return board

    def create_board(self, name: str, description: str = "") -> Board:
        self._logger.info("Creating new board", board=name)
        self._validator.validate_board_name(name)

        existing_board = self._repository.load_board_by_name(name)
        if existing_board:
            self._logger.warning("Board already exists", board=name)
            raise ValidationError("Board with name '{name}' already exists")

        board = Board(name=name, description=description)
        self._repository.save_board(board)
        self._logger.info("Successfully created board", board=name)
        return board

    def save_board(self, board: Board) -> None:
        self._logger.debug("Saving board", board=board.name)
        self._validator.validate_board(board)
        self._repository.save_board(board)
        self._logger.info("Successfully saved board", board=board.name)

    def delete_board(self, board_id: BoardId) -> bool:
        return self._repository.delete_board(board_id)

    def add_column_to_board(
        self, board: Board, column_name: str, position: Optional[int] = None
    ) -> Column:
        self._logger.info(
            "Adding column to board", board=board.name, column=column_name
        )
        self._validator.validate_column_name(column_name)

        for existing_column in board.columns:
            if existing_column.name.lower() == column_name.lower():
                self._logger.warning(
                    "Column already exists", board=board.name, column=column_name
                )
                raise ValidationError("Column '{column_name}' already exists in board")

        column = board.add_column(column_name, position)
        self._logger.info(
            "Successfully added column", board=board.name, column=column_name
        )
        return column

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
