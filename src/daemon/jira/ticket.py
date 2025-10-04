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

        # Hierarchy fields
        self.subtasks = self._parse_subtasks(fields.get("subtasks", []))
        self.parent = self._parse_parent(fields.get("parent"))
        self.epic_link = fields.get("customfield_10014") or fields.get("epic")  # Epic link custom field

        # Issue links
        self.issue_links = self._parse_issue_links(fields.get("issuelinks", []))

        # Sprint information
        self.sprint = self._parse_sprint(fields.get("sprint") or fields.get("customfield_10020"))

        # Story points (common custom field IDs)
        self.story_points = self._parse_story_points(fields)

        # Versions
        self.fix_versions = [v.get("name", "") for v in fields.get("fixVersions", [])]
        self.affects_versions = [v.get("name", "") for v in fields.get("versions", [])]

        # Check if this is a subtask
        self.is_subtask = fields.get("issuetype", {}).get("subtask", False)

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

    def _parse_subtasks(self, subtasks_data: List[Dict[str, Any]]) -> List[str]:
        """Parse subtasks list to get ticket keys"""
        return [st.get("key", "") for st in subtasks_data if st.get("key")]

    def _parse_parent(self, parent_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Parse parent ticket data to get parent key"""
        if not parent_data:
            return None
        return parent_data.get("key")

    def _parse_issue_links(self, links_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Parse issue links"""
        links = []
        for link in links_data:
            link_type = link.get("type", {}).get("name", "")
            # Determine direction and linked issue
            if "outwardIssue" in link:
                linked_issue = link["outwardIssue"]
                direction = "outward"
                relation = link.get("type", {}).get("outward", "relates to")
            elif "inwardIssue" in link:
                linked_issue = link["inwardIssue"]
                direction = "inward"
                relation = link.get("type", {}).get("inward", "relates to")
            else:
                continue

            links.append({
                "key": linked_issue.get("key", ""),
                "type": link_type,
                "relation": relation,
                "direction": direction,
                "status": linked_issue.get("fields", {}).get("status", {}).get("name", "")
            })
        return links

    def _parse_sprint(self, sprint_data: Any) -> Optional[str]:
        """Parse sprint information"""
        if not sprint_data:
            return None
        # Sprint can be a dict or a list of dicts or a string
        if isinstance(sprint_data, dict):
            return sprint_data.get("name")
        elif isinstance(sprint_data, list) and sprint_data:
            # Get the active sprint (usually the last one)
            return sprint_data[-1].get("name") if isinstance(sprint_data[-1], dict) else None
        elif isinstance(sprint_data, str):
            # Some JIRA instances return sprint as a complex string
            import re
            match = re.search(r'name=([^,\]]+)', sprint_data)
            return match.group(1) if match else None
        return None

    def _parse_story_points(self, fields: Dict[str, Any]) -> Optional[float]:
        """Parse story points from common custom field locations"""
        # Common custom field IDs for story points
        story_point_fields = [
            "customfield_10016",  # Common in Jira Cloud
            "customfield_10026",  # Common in Jira Server
            "customfield_10002",  # Another common field
            "story_points",       # Direct field name (some instances)
        ]

        for field_name in story_point_fields:
            value = fields.get(field_name)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
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
            # Hierarchy fields
            "subtasks": self.subtasks,
            "parent": self.parent,
            "epic_link": self.epic_link,
            "is_subtask": self.is_subtask,
            # Links and relationships
            "issue_links": self.issue_links,
            # Sprint and planning
            "sprint": self.sprint,
            "story_points": self.story_points,
            # Versions
            "fix_versions": self.fix_versions,
            "affects_versions": self.affects_versions,
        }

    def has_subtasks(self) -> bool:
        """Check if ticket has subtasks"""
        return len(self.subtasks) > 0

    def has_parent(self) -> bool:
        """Check if ticket has a parent"""
        return self.parent is not None

    def has_epic(self) -> bool:
        """Check if ticket is linked to an epic"""
        return self.epic_link is not None

    def get_linked_ticket_keys(self) -> List[str]:
        """Get all linked ticket keys"""
        return [link["key"] for link in self.issue_links]