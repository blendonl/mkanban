from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class JiraConfiguration:
    enabled: bool = False
    api_url: str = ""
    username: str = ""
    api_token: str = ""
    project_keys: List[str] = field(default_factory=list)
    polling_interval: int = 300
    bidirectional_sync: bool = False
    backlog_limit: int = 50
    status_mapping: Dict[str, str] = field(
        default_factory=lambda: {
            "Backlog": "backlog",
            "To Do": "to-do",
            "In Progress": "in-progress",
            "Done": "done",
        }
    )
    jql_filter: str = ""
    board_name: str = "jira-tickets"
    branch_patterns: List[str] = field(
        default_factory=lambda: [
            r".*[A-Z]+-\d+.*",
            r"[A-Z]+-\d+/.*",
            r".*/[A-Z]+-\d+.*",
        ]
    )