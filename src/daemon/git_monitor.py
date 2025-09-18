"""Git Monitor Service

Monitors git repositories for changes in branch state and
generates events for the task synchronizer to process.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

from infrastructure.git.repository import GitOperations, GitRepository, find_git_repositories


class GitEventType(Enum):
    BRANCH_CREATED = "branch_created"
    BRANCH_DELETED = "branch_deleted"
    BRANCH_SWITCHED = "branch_switched"
    REPOSITORY_ADDED = "repository_added"
    REPOSITORY_REMOVED = "repository_removed"


@dataclass
class GitEvent:
    """Represents a git-related event"""
    event_type: GitEventType
    repository_path: Path
    branch_name: Optional[str] = None
    previous_branch: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RepositoryState:
    """Tracks the state of a git repository"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.git_ops = GitOperations(repo_path)
        self.current_branch: Optional[str] = None
        self.branches: Set[str] = set()
        self.last_check: Optional[float] = None
        
    def update_state(self) -> List[GitEvent]:
        """Update repository state and return any events that occurred"""
        events = []
        
        try:
            # Get current repository info
            repo_info = self.git_ops.get_repository_info()
            new_current_branch = repo_info.current_branch
            new_branches = {branch.name for branch in repo_info.branches if branch.branch_type.value == "local"}
            
            # Check for branch switch
            if self.current_branch != new_current_branch:
                if self.current_branch is not None:  # Skip initial state
                    events.append(GitEvent(
                        event_type=GitEventType.BRANCH_SWITCHED,
                        repository_path=self.repo_path,
                        branch_name=new_current_branch,
                        previous_branch=self.current_branch
                    ))
                self.current_branch = new_current_branch
            
            # Check for new branches
            new_branch_names = new_branches - self.branches
            for branch_name in new_branch_names:
                events.append(GitEvent(
                    event_type=GitEventType.BRANCH_CREATED,
                    repository_path=self.repo_path,
                    branch_name=branch_name
                ))
            
            # Check for deleted branches
            deleted_branch_names = self.branches - new_branches
            for branch_name in deleted_branch_names:
                events.append(GitEvent(
                    event_type=GitEventType.BRANCH_DELETED,
                    repository_path=self.repo_path,
                    branch_name=branch_name
                ))
            
            # Update state
            self.branches = new_branches
            
        except Exception as e:
            logging.getLogger("mkanban-daemon").error(
                f"Error updating repository state for {self.repo_path}: {e}"
            )
        
        return events


class GitMonitor:
    """Monitors git repositories for changes"""
    
    def __init__(self, polling_interval: int = 5, tmux_session_only: bool = True):
        self.polling_interval = polling_interval
        self.tmux_session_only = tmux_session_only
        self.logger = logging.getLogger("mkanban-daemon")
        self.repository_states: Dict[Path, RepositoryState] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Import tmux manager
        from infrastructure.tmux.session_manager import TmuxSessionManager
        self.tmux_manager = TmuxSessionManager() if tmux_session_only else None
        
    async def start(self) -> None:
        """Start monitoring git repositories"""
        if self.running:
            return
            
        self.logger.info("Starting Git monitor...")
        self.running = True
        
        # Initialize repository states
        await self._initialize_repositories()
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        self.logger.info(f"Git monitor started, watching {len(self.repository_states)} repositories")
    
    async def stop(self) -> None:
        """Stop monitoring git repositories"""
        if not self.running:
            return
            
        self.logger.info("Stopping Git monitor...")
        self.running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Git monitor stopped")
    
    async def get_events(self) -> List[GitEvent]:
        """Get pending git events"""
        events = []
        try:
            while True:
                event = self.event_queue.get_nowait()
                events.append(event)
        except asyncio.QueueEmpty:
            pass
        
        return events
    
    async def add_repository(self, repo_path: Path) -> None:
        """Add a repository to monitor"""
        repo_path = repo_path.resolve()
        
        if repo_path in self.repository_states:
            return
        
        try:
            # Verify it's a git repository
            if not GitOperations(repo_path).is_git_repository():
                self.logger.warning(f"Not a git repository: {repo_path}")
                return
            
            # Create repository state
            repo_state = RepositoryState(repo_path)
            repo_state.update_state()  # Initialize state
            
            self.repository_states[repo_path] = repo_state
            
            # Queue repository added event
            await self.event_queue.put(GitEvent(
                event_type=GitEventType.REPOSITORY_ADDED,
                repository_path=repo_path
            ))
            
            self.logger.info(f"Added repository to monitoring: {repo_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to add repository {repo_path}: {e}")
    
    async def remove_repository(self, repo_path: Path) -> None:
        """Remove a repository from monitoring"""
        repo_path = repo_path.resolve()
        
        if repo_path in self.repository_states:
            del self.repository_states[repo_path]
            
            # Queue repository removed event
            await self.event_queue.put(GitEvent(
                event_type=GitEventType.REPOSITORY_REMOVED,
                repository_path=repo_path
            ))
            
            self.logger.info(f"Removed repository from monitoring: {repo_path}")
    
    async def _initialize_repositories(self) -> None:
        """Initialize monitoring for repositories"""
        if self.tmux_session_only and self.tmux_manager:
            # Only monitor the active tmux session's repository
            active_repo = self.tmux_manager.get_active_session_repository()
            if active_repo:
                await self.add_repository(active_repo)
                self.logger.info(f"Monitoring active tmux session repository: {active_repo}")
            else:
                self.logger.info("No git repository found in active tmux session")
        else:
            # Fallback to auto-discovery
            await self._auto_discover_repositories()
    
    async def _auto_discover_repositories(self) -> None:
        """Auto-discover git repositories in common locations"""
        search_paths = [
            Path.cwd(),  # Current working directory
            Path.home() / "projects",
            Path.home() / "git",
            Path.home() / "src",
            Path.home() / "dev",
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                self.logger.info(f"Auto-discovering repositories in: {search_path}")
                repos = find_git_repositories(search_path, max_depth=2)
                for repo_path in repos:
                    await self.add_repository(repo_path)
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Check all repositories for changes
                for repo_path, repo_state in self.repository_states.items():
                    events = repo_state.update_state()
                    
                    # Queue events
                    for event in events:
                        await self.event_queue.put(event)
                        self.logger.info(
                            f"Git event: {event.event_type.value} in {repo_path} "
                            f"(branch: {event.branch_name})"
                        )
                
                # Sleep for polling interval
                await asyncio.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in git monitor loop: {e}")
                await asyncio.sleep(1)  # Short sleep on error