"""Session Task Coordinator

Orchestrates task status changes when tmux sessions are switched,
handling the transition of tasks between columns based on session context.
"""

import logging
from pathlib import Path
from typing import Optional, List

from daemon.core.session_context_manager import SessionContext
from daemon.core.configuration_service import ConfigurationService
from daemon.sync.task_manager import TaskManager
from infrastructure.git.repository import GitOperations
from infrastructure.tmux.session_manager import TmuxSessionManager
from utils.string_utils import get_safe_filename


class SessionTaskCoordinator:
    """Coordinates task status changes based on tmux session switches"""

    def __init__(self, config_service: ConfigurationService, task_manager: TaskManager):
        self.config_service = config_service
        self.task_manager = task_manager
        self.tmux_manager = TmuxSessionManager()
        self.logger = logging.getLogger("mkanban-daemon")

    async def handle_session_switch(self, old_context: SessionContext, new_context: SessionContext) -> None:
        """Handle a tmux session switch by managing task status transitions"""
        board_name = self.config_service.get_board_name()

        # Check if session-based task management is enabled
        if not self.config_service.is_session_task_management_enabled():
            self.logger.debug(f"[{board_name}] Session-based task management is disabled")
            return

        self.logger.info(
            f"[{board_name}] Handling session switch: {old_context.session_name} -> {new_context.session_name}"
        )

        try:
            # Step 1: Move any current in-progress task to done (if enabled)
            if self.config_service.should_auto_complete_on_session_switch():
                await self._complete_current_in_progress_task()

            # Step 2: Activate task for the new session (if enabled)
            if self.config_service.should_auto_activate_on_session_switch():
                await self._activate_task_for_session(new_context)

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Error handling session switch: {e}",
                exc_info=True
            )

    async def _complete_current_in_progress_task(self) -> None:
        """Move any currently in-progress task to done column"""
        board_name = self.config_service.get_board_name()

        try:
            # Get the current board
            board = await self.task_manager._get_git_board()
            if not board:
                self.logger.debug(f"[{board_name}] No git board found")
                return

            # Find tasks in the in-progress column
            in_progress_column_id = get_safe_filename(self.config_service.config.in_progress_column)
            in_progress_tasks = []

            for column in board.columns:
                if column.id == in_progress_column_id:
                    in_progress_tasks = [item for item in column.items if item.is_git_managed]
                    break

            if not in_progress_tasks:
                self.logger.debug(f"[{board_name}] No in-progress tasks to complete")
                return

            # Move all in-progress tasks to done
            for task in in_progress_tasks:
                if task.git_metadata and task.git_metadata.repository_path:
                    repository_path = Path(task.git_metadata.repository_path)
                    success = await self.task_manager.move_task_to_done(
                        repository_path,
                        task.git_metadata.branch_name
                    )
                    if success:
                        self.logger.info(
                            f"[{board_name}] Moved task '{task.title}' from in-progress to done"
                        )

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Error completing in-progress tasks: {e}",
                exc_info=True
            )

    async def _activate_task_for_session(self, context: SessionContext) -> None:
        """Activate the appropriate task for the new session"""
        board_name = self.config_service.get_board_name()

        if not context.repository_path:
            self.logger.debug(f"[{board_name}] No repository path for session {context.session_name}")
            return

        try:
            # Get the current branch in this session's repository
            git_ops = GitOperations(context.repository_path)
            current_branch = git_ops.get_current_branch()

            if not current_branch:
                self.logger.debug(
                    f"[{board_name}] No current branch in repository {context.repository_path.name}"
                )
                return

            # Skip branches that shouldn't be tracked
            if not self.config_service.should_track_branch(current_branch):
                self.logger.debug(
                    f"[{board_name}] Branch {current_branch} is filtered out by configuration"
                )
                return

            # Find existing task for this branch
            existing_task = self.task_manager._find_git_task(context.repository_path, current_branch)

            if existing_task:
                # Check if task is already in-progress
                in_progress_column_id = get_safe_filename(self.config_service.config.in_progress_column)
                if existing_task.column_id == in_progress_column_id:
                    self.logger.debug(
                        f"[{board_name}] Task '{existing_task.title}' is already in-progress"
                    )
                    return

                # Move existing task to in-progress
                success = await self.task_manager.move_task_to_progress(
                    context.repository_path,
                    current_branch
                )
                if success:
                    self.logger.info(
                        f"[{board_name}] Moved task '{existing_task.title}' to in-progress "
                        f"for session {context.session_name}"
                    )
            else:
                # Create new task and move to in-progress
                branch_info = git_ops.get_branch_info(current_branch)
                if branch_info:
                    # Mark as current branch
                    branch_info.is_current = True

                    new_task = await self.task_manager.create_task(
                        context.repository_path,
                        current_branch,
                        {"branch_info": branch_info}
                    )

                    if new_task:
                        # Move to in-progress
                        success = await self.task_manager.move_task_to_progress(
                            context.repository_path,
                            current_branch
                        )
                        if success:
                            self.logger.info(
                                f"[{board_name}] Created and moved new task '{new_task.title}' "
                                f"to in-progress for session {context.session_name}"
                            )

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Error activating task for session {context.session_name}: {e}",
                exc_info=True
            )

    async def _get_session_repository_and_branch(self, session_name: str) -> Optional[tuple[Path, str]]:
        """Get the repository path and current branch for a specific session"""
        try:
            # Get repository path for the session
            repository_path = None
            sessions = self.tmux_manager.list_all_sessions()

            for session in sessions:
                if session.name == session_name:
                    # Get working directory for this session
                    working_dir = self.tmux_manager.get_session_working_directory(session_name)
                    if working_dir:
                        # Find git repository
                        current_path = working_dir
                        while current_path != current_path.parent:
                            if (current_path / ".git").exists():
                                repository_path = current_path
                                break
                            current_path = current_path.parent
                    break

            if not repository_path:
                return None

            # Get current branch
            git_ops = GitOperations(repository_path)
            current_branch = git_ops.get_current_branch()

            if not current_branch:
                return None

            return repository_path, current_branch

        except Exception as e:
            self.logger.error(f"Error getting repository/branch for session {session_name}: {e}")
            return None