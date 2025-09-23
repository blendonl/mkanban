import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime

from src.infrastructure.git.repository import GitOperations
from .event_types import GitEvent, GitEventType
from .repository_state import RepositoryState


class GitMonitor:
    """Monitors Git repositories for changes and emits events"""

    def __init__(self, polling_interval: int = 5):
        self.polling_interval = polling_interval
        self.repositories: Dict[Path, RepositoryState] = {}
        self.event_handlers: List[Callable[[GitEvent], None]] = []
        self.logger = logging.getLogger("mkanban-daemon")
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def add_repository(self, repo_path: Path) -> bool:
        """Add a repository to monitor"""
        try:
            git_ops = GitOperations(repo_path)
            if not git_ops.is_git_repository():
                self.logger.warning(f"Path is not a git repository: {repo_path}")
                return False

            # Initialize repository state
            current_branch = git_ops.get_current_branch()
            branches = set(git_ops.get_local_branches())

            # Get latest commit info if available
            commit_hash = None
            commit_message = None
            commit_author = None
            commit_date = None

            if current_branch:
                branch_info = git_ops.get_branch_info(current_branch)
                if branch_info:
                    commit_hash = branch_info.last_commit_hash
                    commit_message = branch_info.last_commit_message
                    commit_author = branch_info.last_commit_author
                    commit_date = branch_info.last_commit_date

            state = RepositoryState(
                path=repo_path,
                current_branch=current_branch,
                branches=branches,
                last_commit_hash=commit_hash,
                last_commit_message=commit_message,
                last_commit_author=commit_author,
                last_commit_date=commit_date,
            )

            self.repositories[repo_path] = state
            self.logger.info(f"Added repository to monitor: {repo_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add repository {repo_path}: {e}")
            return False

    def remove_repository(self, repo_path: Path):
        """Remove a repository from monitoring"""
        if repo_path in self.repositories:
            del self.repositories[repo_path]
            self.logger.info(f"Removed repository from monitoring: {repo_path}")

    def add_event_handler(self, handler: Callable[[GitEvent], None]):
        """Add an event handler function"""
        self.event_handlers.append(handler)

    def _emit_event(self, event: GitEvent):
        """Emit an event to all registered handlers"""
        self.logger.debug(f"Emitting git event: {event}")
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in git event handler: {e}")

    async def _check_repository(self, repo_path: Path, state: RepositoryState):
        """Check a single repository for changes"""
        try:
            git_ops = GitOperations(repo_path)

            # Get current repository state
            current_branch = git_ops.get_current_branch()
            current_branches = set(git_ops.get_local_branches())

            # Check for branch switch
            if state.has_branch_switch(current_branch):
                self._emit_event(
                    GitEvent(
                        event_type=GitEventType.BRANCH_SWITCHED,
                        repository_path=repo_path,
                        branch_name=current_branch,
                        previous_branch=state.current_branch,
                        timestamp=datetime.now().isoformat(),
                    )
                )

            # Check for branch changes
            if state.has_branch_changes(current_branches):
                added_branches = state.get_added_branches(current_branches)
                deleted_branches = state.get_deleted_branches(current_branches)

                for branch in added_branches:
                    self._emit_event(
                        GitEvent(
                            event_type=GitEventType.BRANCH_CREATED,
                            repository_path=repo_path,
                            branch_name=branch,
                            timestamp=datetime.now().isoformat(),
                        )
                    )

                for branch in deleted_branches:
                    self._emit_event(
                        GitEvent(
                            event_type=GitEventType.BRANCH_DELETED,
                            repository_path=repo_path,
                            branch_name=branch,
                            timestamp=datetime.now().isoformat(),
                        )
                    )

            # Check for new commits on current branch
            if current_branch:
                branch_info = git_ops.get_branch_info(current_branch)
                if branch_info and state.has_new_commit(branch_info.last_commit_hash):
                    self._emit_event(
                        GitEvent(
                            event_type=GitEventType.COMMIT_CREATED,
                            repository_path=repo_path,
                            branch_name=current_branch,
                            commit_hash=branch_info.last_commit_hash,
                            commit_message=branch_info.last_commit_message,
                            timestamp=datetime.now().isoformat(),
                        )
                    )

            # Update repository state
            commit_info = {}
            if current_branch:
                branch_info = git_ops.get_branch_info(current_branch)
                if branch_info:
                    commit_info = {
                        "commit_hash": branch_info.last_commit_hash,
                        "commit_message": branch_info.last_commit_message,
                        "commit_author": branch_info.last_commit_author,
                        "commit_date": branch_info.last_commit_date,
                    }

            state.update_state(
                current_branch=current_branch,
                branches=current_branches,
                **commit_info,
            )

        except Exception as e:
            self.logger.error(f"Error checking repository {repo_path}: {e}")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Git monitor started")

        while self._running:
            try:
                # Check all repositories
                for repo_path, state in self.repositories.items():
                    await self._check_repository(repo_path, state)

                # Wait for next iteration
                await asyncio.sleep(self.polling_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in git monitor loop: {e}")
                await asyncio.sleep(self.polling_interval)

        self.logger.info("Git monitor stopped")

    async def start(self):
        """Start the git monitor"""
        if self._running:
            self.logger.warning("Git monitor is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop the git monitor"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def is_running(self) -> bool:
        """Check if the monitor is running"""
        return self._running

    def get_repository_status(self) -> Dict[str, Any]:
        """Get status of all monitored repositories"""
        return {
            str(path): {
                "current_branch": state.current_branch,
                "branch_count": len(state.branches),
                "last_checked": state.last_checked.isoformat() if state.last_checked else None,
                "last_commit": state.last_commit_hash[:7] if state.last_commit_hash else None,
            }
            for path, state in self.repositories.items()
        }

    async def handle_session_change(self, old_context, new_context) -> None:
        """Handle session context change"""
        self.logger.info(
            f"GitMonitor handling session change: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )
        # GitMonitor doesn't need to do anything special for session changes
        # since it monitors repositories globally