"""Session Context Manager

Unified session management for the daemon, handling tmux session detection,
changes, and repository monitoring across sessions.
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass

from infrastructure.tmux.session_manager import TmuxSessionManager


@dataclass
class SessionContext:
    """Represents the current session context"""

    session_name: str
    repository_path: Optional[Path] = None
    is_tmux_session: bool = False

    def __post_init__(self):
        """Ensure repository path is resolved if provided"""
        if self.repository_path and isinstance(self.repository_path, str):
            self.repository_path = Path(self.repository_path).resolve()


class SessionContextManager:
    """Manages session context detection and change notification"""

    def __init__(self, tmux_session_only: bool = True):
        self.tmux_session_only = tmux_session_only
        self.logger = logging.getLogger("mkanban-daemon")
        self.tmux_manager = TmuxSessionManager() if tmux_session_only else None

        # Current context state
        self._current_context: Optional[SessionContext] = None
        self._change_callbacks: list[
            Callable[[SessionContext, SessionContext], Any]
        ] = []
        self._session_switch_callbacks: list[
            Callable[[SessionContext, SessionContext], Any]
        ] = []

    @property
    def current_context(self) -> Optional[SessionContext]:
        """Get the current session context"""
        return self._current_context

    def add_change_callback(
        self, callback: Callable[[SessionContext, SessionContext], Any]
    ) -> None:
        """Add a callback to be called when session context changes"""
        self._change_callbacks.append(callback)

    def remove_change_callback(
        self, callback: Callable[[SessionContext, SessionContext], Any]
    ) -> None:
        """Remove a session change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def add_session_switch_callback(
        self, callback: Callable[[SessionContext, SessionContext], Any]
    ) -> None:
        """Add a callback specifically for tmux session switches"""
        self._session_switch_callbacks.append(callback)

    def remove_session_switch_callback(
        self, callback: Callable[[SessionContext, SessionContext], Any]
    ) -> None:
        """Remove a session switch callback"""
        if callback in self._session_switch_callbacks:
            self._session_switch_callbacks.remove(callback)

    async def initialize_context(self) -> SessionContext:
        """Initialize the session context"""
        if self.tmux_session_only and self.tmux_manager:
            context = await self._get_tmux_context()
        else:
            context = self._get_default_context()

        self._current_context = context
        self.logger.info(
            f"Initialized session context: session='{context.session_name}', "
            f"repository='{context.repository_path}', "
            f"tmux={context.is_tmux_session}"
        )

        return context

    async def check_for_changes(self) -> bool:
        """
        Check for session context changes.

        Returns True if context changed, False otherwise.
        """
        if not self.tmux_session_only or not self.tmux_manager:
            return False

        new_context = await self._get_tmux_context()

        if not self._current_context:
            # First initialization
            self._current_context = new_context
            return True

        if self._contexts_equal(self._current_context, new_context):
            return False

        # Context has changed
        old_context = self._current_context
        self._current_context = new_context

        self.logger.info(
            f"Session context changed: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )

        # Check if this is specifically a session switch
        is_session_switch = self._session_name_changed(
            old_context, new_context
        )

        # Notify general change callbacks
        await self._notify_change_callbacks(old_context, new_context)

        # Notify session switch callbacks if applicable
        if is_session_switch:
            self.logger.info(
                f"Tmux session switch detected: "
                f"{old_context.session_name} -> {new_context.session_name}"
            )
            await self._notify_session_switch_callbacks(
                old_context, new_context
            )

        return True

    async def _get_tmux_context(self) -> SessionContext:
        """Get session context from tmux"""
        try:
            active_session = self.tmux_manager.get_active_session()

            if not active_session:
                # No active tmux session
                return SessionContext(
                    session_name="git-branches",  # Default fallback
                    repository_path=None,
                    is_tmux_session=False
                )

            # Get repository for the active session
            repository_path = self.tmux_manager.get_active_session_repository_external()

            return SessionContext(
                session_name=active_session.name,
                repository_path=repository_path,
                is_tmux_session=True
            )

        except Exception as e:
            self.logger.warning(f"Error getting tmux context: {e}")
            return self._get_default_context()

    def _get_default_context(self) -> SessionContext:
        """Get default session context (non-tmux)"""
        return SessionContext(
            session_name="git-branches",
            repository_path=None,
            is_tmux_session=False
        )

    def _contexts_equal(self, context1: SessionContext, context2: SessionContext) -> bool:
        """Check if two session contexts are equal"""
        return (
            context1.session_name == context2.session_name and
            context1.repository_path == context2.repository_path and
            context1.is_tmux_session == context2.is_tmux_session
        )

    def _session_name_changed(self, old_context: SessionContext, new_context: SessionContext) -> bool:
        """Check if only the session name changed (for tmux session switches)"""
        return (
            old_context.session_name != new_context.session_name and
            old_context.is_tmux_session and
            new_context.is_tmux_session
        )

    async def _notify_change_callbacks(
        self,
        old_context: SessionContext,
        new_context: SessionContext
    ) -> None:
        """Notify all registered callbacks of context change"""
        for callback in self._change_callbacks:
            try:
                # Check if callback is async
                if hasattr(callback, '__call__'):
                    result = callback(old_context, new_context)
                    # If it returns a coroutine, await it
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                self.logger.error(f"Error in session change callback: {e}")

    async def _notify_session_switch_callbacks(
        self,
        old_context: SessionContext,
        new_context: SessionContext
    ) -> None:
        """Notify all registered session switch callbacks"""
        for callback in self._session_switch_callbacks:
            try:
                # Check if callback is async
                if hasattr(callback, '__call__'):
                    result = callback(old_context, new_context)
                    # If it returns a coroutine, await it
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                self.logger.error(f"Error in session switch callback: {e}")

    def get_repository_for_session(self, session_name: str) -> Optional[Path]:
        """Get repository path for a specific session"""
        if not self.tmux_manager:
            return None

        try:
            # Get all sessions and find the one we want
            sessions = self.tmux_manager.list_all_sessions()
            target_session = None

            for session in sessions:
                if session.name == session_name:
                    target_session = session
                    break

            if not target_session:
                return None

            # Get the working directory for this session and find git repo
            working_dir = self.tmux_manager.get_session_working_directory(session_name)
            if not working_dir:
                return None

            # Walk up to find git repository
            current_path = working_dir
            while current_path != current_path.parent:
                if (current_path / ".git").exists():
                    return current_path
                current_path = current_path.parent

            return None

        except Exception as e:
            self.logger.error(
                f"Error getting repository for session '{session_name}': {e}"
            )
            return None