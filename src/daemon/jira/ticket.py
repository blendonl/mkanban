from typing import Dict, Any, Optional, List
from datetime import datetime


class JiraTicket:
    """Represents a Jira ticket with relevant fields"""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.key = data.get("key", "")
        self.id = data.get("id", "")

        fields = data.get("fields", {})
        self.summary = fields.get("summary") or ""
        self.description = fields.get("description") or ""
        self.status = fields.get("status", {}).get("name", "")
        self.issue_type = fields.get("issuetype", {}).get("name", "")
        self.priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else None
        self.assignee = fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else None
        self.reporter = fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else None
        self.project_key = fields.get("project", {}).get("key", "")

        # Handle labels and components
        self.labels = fields.get("labels", [])
        self.components = [comp.get("name", "") for comp in fields.get("components", [])]

        # Parse timestamps
        self.created = self._parse_timestamp(fields.get("created"))
        self.updated = self._parse_timestamp(fields.get("updated"))

        # Construct URL
        self.url = f"{data.get('self', '').split('/rest/')[0]}/browse/{self.key}" if data.get('self') else ""

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira timestamp string to datetime"""
        if not timestamp_str:
            return None
        try:
            # Jira uses ISO format with timezone
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def get_project_key(self) -> str:
        """Extract project key from ticket key"""
        if "-" in self.key:
            return self.key.split("-")[0]
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "key": self.key,
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "project_key": self.project_key,
            "labels": self.labels,
            "components": self.components,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "url": self.url,
        }