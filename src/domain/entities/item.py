from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from core.types import ItemId, ColumnId, ParentId, Timestamp, FilePath
from utils.string_utils import generate_id_from_name, get_safe_filename
from utils.date_utils import now


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


class Item(BaseModel):
    id: ItemId = Field(default="")
    title: str
    column_id: ColumnId
    description: str = ""
    parent_id: Optional[ParentId] = None
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
    file_path: Optional[FilePath] = None

    # Git-specific fields (optional)
    git_metadata: Optional[GitMetadata] = None
    is_git_managed: bool = Field(default=False)
    auto_sync_enabled: bool = Field(default=True)

    def model_post_init(self, __context) -> None:
        # If this is a git task and no title is provided, generate from branch name
        if self.git_metadata and not self.title:
            self.title = self._generate_title_from_branch()

        # If no description and this is a git task with commit message, use it
        if self.git_metadata and not self.description and self.git_metadata.last_commit_message:
            self.description = self.git_metadata.last_commit_message

        if self.file_path and not self.id:
            filename = Path(self.file_path).stem
            self.id = filename
            if not self.title or self.title == filename:
                self.title = filename
        elif not self.id:
            self.id = generate_id_from_name(self.title) or "unnamed_item"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()

    def move_to_column(self, column_id: ColumnId) -> None:
        self.column_id = column_id
        self.updated_at = now()

    def set_parent(self, parent_id: Optional[ParentId]) -> None:
        self.parent_id = parent_id
        self.updated_at = now()

    @property
    def has_parent(self) -> bool:
        return self.parent_id is not None

    def _generate_title_from_branch(self) -> str:
        """Generate a human-readable title from branch name"""
        if not self.git_metadata:
            return ""

        branch_name = self.git_metadata.branch_name
        repository_path = Path(self.git_metadata.repository_path)
        repo_name = repository_path.name

        # Remove common prefixes
        prefixes = ["feature/", "bugfix/", "hotfix/", "fix/", "feat/"]
        for prefix in prefixes:
            if branch_name.startswith(prefix):
                branch_name = branch_name[len(prefix):]
                break

        # Replace dashes and underscores with spaces and title case
        title = branch_name.replace("-", " ").replace("_", " ").title()

        # Include repository name to distinguish between repos
        return f"{title} ({repo_name})"

    def update_git_metadata(self, **kwargs) -> None:
        """Update git metadata fields"""
        if not self.git_metadata:
            return

        for key, value in kwargs.items():
            if hasattr(self.git_metadata, key):
                setattr(self.git_metadata, key, value)
        self.updated_at = now()

    def set_current_branch(self, is_current: bool) -> None:
        """Mark this task as corresponding to the current branch"""
        if self.git_metadata:
            self.git_metadata.is_current_branch = is_current
            self.updated_at = now()

    def mark_branch_deleted(self) -> None:
        """Mark the associated branch as deleted"""
        if self.git_metadata:
            self.git_metadata.branch_deleted_at = now()
            self.git_metadata.is_current_branch = False
            self.updated_at = now()

    def get_repository_name(self) -> Optional[str]:
        """Get the repository name from the path"""
        if self.git_metadata:
            return Path(self.git_metadata.repository_path).name
        return None

    def get_short_commit_hash(self) -> Optional[str]:
        """Get short version of commit hash"""
        if self.git_metadata and self.git_metadata.last_commit_hash:
            return self.git_metadata.last_commit_hash[:7]
        return None

    def is_branch_active(self) -> bool:
        """Check if the associated branch is still active (not deleted)"""
        if self.git_metadata:
            return self.git_metadata.branch_deleted_at is None
        return False

    def should_auto_complete(self) -> bool:
        """Check if task should be auto-completed based on branch state"""
        done_column_id = get_safe_filename("done")

        return (
            self.is_git_managed
            and self.auto_sync_enabled
            and not self.is_branch_active()
            and self.column_id != done_column_id
        )

    def should_auto_activate(self) -> bool:
        """Check if task should be moved to in-progress based on current branch"""
        # Convert common column names to their corresponding IDs
        excluded_column_ids = [
            get_safe_filename("in-progress"),
            get_safe_filename("done")
        ]

        return (
            self.is_git_managed
            and self.auto_sync_enabled
            and self.git_metadata
            and self.git_metadata.is_current_branch
            and self.is_branch_active()
            and self.column_id not in excluded_column_ids
        )

    @classmethod
    def from_git_branch(cls, branch_name: str, repository_path: str, column_id: ColumnId, **branch_info) -> "Item":
        """Create an Item from git branch information"""
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
            is_git_managed=True,
            auto_sync_enabled=True,
        )

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "title": self.title,
            "column_id": self.column_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        # Add git-specific fields if this is a git-managed item
        if self.is_git_managed:
            result.update({
                "is_git_managed": self.is_git_managed,
                "auto_sync_enabled": self.auto_sync_enabled,
            })

            if self.git_metadata:
                result["git_metadata"] = self.git_metadata.to_dict()

        return result
