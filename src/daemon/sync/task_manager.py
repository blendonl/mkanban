"""Task Manager

Handles kanban task operations including creation, updates, and movement
between columns for git-managed tasks.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.daemon.core.configuration_service import ConfigurationService
from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.services.board_service import BoardService
from src.services.validation_service import ValidationService
from src.core.dependency_container import get_container
from src.infrastructure.git.repository import GitOperations
from src.utils.string_utils import get_safe_filename


class TaskManager:
    """Manages kanban tasks for git synchronization"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize required services with current configuration"""
        settings = self.config_service.settings
        board_name = self.config_service.get_board_name()

        self.logger.debug(f"[{board_name}] TaskManager initializing services")

        # Initialize services using DI container
        container = get_container()
        self.board_service = container.get(BoardService)

        self.logger.debug(f"[{board_name}] TaskManager services initialized")

    async def reinitialize_for_session(self, session_name: str) -> None:
        """Reinitialize services for a new session"""
        board_name = self.config_service.get_board_name()
        self.logger.info(f"[{board_name}] Reinitializing TaskManager for session: {session_name}")
        self._initialize_services()

    async def create_task(self, repository_path: Path, branch_name: str, metadata: Dict[str, Any]) -> Optional[Item]:
        """Create a new git task"""
        board_name = self.config_service.get_board_name()
        repo_name = repository_path.name

        self.logger.info(
            f"[{board_name}] Creating task for branch '{branch_name}' in {repo_name}"
        )

        try:
            # Check if task already exists
            existing_task = self._find_git_task(repository_path, branch_name)
            if existing_task:
                self.logger.debug(
                    f"[{board_name}] Task for branch {branch_name} already exists"
                )
                return existing_task

            branch_info = metadata.get("branch_info")
            if not branch_info:
                self.logger.warning(f"[{board_name}] No branch info provided for {branch_name}")
                return None

            # Create git task as Item
            git_task = Item.from_git_branch(
                branch_name=branch_name,
                repository_path=str(repository_path),
                column_id=self.config_service.config.default_column,
                full_name=branch_info.full_name,
                last_commit_hash=branch_info.last_commit_hash,
                last_commit_message=branch_info.last_commit_message,
                last_commit_author=branch_info.last_commit_author,
                last_commit_date=branch_info.last_commit_date,
                is_current=branch_info.is_current,
            )

            self.logger.debug(
                f"[{board_name}] Created git task: {git_task.title} (ID: {git_task.id})"
            )

            # Ensure board exists
            board = await self._ensure_git_board_exists()

            # Add task to board
            self._add_git_task_to_board(board, git_task)

            self.logger.info(
                f"[{board.name}] Successfully created task '{git_task.title}' "
                f"for branch {branch_name} in {repo_name}"
            )

            return git_task

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to create task for branch {branch_name}: {e}",
                exc_info=True
            )
            return None

    async def move_task_to_progress(self, repository_path: Path, branch_name: str) -> bool:
        """Move a task to the in-progress column"""
        return await self._move_task_to_column(
            repository_path,
            branch_name,
            self.config_service.config.in_progress_column,
            "in-progress"
        )

    async def move_task_to_done(self, repository_path: Path, branch_name: str) -> bool:
        """Move a task to the done column"""
        return await self._move_task_to_column(
            repository_path,
            branch_name,
            self.config_service.config.done_column,
            "done"
        )

    async def mark_task_deleted(self, repository_path: Path, branch_name: str) -> bool:
        """Mark a task as deleted (branch deleted)"""
        git_task = self._find_git_task(repository_path, branch_name)
        if not git_task:
            return False

        board_name = self.config_service.get_board_name()

        try:
            # Mark branch as deleted
            git_task.mark_branch_deleted()

            # Move to done if auto-sync is enabled
            if git_task.should_auto_complete():
                board = await self._get_git_board()
                if board:
                    done_column = self._find_or_create_column(
                        board, self.config_service.config.done_column
                    )
                    git_task.move_to_column(done_column.id)
                    self._save_git_task_changes(board, git_task)

            self.logger.info(
                f"[{board_name}] Marked task as completed for deleted branch: {branch_name}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to mark task deleted for {branch_name}: {e}"
            )
            return False

    async def deactivate_task(self, repository_path: Path, branch_name: str) -> bool:
        """Deactivate a task (set as not current branch)"""
        git_task = self._find_git_task(repository_path, branch_name)
        if not git_task:
            return False

        board_name = self.config_service.get_board_name()

        try:
            if git_task.auto_sync_enabled:
                git_task.set_current_branch(False)

                # Move to done if it was in progress
                in_progress_column_id = get_safe_filename(self.config_service.config.in_progress_column)
                if git_task.column_id == in_progress_column_id:
                    board = await self._get_git_board()
                    if board:
                        done_column = self._find_or_create_column(
                            board, self.config_service.config.done_column
                        )
                        git_task.move_to_column(done_column.id)
                        self._save_git_task_changes(board, git_task)

            self.logger.debug(
                f"[{board_name}] Deactivated task for branch: {branch_name}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to deactivate task for {branch_name}: {e}"
            )
            return False

    async def activate_task(self, repository_path: Path, branch_name: str) -> bool:
        """Activate a task (set as current branch)"""
        git_task = self._find_git_task(repository_path, branch_name)
        if not git_task:
            # Create task if it doesn't exist
            try:
                git_ops = GitOperations(repository_path)
                branch_info = git_ops.get_branch_info(branch_name)
                if branch_info:
                    git_task = await self.create_task(
                        repository_path,
                        branch_name,
                        {"branch_info": branch_info}
                    )
            except Exception as e:
                self.logger.error(f"Failed to create task for activation: {e}")
                return False

        if not git_task:
            return False

        board_name = self.config_service.get_board_name()

        try:
            if git_task.auto_sync_enabled:
                # Mark as current branch BEFORE checking auto-activation
                git_task.set_current_branch(True)

                # Move to in-progress if should auto-activate
                if git_task.should_auto_activate():
                    board = await self._get_git_board()
                    if board:
                        progress_column = self._find_or_create_column(
                            board, self.config_service.config.in_progress_column
                        )
                        git_task.move_to_column(progress_column.id)
                        self._save_git_task_changes(board, git_task)

            self.logger.debug(
                f"[{board_name}] Activated task for branch: {branch_name}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to activate task for {branch_name}: {e}"
            )
            return False

    async def initialize_repository_tasks(self, repository_path: Path) -> List[Item]:
        """Initialize tasks for all branches in a repository"""
        tasks = []
        board_name = self.config_service.get_board_name()

        try:
            git_ops = GitOperations(repository_path)
            repo_info = git_ops.get_repository_info()

            for branch in repo_info.branches:
                if (branch.branch_type.value == "local" and
                    self.config_service.should_track_branch(branch.name)):

                    task = await self.create_task(
                        repository_path,
                        branch.name,
                        {"branch_info": branch}
                    )
                    if task:
                        tasks.append(task)

            repo_name = repository_path.name
            self.logger.info(
                f"[{board_name}] Initialized {len(tasks)} tasks for repository: {repo_name}"
            )

        except Exception as e:
            self.logger.error(f"[{board_name}] Failed to initialize repository tasks: {e}")

        return tasks

    async def get_all_in_progress_tasks(self) -> List[Item]:
        """Get all tasks currently in the in-progress column"""
        try:
            board = await self._get_git_board()
            if not board:
                return []

            in_progress_column_id = get_safe_filename(self.config_service.config.in_progress_column)

            for column in board.columns:
                if column.id == in_progress_column_id:
                    return [item for item in column.items if item.is_git_managed]

            return []

        except Exception as e:
            board_name = self.config_service.get_board_name()
            self.logger.error(f"[{board_name}] Failed to get in-progress tasks: {e}")
            return []

    async def move_all_in_progress_to_done(self) -> int:
        """Move all in-progress tasks to done column. Returns count of moved tasks."""
        board_name = self.config_service.get_board_name()
        moved_count = 0

        try:
            in_progress_tasks = await self.get_all_in_progress_tasks()

            for task in in_progress_tasks:
                if task.git_metadata and task.git_metadata.repository_path:
                    repository_path = Path(task.git_metadata.repository_path)
                    success = await self.move_task_to_done(
                        repository_path,
                        task.git_metadata.branch_name
                    )
                    if success:
                        moved_count += 1
                        self.logger.debug(
                            f"[{board_name}] Moved task '{task.title}' from in-progress to done"
                        )

            if moved_count > 0:
                self.logger.info(f"[{board_name}] Moved {moved_count} tasks from in-progress to done")

        except Exception as e:
            self.logger.error(f"[{board_name}] Failed to move in-progress tasks to done: {e}")

        return moved_count

    async def find_or_create_and_activate_task(self, repository_path: Path, branch_name: str) -> Optional[Item]:
        """Find existing task or create new one and move to in-progress"""
        board_name = self.config_service.get_board_name()

        try:
            # Check if task already exists
            existing_task = self._find_git_task(repository_path, branch_name)

            if existing_task:
                # Check if already in progress
                in_progress_column_id = get_safe_filename(self.config_service.config.in_progress_column)
                if existing_task.column_id == in_progress_column_id:
                    self.logger.debug(f"[{board_name}] Task '{existing_task.title}' is already in-progress")
                    return existing_task

                # Move to in-progress
                success = await self.move_task_to_progress(repository_path, branch_name)
                if success:
                    self.logger.info(f"[{board_name}] Moved existing task '{existing_task.title}' to in-progress")
                    return existing_task
                else:
                    self.logger.warning(f"[{board_name}] Failed to move existing task to in-progress")
                    return None

            else:
                # Create new task
                git_ops = GitOperations(repository_path)
                branch_info = git_ops.get_branch_info(branch_name)

                if not branch_info:
                    self.logger.warning(f"[{board_name}] Could not get branch info for {branch_name}")
                    return None

                # Mark as current branch
                branch_info.is_current = True

                new_task = await self.create_task(
                    repository_path,
                    branch_name,
                    {"branch_info": branch_info}
                )

                if new_task:
                    # Move to in-progress
                    success = await self.move_task_to_progress(repository_path, branch_name)
                    if success:
                        self.logger.info(
                            f"[{board_name}] Created and moved new task '{new_task.title}' to in-progress"
                        )
                        return new_task
                    else:
                        self.logger.warning(f"[{board_name}] Created task but failed to move to in-progress")
                        return new_task

                return None

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Error in find_or_create_and_activate_task for {branch_name}: {e}",
                exc_info=True
            )
            return None

    async def _move_task_to_column(self, repository_path: Path, branch_name: str, column_name: str, friendly_name: str) -> bool:
        """Move a task to a specific column"""
        git_task = self._find_git_task(repository_path, branch_name)
        if not git_task:
            return False

        board_name = self.config_service.get_board_name()

        try:
            board = await self._get_git_board()
            if board:
                target_column = self._find_or_create_column(board, column_name)
                git_task.move_to_column(target_column.id)
                self._save_git_task_changes(board, git_task)

                self.logger.debug(
                    f"[{board_name}] Moved task '{git_task.title}' to {friendly_name}"
                )
                return True

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to move task to {friendly_name}: {e}"
            )

        return False

    def _find_git_task(self, repository_path: Path, branch_name: str) -> Optional[Item]:
        """Find git task by repository and branch"""
        try:
            board_name = self.config_service.get_board_name()
            board = self.board_service.get_board_by_name(board_name)

            for column in board.columns:
                for item in column.items:
                    if (item.is_git_managed and
                        item.git_metadata and
                        item.git_metadata.repository_path == str(repository_path) and
                        item.git_metadata.branch_name == branch_name):
                        return item

            return None

        except Exception as e:
            board_name = self.config_service.get_board_name()
            self.logger.debug(
                f"[{board_name}] Could not find git task for {repository_path}:{branch_name}: {e}"
            )
            return None

    async def _ensure_git_board_exists(self) -> Board:
        """Ensure the git board exists with all required columns"""
        board_name = self.config_service.get_board_name()

        try:
            board = self.board_service.get_board_by_name(board_name)
            self.logger.debug(f"[{board_name}] Found existing git board")

            # Ensure required columns exist
            self._ensure_required_columns(board)
            return board

        except Exception:
            self.logger.info(f"[{board_name}] Creating new git board")

            # Create the board
            board = self.board_service.create_board(
                name=board_name,
                description="Automatically managed tasks based on git branches",
            )

            # Add default columns
            config = self.config_service.config
            board.add_column(config.default_column, 0)
            board.add_column(config.in_progress_column, 1)
            board.add_column(config.done_column, 2)

            self.board_service.save_board(board)
            self.logger.info(f"[{board_name}] Created git board with default columns")
            return board

    def _ensure_required_columns(self, board: Board) -> None:
        """Ensure board has all required columns"""
        config = self.config_service.config
        required_columns = [
            (config.default_column, 0),
            (config.in_progress_column, 1),
            (config.done_column, 2),
        ]

        board_modified = False
        for column_name, intended_position in required_columns:
            column_id = get_safe_filename(column_name)

            column_exists = any(
                col.id == column_id or col.name.lower() == column_name.lower()
                for col in board.columns
            )

            if not column_exists:
                existing_positions = {
                    col.position for col in board.columns
                    if col.position is not None
                }

                position = intended_position
                while position in existing_positions:
                    position += 1

                board.add_column(column_name, position)
                board_modified = True

        if board_modified:
            self.board_service.save_board(board)

    async def _get_git_board(self) -> Optional[Board]:
        """Get the current git board"""
        try:
            board_name = self.config_service.get_board_name()
            return self.board_service.get_board_by_name(board_name)
        except:
            return None

    def _find_or_create_column(self, board: Board, column_name: str) -> Column:
        """Find or create a column in the board"""
        target_column_id = get_safe_filename(column_name)

        # First, look for exact name match
        for column in board.columns:
            if column.name.lower() == column_name.lower():
                return column

        # Then, look for ID match
        for column in board.columns:
            if column.id == target_column_id:
                return column

        # Create new column
        max_position = max(
            (col.position for col in board.columns if col.position is not None),
            default=-1
        )
        return board.add_column(column_name, max_position + 1)

    def _add_git_task_to_board(self, board: Board, git_task: Item) -> None:
        """Add a git task to the appropriate column in the board"""
        try:
            # Find target column
            target_column = None
            for column in board.columns:
                if column.id == git_task.column_id:
                    target_column = column
                    break

            if not target_column:
                target_column = self._find_or_create_column(
                    board, self.config_service.config.default_column
                )
                git_task.column_id = target_column.id

            # Add item to column
            target_column.items.append(git_task)

            # Save board
            self.board_service.save_board(board)

        except Exception as e:
            self.logger.error(f"Failed to add git task to board: {e}", exc_info=True)
            raise

    def _save_git_task_changes(self, board: Board, git_task: Item) -> None:
        """Save changes to a git task"""
        # Remove task from its old location
        for column in board.columns:
            for i, item in enumerate(column.items):
                if item.id == git_task.id:
                    column.items.pop(i)
                    break

        # Add task to correct column
        target_column = None
        for column in board.columns:
            if column.id == git_task.column_id:
                target_column = column
                break

        if not target_column:
            column_name = git_task.column_id.replace("-", " ").title()
            target_column = self._find_or_create_column(board, column_name)
            git_task.column_id = target_column.id

        target_column.items.append(git_task)

        # Save board
        self.board_service.save_board(board)