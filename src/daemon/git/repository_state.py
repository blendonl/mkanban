from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Optional
from datetime import datetime


@dataclass
class RepositoryState:
    """Tracks the state of a Git repository for change detection"""

    path: Path
    current_branch: Optional[str] = None
    branches: Set[str] = field(default_factory=set)
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[str] = None
    last_checked: Optional[datetime] = None

    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()

    def update_timestamp(self):
        """Update the last checked timestamp"""
        self.last_checked = datetime.now()

    def has_branch_changes(self, new_branches: Set[str]) -> bool:
        """Check if there are changes in the branch list"""
        return self.branches != new_branches

    def has_branch_switch(self, new_current_branch: Optional[str]) -> bool:
        """Check if the current branch has changed"""
        return self.current_branch != new_current_branch

    def has_new_commit(self, new_commit_hash: Optional[str]) -> bool:
        """Check if there's a new commit"""
        return self.last_commit_hash != new_commit_hash

    def get_added_branches(self, new_branches: Set[str]) -> Set[str]:
        """Get branches that were added since last check"""
        return new_branches - self.branches

    def get_deleted_branches(self, new_branches: Set[str]) -> Set[str]:
        """Get branches that were deleted since last check"""
        return self.branches - new_branches

    def update_state(
        self,
        current_branch: Optional[str],
        branches: Set[str],
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_author: Optional[str] = None,
        commit_date: Optional[str] = None,
    ):
        """Update the repository state with new information"""
        self.current_branch = current_branch
        self.branches = branches.copy()
        if commit_hash:
            self.last_commit_hash = commit_hash
        if commit_message:
            self.last_commit_message = commit_message
        if commit_author:
            self.last_commit_author = commit_author
        if commit_date:
            self.last_commit_date = commit_date
        self.update_timestamp()

    def __str__(self) -> str:
        return f"RepositoryState({self.path.name}, {self.current_branch}, {len(self.branches)} branches)"