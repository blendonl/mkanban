from typing import Optional, Dict, Any
from pydantic import BaseModel
from src.core.types import Timestamp


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