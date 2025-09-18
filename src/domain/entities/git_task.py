"""Git Task Entity

Extends the base Item entity to include git-specific metadata
for tasks that are automatically managed based on git branch state.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from domain.entities.item import Item
from core.types import ItemId, ColumnId, ParentId, Timestamp, FilePath
from utils.date_utils import now
from utils.string_utils import get_safe_filename


class GitMetadata(BaseModel):
    """Git-specific metadata for tasks"""

    repository_path: str
    branch_name: str
    branch_full_name: str
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[str] = None
    is_current_branch: bool = False
    branch_created_at: Optional[Timestamp] = None
    branch_deleted_at: Optional[Timestamp] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "repository_path": self.repository_path,
            "branch_name": self.branch_name,
            "branch_full_name": self.branch_full_name,
            "last_commit_hash": self.last_commit_hash,
            "last_commit_message": self.last_commit_message,
            "last_commit_author": self.last_commit_author,
            "last_commit_date": self.last_commit_date,
            "is_current_branch": self.is_current_branch,
            "branch_created_at": self.branch_created_at,
            "branch_deleted_at": self.branch_deleted_at,
        }


class GitTask(Item):
    """Task entity with git-specific functionality"""

    git_metadata: GitMetadata
    is_git_managed: bool = Field(default=True)
    auto_sync_enabled: bool = Field(default=True)

    def model_post_init(self, __context) -> None:
        # If no title is provided, use branch name
        if not self.title:
            self.title = self._generate_title_from_branch()

        # If no description is provided, use commit message
        if not self.description and self.git_metadata.last_commit_message:
            self.description = self.git_metadata.last_commit_message

        # Call parent post_init
        super().model_post_init(__context)

    def _generate_title_from_branch(self) -> str:
        """Generate a human-readable title from branch name"""
        branch_name = self.git_metadata.branch_name

        # Remove common prefixes
        prefixes = ["feature/", "bugfix/", "hotfix/", "fix/", "feat/"]
        for prefix in prefixes:
            if branch_name.startswith(prefix):
                branch_name = branch_name[len(prefix) :]
                break

        # Replace dashes and underscores with spaces and title case
        title = branch_name.replace("-", " ").replace("_", " ")
        return title.title()

    def update_git_metadata(self, **kwargs) -> None:
        """Update git metadata fields"""
        for key, value in kwargs.items():
            if hasattr(self.git_metadata, key):
                setattr(self.git_metadata, key, value)
        self.updated_at = now()

    def set_current_branch(self, is_current: bool) -> None:
        """Mark this task as corresponding to the current branch"""
        self.git_metadata.is_current_branch = is_current
        self.updated_at = now()

    def mark_branch_deleted(self) -> None:
        """Mark the associated branch as deleted"""
        self.git_metadata.branch_deleted_at = now()
        self.git_metadata.is_current_branch = False
        self.updated_at = now()

    def get_repository_name(self) -> str:
        """Get the repository name from the path"""
        return Path(self.git_metadata.repository_path).name

    def get_short_commit_hash(self) -> Optional[str]:
        """Get short version of commit hash"""
        if self.git_metadata.last_commit_hash:
            return self.git_metadata.last_commit_hash[:7]
        return None

    def is_branch_active(self) -> bool:
        """Check if the associated branch is still active (not deleted)"""
        return self.git_metadata.branch_deleted_at is None

    def should_auto_complete(self) -> bool:
        """Check if task should be auto-completed based on branch state"""
        # Task should be completed if branch is deleted and auto-sync is enabled
        done_column_id = get_safe_filename("done")

        return (
            self.auto_sync_enabled
            and not self.is_branch_active()
            and self.column_id != done_column_id  # Avoid moving already completed tasks
        )

    def should_auto_activate(self) -> bool:
        """Check if task should be moved to in-progress based on current branch"""
        # Task should be in-progress if it's the current branch and auto-sync is enabled
        excluded_column_ids = [
            get_safe_filename("in-progress"),
            get_safe_filename("done")
        ]

        return (
            self.auto_sync_enabled
            and self.git_metadata.is_current_branch
            and self.is_branch_active()
            and self.column_id not in excluded_column_ids
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, including git metadata"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "git_metadata": self.git_metadata.to_dict(),
                "is_git_managed": self.is_git_managed,
                "auto_sync_enabled": self.auto_sync_enabled,
            }
        )
        return base_dict

    @classmethod
    def from_git_branch(
        cls, branch_name: str, repository_path: str, column_id: ColumnId, **branch_info
    ) -> "GitTask":
        """Create a GitTask from git branch information"""
        git_metadata = GitMetadata(
            repository_path=repository_path,
            branch_name=branch_name,
            branch_full_name=branch_info.get("full_name", f"refs/heads/{branch_name}"),
            last_commit_hash=branch_info.get("last_commit_hash"),
            last_commit_message=branch_info.get("last_commit_message"),
            last_commit_author=branch_info.get("last_commit_author"),
            last_commit_date=branch_info.get("last_commit_date"),
            is_current_branch=branch_info.get("is_current", False),
            branch_created_at=now(),
        )

        return cls(
            title="",  # Will be generated in model_post_init
            column_id=column_id,
            git_metadata=git_metadata,
        )

    @classmethod
    def from_item(cls, item: Item, git_metadata: GitMetadata) -> "GitTask":
        """Convert a regular Item to a GitTask"""
        return cls(
            id=item.id,
            title=item.title,
            column_id=item.column_id,
            description=item.description,
            parent_id=item.parent_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
            file_path=item.file_path,
            git_metadata=git_metadata,
        )
