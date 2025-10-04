from typing import Dict, List
from dataclasses import dataclass, field


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

    # Hierarchy and filtering options
    include_subtasks: bool = True
    include_epics: bool = True
    fetch_strategy: str = "assigned"  # "assigned" | "all_in_projects" | "custom_jql"
    max_hierarchy_depth: int = 2

    # Subtask handling
    subtask_column_strategy: str = "same_as_jira"  # "same_as_parent" | "same_as_jira" | "custom"
    move_subtasks_with_parent: bool = False
    auto_complete_subtasks: bool = False

    # Metadata sync
    sync_priority: bool = True
    sync_labels: bool = True
    sync_components: bool = True
