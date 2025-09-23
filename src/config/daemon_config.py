from dataclasses import dataclass, field
from typing import List
from .jira_config import JiraConfiguration


@dataclass
class DaemonConfiguration:
    enabled: bool = True
    polling_interval: int = 5
    tmux_session_only: bool = True
    enable_session_task_management: bool = True
    auto_complete_on_session_switch: bool = True
    auto_activate_on_session_switch: bool = True
    session_name: str = "git-branches"
    default_board: str = "git-branches"
    default_column: str = "to-do"
    in_progress_column: str = "in-progress"
    done_column: str = "done"
    branch_patterns: List[str] = field(
        default_factory=lambda: [
            "feature/*",
            "bugfix/*",
            "hotfix/*",
            "fix/*",
            "feat/*",
            "test",
            "test/*",
            "*",
        ]
    )
    excluded_branches: List[str] = field(
        default_factory=lambda: [
            "main", "master", "develop", "staging", "production"
        ]
    )
    jira: JiraConfiguration = field(default_factory=JiraConfiguration)