"""Board Resolver Utility

Provides common logic for resolving board names across CLI commands.
"""

from typing import Optional
from src.core.exceptions import MKanbanError
from src.infrastructure.tmux.session_manager import TmuxSessionManager


class BoardResolver:
    """Utility class for resolving board names from explicit input or tmux session."""

    def __init__(self):
        self._tmux_manager = TmuxSessionManager()

    def determine_board_name(self, board_name: Optional[str]) -> str:
        """Determine which board to use - explicit name or tmux session fallback.

        Args:
            board_name: Optional explicit board name

        Returns:
            The resolved board name

        Raises:
            MKanbanError: If no board name provided and no active tmux session found
        """
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
