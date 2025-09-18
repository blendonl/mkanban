"""Task Synchronizer

Synchronizes git branch state with kanban tasks, handling creation,
updates, and status changes based on git events.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Set
from fnmatch import fnmatch

from config.settings import Settings
from domain.entities.board import Board
from domain.entities.column import Column
from domain.entities.git_task import GitTask, GitMetadata
from services.board_service import BoardService
from services.item_service import ItemService
from services.validation_service import ValidationService
from infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from domain.repositories.board_repository import BoardRepository
from domain.repositories.storage_repository import StorageRepository
from infrastructure.git.repository import GitOperations, GitBranch
from daemon.git_monitor import GitEvent, GitEventType
from daemon.service_manager import DaemonConfig


class TaskSynchronizer:
    """Synchronizes git state with kanban tasks"""
    
    def __init__(self, settings: Settings, daemon_config: DaemonConfig):
        self.daemon_config = daemon_config
        self.logger = logging.getLogger("mkanban-daemon")
        
        # Create settings with daemon data path
        self.settings = Settings(data_dir=str(daemon_config.data_path))
        
        # Initialize services
        self._initialize_services()
        
        # Track git tasks by repository and branch
        self.git_tasks: Dict[str, Dict[str, GitTask]] = {}  # repo_path -> {branch_name -> GitTask}
        
    def _initialize_services(self) -> None:
        """Initialize required services"""
        # Initialize storage and repositories
        markdown_storage = MarkdownStorageImpl(self.settings.get_data_dir())
        validation_service = ValidationService()
        
        # Initialize business services
        self.board_service = BoardService(markdown_storage, validation_service)
        self.item_service = ItemService(markdown_storage, validation_service)
        
        # Load existing git tasks
        self._load_existing_git_tasks()
    
    def _load_existing_git_tasks(self) -> None:
        """Load existing git tasks from storage"""
        try:
            boards = self.board_service.get_all_boards()
            
            for board in boards:
                for column in board.columns:
                    for item in column.items:
                        # Check if item has git metadata (is a GitTask)
                        if hasattr(item, 'git_metadata') and hasattr(item, 'is_git_managed'):
                            git_task = item  # Already a GitTask
                        elif self._is_potential_git_task(item):
                            # Convert regular item to GitTask if it looks like a branch-based task
                            git_task = self._convert_to_git_task(item)
                        else:
                            continue
                        
                        # Add to tracking
                        repo_path = git_task.git_metadata.repository_path
                        branch_name = git_task.git_metadata.branch_name
                        
                        if repo_path not in self.git_tasks:
                            self.git_tasks[repo_path] = {}
                        
                        self.git_tasks[repo_path][branch_name] = git_task
                        
        except Exception as e:
            self.logger.error(f"Failed to load existing git tasks: {e}")
    
    def _is_potential_git_task(self, item) -> bool:
        """Check if an item might be a git task based on naming patterns"""
        # Simple heuristic: if title looks like a branch name
        title_lower = item.title.lower()
        branch_patterns = ["feature", "bugfix", "hotfix", "fix", "feat"]
        return any(pattern in title_lower for pattern in branch_patterns)
    
    def _convert_to_git_task(self, item) -> Optional[GitTask]:
        """Convert a regular item to a GitTask (best effort)"""
        # This is a fallback conversion - would need more context
        # For now, skip conversion and log
        self.logger.info(f"Found potential git task but cannot convert: {item.title}")
        return None
    
    async def process_events(self, events: List[GitEvent]) -> None:
        """Process a list of git events"""
        for event in events:
            try:
                await self._process_single_event(event)
            except Exception as e:
                self.logger.error(f"Failed to process git event {event.event_type.value}: {e}")
    
    async def _process_single_event(self, event: GitEvent) -> None:
        """Process a single git event"""
        repo_path = str(event.repository_path)
        
        if event.event_type == GitEventType.BRANCH_CREATED:
            await self._handle_branch_created(repo_path, event.branch_name)
        elif event.event_type == GitEventType.BRANCH_DELETED:
            await self._handle_branch_deleted(repo_path, event.branch_name)
        elif event.event_type == GitEventType.BRANCH_SWITCHED:
            await self._handle_branch_switched(repo_path, event.branch_name, event.previous_branch)
        elif event.event_type == GitEventType.REPOSITORY_ADDED:
            await self._handle_repository_added(repo_path)
        elif event.event_type == GitEventType.REPOSITORY_REMOVED:
            await self._handle_repository_removed(repo_path)
    
    async def _handle_branch_created(self, repo_path: str, branch_name: str) -> None:
        """Handle creation of a new branch"""
        if not self._should_track_branch(branch_name):
            self.logger.debug(f"Skipping branch {branch_name} (filtered out)")
            return
        
        # Check if task already exists
        if self._get_git_task(repo_path, branch_name):
            self.logger.debug(f"Task for branch {branch_name} already exists")
            return
        
        try:
            # Get branch information
            git_ops = GitOperations(Path(repo_path))
            branch_info = git_ops.get_branch_info(branch_name)
            
            if not branch_info:
                self.logger.warning(f"Could not get info for branch {branch_name}")
                return
            
            # Create GitTask
            git_task = GitTask.from_git_branch(
                branch_name=branch_name,
                repository_path=repo_path,
                column_id=self.daemon_config.default_column,
                full_name=branch_info.full_name,
                last_commit_hash=branch_info.last_commit_hash,
                last_commit_message=branch_info.last_commit_message,
                last_commit_author=branch_info.last_commit_author,
                last_commit_date=branch_info.last_commit_date,
                is_current=branch_info.is_current
            )
            
            # Ensure board exists
            board = await self._ensure_git_board_exists()
            
            # Add task to board
            self._add_git_task_to_board(board, git_task)
            
            # Track the task
            if repo_path not in self.git_tasks:
                self.git_tasks[repo_path] = {}
            self.git_tasks[repo_path][branch_name] = git_task
            
            self.logger.info(f"Created task for new branch: {branch_name} in {Path(repo_path).name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create task for branch {branch_name}: {e}")
    
    async def _handle_branch_deleted(self, repo_path: str, branch_name: str) -> None:
        """Handle deletion of a branch"""
        git_task = self._get_git_task(repo_path, branch_name)
        if not git_task:
            return
        
        try:
            # Mark branch as deleted
            git_task.mark_branch_deleted()
            
            # Move to completed column if auto-sync is enabled
            if git_task.should_auto_complete():
                board = await self._get_git_board()
                if board:
                    done_column = self._find_or_create_column(board, self.daemon_config.done_column)
                    git_task.move_to_column(done_column.id)
                    
                    # Save changes
                    self._save_git_task_changes(board, git_task)
            
            self.logger.info(f"Marked task as completed for deleted branch: {branch_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle branch deletion for {branch_name}: {e}")
    
    async def _handle_branch_switched(self, repo_path: str, current_branch: str, previous_branch: str) -> None:
        """Handle switching between branches"""
        try:
            # Update previous branch task (if exists)
            if previous_branch:
                prev_task = self._get_git_task(repo_path, previous_branch)
                if prev_task and prev_task.auto_sync_enabled:
                    prev_task.set_current_branch(False)
                    
                    # Move to pending/backlog if it was in progress
                    if prev_task.column_id == self.daemon_config.in_progress_column:
                        board = await self._get_git_board()
                        if board:
                            todo_column = self._find_or_create_column(board, self.daemon_config.default_column)
                            prev_task.move_to_column(todo_column.id)
                            self._save_git_task_changes(board, prev_task)
            
            # Update current branch task (if exists)
            if current_branch and self._should_track_branch(current_branch):
                current_task = self._get_git_task(repo_path, current_branch)
                if current_task and current_task.auto_sync_enabled:
                    current_task.set_current_branch(True)
                    
                    # Move to in-progress
                    if current_task.should_auto_activate():
                        board = await self._get_git_board()
                        if board:
                            progress_column = self._find_or_create_column(board, self.daemon_config.in_progress_column)
                            current_task.move_to_column(progress_column.id)
                            self._save_git_task_changes(board, current_task)
                
                # If no task exists for current branch, create one
                elif not current_task:
                    await self._handle_branch_created(repo_path, current_branch)
            
            self.logger.info(f"Switched from {previous_branch} to {current_branch}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle branch switch: {e}")
    
    async def _handle_repository_added(self, repo_path: str) -> None:
        """Handle adding a new repository to monitoring"""
        try:
            git_ops = GitOperations(Path(repo_path))
            repo_info = git_ops.get_repository_info()
            
            # Create tasks for existing branches
            for branch in repo_info.branches:
                if branch.branch_type.value == "local" and self._should_track_branch(branch.name):
                    await self._handle_branch_created(repo_path, branch.name)
            
            self.logger.info(f"Initialized tasks for repository: {Path(repo_path).name}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle repository addition: {e}")
    
    async def _handle_repository_removed(self, repo_path: str) -> None:
        """Handle removing a repository from monitoring"""
        # Clean up tracking data
        if repo_path in self.git_tasks:
            del self.git_tasks[repo_path]
        
        self.logger.info(f"Removed repository from tracking: {Path(repo_path).name}")
    
    def _should_track_branch(self, branch_name: str) -> bool:
        """Check if a branch should be tracked based on configuration"""
        # Skip excluded branches
        for excluded in self.daemon_config.excluded_branches:
            if fnmatch(branch_name, excluded):
                return False
        
        # Check inclusion patterns
        if self.daemon_config.branch_patterns:
            for pattern in self.daemon_config.branch_patterns:
                if fnmatch(branch_name, pattern):
                    return True
            return False  # No patterns matched
        
        return True  # No patterns specified, track all (except excluded)
    
    def _get_git_task(self, repo_path: str, branch_name: str) -> Optional[GitTask]:
        """Get tracked git task for repository and branch"""
        return self.git_tasks.get(repo_path, {}).get(branch_name)
    
    async def _ensure_git_board_exists(self) -> Board:
        """Ensure the git branches board exists"""
        board_name = self.daemon_config.default_board
        
        try:
            return self.board_service.get_board_by_name(board_name)
        except:
            # Create the board
            board = self.board_service.create_board(
                name=board_name,
                description="Automatically managed tasks based on git branches"
            )
            
            # Add default columns
            board.add_column(self.daemon_config.default_column, 0)
            board.add_column(self.daemon_config.in_progress_column, 1) 
            board.add_column(self.daemon_config.done_column, 2)
            
            self.board_service.save_board(board)
            return board
    
    async def _get_git_board(self) -> Optional[Board]:
        """Get the git branches board"""
        try:
            return self.board_service.get_board_by_name(self.daemon_config.default_board)
        except:
            return None
    
    def _find_or_create_column(self, board: Board, column_name: str) -> Column:
        """Find or create a column in the board"""
        for column in board.columns:
            if column.name.lower() == column_name.lower():
                return column
        
        # Create new column
        return board.add_column(column_name)
    
    def _add_git_task_to_board(self, board: Board, git_task: GitTask) -> None:
        """Add a git task to the appropriate column in the board"""
        # Find target column
        target_column = None
        for column in board.columns:
            if column.id == git_task.column_id:
                target_column = column
                break
        
        if not target_column:
            target_column = self._find_or_create_column(board, self.daemon_config.default_column)
            git_task.column_id = target_column.id
        
        # Add item to column
        target_column.items.append(git_task)
        
        # Save board
        self.board_service.save_board(board)
    
    def _save_git_task_changes(self, board: Board, git_task: GitTask) -> None:
        """Save changes to a git task"""
        # Find and update the task in the board
        for column in board.columns:
            for i, item in enumerate(column.items):
                if item.id == git_task.id:
                    column.items[i] = git_task
                    break
        
        # Save board
        self.board_service.save_board(board)