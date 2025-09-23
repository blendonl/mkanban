from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class BranchType(Enum):
    LOCAL = "local"
    REMOTE = "remote"
    TRACKING = "tracking"


@dataclass
class GitBranch:
    """Represents a Git branch"""

    name: str
    full_name: str
    branch_type: BranchType
    is_current: bool = False
    upstream: Optional[str] = None
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[str] = None