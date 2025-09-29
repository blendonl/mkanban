"""Branch Command Handler

CLI command handler for creating/checking out git branches based on tasks.
"""

import click
from pathlib import Path
from typing import Optional, List

from src.core.exceptions import MKanbanError, BoardNotFoundError, ItemNotFoundError
from src.core.dependency_container import DependencyContainer
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.services.branch_service import BranchService
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.domain.entities.item import Item
from src.domain.entities.board import Board


class BranchCommand:
    """Handles branch checkout operations with task state management."""

    def __init__(self, container: DependencyContainer):
        self.container = container
        self._board_service = container.get(BoardService)
        self._item_service = container.get(ItemService)
        self._branch_service = container.get(BranchService)
        self._tmux_manager = TmuxSessionManager()

    def checkout_task_branch(
        self, task_identifier: str, board_name: Optional[str]
    ) -> None:
        """Checkout or create a branch for a task and manage task states.

        Args:
            task_identifier: Task title, ID, or partial match
            board_name: Optional board name (defaults to tmux session board)
        """
        try:
            # Determine board to use
            target_board_name = self._determine_board_name(board_name)

            # Load the board
            board = self._load_board(target_board_name)

            # Find the task
            task = self._find_task(board, task_identifier)

            # Get repository path
            repo_path = self._get_repository_path(target_board_name)

            # Manage task states: move others from in-progress to to-do
            self._manage_task_states(board, task)

            # Checkout or create the branch
            branch_name = self._branch_service.format_task_title_as_branch(task.title)
            self._branch_service.checkout_or_create_branch(task.title, repo_path)

            # Save board changes
            self._board_service.save_board(board)

            click.echo(f"✓ Checked out branch: {branch_name}")
            click.echo(f"✓ Moved task '{task.title}' to in-progress")

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
            session = self._tmux_manager.get_current_session()
            if not session:
                session = self._tmux_manager.get_active_session()

            if session:
                return session.name

            raise MKanbanError("No board specified and no active tmux session found")
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
                raise MKanbanError(
                    f"Board '{board_name}' not found. Available boards: {available_list}"
                )
            else:
                raise MKanbanError(
                    f"Board '{board_name}' not found. No boards available."
                )

    def _find_task(self, board: Board, task_identifier: str) -> Item:
        """Find a task by title, ID, or partial match.

        Args:
            board: The board to search
            task_identifier: Task identifier (title, ID, or partial match)

        Returns:
            The matching Item

        Raises:
            MKanbanError: If task not found or multiple matches found
        """
        matches: List[Item] = []

        # Search all columns for matches
        for column in board.columns:
            for item in column.items:
                # Exact ID match
                if item.id == task_identifier:
                    return item

                # Exact title match (case-insensitive)
                if item.title.lower() == task_identifier.lower():
                    return item

                # Partial title match (case-insensitive)
                if task_identifier.lower() in item.title.lower():
                    matches.append(item)

        # Handle results
        if len(matches) == 0:
            raise MKanbanError(
                f"Task '{task_identifier}' not found in board '{board.name}'"
            )
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches - show options
            match_titles = [f"  - {item.title}" for item in matches]
            raise MKanbanError(
                f"Multiple tasks match '{task_identifier}':\n"
                + "\n".join(match_titles)
                + "\n\nPlease be more specific."
            )

    def _get_repository_path(self, board_name: str) -> Path:
        """Get the git repository path for the board.

        Args:
            board_name: Name of the board

        Returns:
            Path to the git repository

        Raises:
            MKanbanError: If repository path cannot be determined
        """
        # Try to get from tmux session
        try:
            repo_path = self._tmux_manager.get_active_session_repository()
            if repo_path and repo_path.exists():
                return repo_path

            repo_path = self._tmux_manager.get_active_session_repository_external()
            if repo_path and repo_path.exists():
                return repo_path
        except Exception:
            pass

        raise MKanbanError(
            f"Could not determine git repository path for board '{board_name}'. "
            "Make sure you're in a tmux session within a git repository."
        )

    def _manage_task_states(self, board: Board, selected_task: Item) -> None:
        """Manage task states: move all in-progress to to-do, move selected to in-progress.

        Args:
            board: The board containing the tasks
            selected_task: The task to move to in-progress
        """
        # Find the "to-do" and "in-progress" columns
        todo_column = None
        in_progress_column = None

        for column in board.columns:
            if column.name.lower() == "to-do":
                todo_column = column
            elif column.name.lower() == "in-progress":
                in_progress_column = column

        if not todo_column:
            raise MKanbanError("Could not find 'to-do' column in board")

        if not in_progress_column:
            raise MKanbanError("Could not find 'in-progress' column in board")

        # Move all tasks from in-progress to to-do
        tasks_to_move = list(in_progress_column.items)  # Create a copy to avoid modification during iteration
        for task in tasks_to_move:
            if task.id != selected_task.id:
                self._item_service.move_item_between_columns(
                    board, task.id, todo_column.id
                )

        # Move selected task to in-progress (if not already there)
        if selected_task.column_id != in_progress_column.id:
            self._item_service.move_item_between_columns(
                board, selected_task.id, in_progress_column.id
            )