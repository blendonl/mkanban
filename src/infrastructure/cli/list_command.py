import click
from typing import List, Optional
from src.core.exceptions import MKanbanError, BoardNotFoundError
from src.core.dependency_container import DependencyContainer
from src.services.board_service import BoardService
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.domain.entities.item import Item
from src.domain.entities.board import Board


class ListCommand:
    def __init__(self, container: DependencyContainer):
        self.container = container
        self._board_service = container.get(BoardService)
        self._tmux_manager = TmuxSessionManager()

    def list_tasks(self, board_name: Optional[str], columns: Optional[str]) -> None:
        """List tasks from the specified board and columns."""
        try:
            # Determine board to use
            target_board_name = self._determine_board_name(board_name)

            # Load the board
            board = self._load_board(target_board_name)

            # Parse and validate columns
            target_columns = self._parse_columns(columns, board)

            # Get tasks from specified columns
            tasks = self._get_tasks_from_columns(board, target_columns)

            # Output tasks (one per line, title only)
            self._output_tasks(tasks)

        except MKanbanError as e:
            click.echo(f"Error: {e}", err=True)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)

    def _determine_board_name(self, board_name: Optional[str]) -> str:
        """Determine which board to use - explicit name or tmux session fallback."""
        if board_name:
            return board_name

        # Try to get board from tmux session
        try:
            session = self._tmux_manager.get_active_session()
            return session.name
        except Exception:
            raise MKanbanError("No board specified and no active tmux session found")

    def _load_board(self, board_name: str) -> Board:
        """Load the specified board."""
        try:
            return self._board_service.get_board_by_name(board_name)
        except BoardNotFoundError:
            available_boards = self._board_service.list_board_names()
            if available_boards:
                available_list = ", ".join(available_boards)
                raise MKanbanError(f"Board '{board_name}' not found. Available boards: {available_list}")
            else:
                raise MKanbanError(f"Board '{board_name}' not found. No boards available.")

    def _parse_columns(self, columns: Optional[str], board: Board) -> List[str]:
        """Parse the columns parameter and validate against board columns."""
        if not columns:
            # Return all column names if no filter specified
            return [col.name for col in board.columns]

        # Parse comma-separated column names
        requested_columns = [col.strip() for col in columns.split(",")]
        board_column_names = [col.name for col in board.columns]

        # Validate that requested columns exist
        invalid_columns = [col for col in requested_columns if col not in board_column_names]
        if invalid_columns:
            available_list = ", ".join(board_column_names)
            invalid_list = ", ".join(invalid_columns)
            raise MKanbanError(f"Invalid columns: {invalid_list}. Available columns: {available_list}")

        return requested_columns

    def _get_tasks_from_columns(self, board: Board, target_columns: List[str]) -> List[Item]:
        """Get all tasks from the specified columns."""
        tasks = []
        for column in board.columns:
            if column.name in target_columns:
                tasks.extend(column.items)
        return tasks

    def _output_tasks(self, tasks: List[Item]) -> None:
        """Output tasks in a format suitable for piping to external tools."""
        for task in tasks:
            # Output just the title, one per line
            click.echo(task.title)