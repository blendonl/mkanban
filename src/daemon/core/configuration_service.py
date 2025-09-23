from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import logging

from src.config.settings import Settings
from src.infrastructure.tmux.session_manager import (
    get_mkanban_data_path,
    ensure_mkanban_directory,
)
from src.utils.string_utils import get_safe_filename


@dataclass
class JiraConfig:
    """Configuration for Jira integration"""

    enabled: bool = False
    api_url: str = ""
    username: str = ""
    api_token: str = ""
    project_keys: List[str] = field(default_factory=list)
    polling_interval: int = 300  # 5 minutes
    bidirectional_sync: bool = False
    backlog_limit: int = 50  # -1 for unlimited
    status_mapping: Dict[str, str] = field(
        default_factory=lambda: {
            "To Do": "to-do",
            "In Progress": "in-progress",
            "Done": "done",
            "Backlog": "backlog",
        }
    )
    jql_filter: str = ""
    board_name: str = "jira-tickets"
    branch_patterns: List[str] = field(
        default_factory=lambda: [
            r".*[A-Z]+-\d+.*",  # Matches PROJ-123 anywhere in branch name
            r"[A-Z]+-\d+/.*",  # Matches PROJ-123/feature-name
            r".*/[A-Z]+-\d+.*",  # Matches feature/PROJ-123-something
        ]
    )


@dataclass
class DaemonConfiguration:
    """Unified daemon configuration"""

    # Core settings
    enabled: bool = True
    polling_interval: int = 5
    tmux_session_only: bool = True

    # Session-based task management
    enable_session_task_management: bool = True
    auto_complete_on_session_switch: bool = True
    auto_activate_on_session_switch: bool = True

    # Session context
    session_name: str = "git-branches"
    data_path: Path = field(default_factory=ensure_mkanban_directory)

    # Board configuration
    default_board: str = "git-branches"
    default_column: str = "to-do"
    in_progress_column: str = "in-progress"
    done_column: str = "done"

    # Branch filtering
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
        default_factory=lambda: ["main", "master", "develop", "staging", "production"]
    )

    # Jira integration
    jira: JiraConfig = field(default_factory=JiraConfig)

    def __post_init__(self):
        """Ensure data path is resolved"""
        if isinstance(self.data_path, str):
            self.data_path = Path(self.data_path)
        self.data_path = self.data_path.resolve()


class ConfigurationService:
    """Manages daemon configuration with session awareness"""

    def __init__(self, initial_config: Optional[DaemonConfiguration] = None):
        self.logger = logging.getLogger("mkanban-daemon")
        self._config = initial_config or DaemonConfiguration()
        self._settings: Optional[Settings] = None

    @property
    def config(self) -> DaemonConfiguration:
        """Get current configuration"""
        return self._config

    @property
    def settings(self) -> Settings:
        """Get Settings instance for current configuration"""
        if self._settings is None:
            self._settings = Settings(boards_path=str(self._config.data_path))
        return self._settings

    def update_session_context(self, session_name: str) -> bool:
        """
        Update configuration for a new session context.

        Returns True if configuration changed, False otherwise.
        """
        if session_name == self._config.session_name:
            return False

        old_session = self._config.session_name
        self.logger.info(
            f"Updating configuration from session '{old_session}' to '{session_name}'"
        )

        # Update session-specific configuration
        self._config.session_name = session_name
        self._config.default_board = session_name

        # Update data path if using session-specific paths
        if self._config.tmux_session_only:
            # Use global data path but session-specific board name
            self._config.data_path = get_mkanban_data_path()

        # Invalidate cached settings to force recreation with new data path
        self._settings = None

        self.logger.info(
            f"Configuration updated for session '{session_name}': "
            f"board='{self._config.default_board}', "
            f"data_path='{self._config.data_path}'"
        )

        return True

    def get_board_name(self) -> str:
        """Get the current board name"""
        return self._config.default_board

    def get_data_path(self) -> Path:
        """Get the current data path"""
        return self._config.data_path

    def get_socket_path(self) -> Path:
        """Get the IPC socket path for current session"""
        if self._config.tmux_session_only:
            # Use session-specific socket path
            safe_session_name = get_safe_filename(self._config.session_name)
            return self._config.data_path / safe_session_name / "daemon.sock"
        else:
            # Use global socket path
            return self._config.data_path / "daemon.sock"

    def should_track_branch(self, branch_name: str) -> bool:
        """Check if a branch should be tracked based on configuration"""
        from fnmatch import fnmatch

        # Skip excluded branches
        for excluded in self._config.excluded_branches:
            if fnmatch(branch_name, excluded):
                return False

        # Check inclusion patterns
        if self._config.branch_patterns:
            for pattern in self._config.branch_patterns:
                if fnmatch(branch_name, pattern):
                    return True
            return False  # No patterns matched

        return True  # No patterns specified, track all (except excluded)

    def is_session_task_management_enabled(self) -> bool:
        """Check if session-based task management is enabled"""
        return self._config.enable_session_task_management

    def should_auto_complete_on_session_switch(self) -> bool:
        """Check if tasks should be auto-completed when switching sessions"""
        return (
            self._config.enable_session_task_management
            and self._config.auto_complete_on_session_switch
        )

    def should_auto_activate_on_session_switch(self) -> bool:
        """Check if tasks should be auto-activated when switching sessions"""
        return (
            self._config.enable_session_task_management
            and self._config.auto_activate_on_session_switch
        )

    def is_jira_enabled(self) -> bool:
        """Check if Jira integration is enabled"""
        return self._config.jira.enabled

    def get_jira_config(self) -> JiraConfig:
        """Get Jira configuration"""
        return self._config.jira

    def should_track_jira_ticket(
        self, ticket_key: str, project_keys: List[str] = None
    ) -> bool:
        """Check if a Jira ticket should be tracked based on configuration"""
        if not self.is_jira_enabled():
            return False

        # Use provided project keys or fall back to config
        projects = project_keys or self._config.jira.project_keys
        if not projects:
            return True  # Track all if no specific projects configured

        # Extract project key from ticket (e.g., "PROJ-123" -> "PROJ")
        if "-" in ticket_key:
            ticket_project = ticket_key.split("-")[0]
            return ticket_project in projects

        return False

    def get_jira_board_name(self) -> str:
        """Get the board name for Jira tickets"""
        return self._config.jira.board_name

    @classmethod
    def from_args(cls, args) -> "ConfigurationService":
        """Create configuration service from command line arguments"""
        config = DaemonConfiguration(
            enabled=not args.disable,
            polling_interval=args.polling_interval,
            tmux_session_only=args.tmux_session_only,
            session_name=args.board_name,
            default_board=args.board_name,
            default_column=args.default_column,
            in_progress_column=args.in_progress_column,
            done_column=args.done_column,
            data_path=(
                Path(args.data_path) if args.data_path else get_mkanban_data_path()
            ),
        )

        if args.branch_patterns:
            config.branch_patterns = args.branch_patterns.split(",")
        if args.excluded_branches:
            config.excluded_branches = args.excluded_branches.split(",")

        return cls(config)

