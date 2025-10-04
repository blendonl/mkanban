"""Board Resolution Utility

Provides unified board name resolution logic across TUI and CLI commands.
Implements a clear priority chain for determining which board to use.
"""

from typing import Optional
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.core.dependency_container import get_config_manager


def determine_board_name(explicit_board: Optional[str] = None) -> str:
    """Determine which board to use with proper fallback chain.

    Priority:
    1. Explicit board parameter (--board flag) - highest priority
    2. Current tmux session name - if running in tmux
    3. Active tmux session name - if tmux is running but not in a session
    4. Default board from config - final fallback

    Args:
        explicit_board: Board name explicitly provided (e.g., via --board flag)

    Returns:
        Board name to use

    Raises:
        RuntimeError: If no board can be determined (should be rare)
    """
    # Priority 1: Explicit board parameter
    if explicit_board:
        return explicit_board

    # Priority 2 & 3: Try tmux session
    try:
        tmux_manager = TmuxSessionManager()

        # Try current session first (if we're inside tmux)
        session = tmux_manager.get_current_session()
        if session:
            return session.name

        # Try active session (if tmux is running)
        session = tmux_manager.get_active_session()
        if session:
            return session.name
    except Exception:
        # Tmux not available or error occurred, continue to fallback
        pass

    # Priority 4: Default board from config
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        default_board = config.daemon.get("default_board", "default")
        return default_board
    except Exception:
        # Config not available, use hardcoded default
        pass

    # Final fallback (should rarely reach here)
    return "default"


def determine_board_name_for_daemon(
    explicit_board: Optional[str] = None,
    session_name: Optional[str] = None
) -> str:
    """Determine board name for daemon context.

    This is a specialized version for the daemon that can use
    the session name from the daemon's session context manager.

    Args:
        explicit_board: Explicitly provided board name
        session_name: Session name from daemon's context manager

    Returns:
        Board name to use
    """
    # Priority 1: Explicit board
    if explicit_board:
        return explicit_board

    # Priority 2: Session name from daemon context
    if session_name:
        return session_name

    # Priority 3: Fall back to standard resolution
    return determine_board_name()
