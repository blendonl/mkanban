from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from enum import Enum


class GitEventType(Enum):
    BRANCH_CREATED = "branch_created"
    BRANCH_DELETED = "branch_deleted"
    BRANCH_SWITCHED = "branch_switched"
    COMMIT_CREATED = "commit_created"
    REPOSITORY_STATE_CHANGED = "repository_state_changed"


@dataclass
class GitEvent:
    """Represents a Git event (branch creation, deletion, etc.)"""

    event_type: GitEventType
    repository_path: Path
    branch_name: Optional[str] = None
    previous_branch: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    timestamp: Optional[str] = None

    def __str__(self) -> str:
        return f"GitEvent({self.event_type.value}, {self.repository_path.name}, {self.branch_name})"