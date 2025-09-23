"""Git Monitor Service

Monitors git repositories for changes in branch state and
generates events for the task synchronizer to process.
"""

# Re-export all git monitoring classes for backward compatibility
from .git.event_types import GitEventType, GitEvent
from .git.repository_state import RepositoryState
from .git.monitor import GitMonitor

__all__ = [
    "GitEventType",
    "GitEvent",
    "RepositoryState",
    "GitMonitor"
]