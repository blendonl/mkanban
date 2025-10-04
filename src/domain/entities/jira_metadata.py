from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from src.core.types import Timestamp


class JiraMetadata(BaseModel):
    """Jira-specific metadata for tasks"""
    ticket_key: str  # PROJ-123
    ticket_id: str   # Internal Jira ID
    ticket_url: str
    project_key: str
    issue_type: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    last_sync: Optional[Timestamp] = None
    jira_status: str = ""

    # Hierarchy fields
    parent_ticket_key: Optional[str] = None
    epic_key: Optional[str] = None
    subtask_keys: List[str] = Field(default_factory=list)
    is_subtask: bool = False

    # Issue links
    issue_links: List[Dict[str, str]] = Field(default_factory=list)

    # Sprint and planning
    sprint_name: Optional[str] = None
    story_points: Optional[float] = None

    # Versions
    fix_versions: List[str] = Field(default_factory=list)
    affects_versions: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "ticket_key": self.ticket_key,
            "ticket_id": self.ticket_id,
            "ticket_url": self.ticket_url,
            "project_key": self.project_key,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "labels": self.labels,
            "components": self.components,
            "last_sync": self.last_sync,
            "jira_status": self.jira_status,
            # Hierarchy fields
            "parent_ticket_key": self.parent_ticket_key,
            "epic_key": self.epic_key,
            "subtask_keys": self.subtask_keys,
            "is_subtask": self.is_subtask,
            # Issue links
            "issue_links": self.issue_links,
            # Sprint and planning
            "sprint_name": self.sprint_name,
            "story_points": self.story_points,
            # Versions
            "fix_versions": self.fix_versions,
            "affects_versions": self.affects_versions,
        }