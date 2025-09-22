import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field, asdict
from src.core.constants import (
    DEFAULT_BOARDS_PATH,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_COLUMN_WIDTH,
    DEFAULT_AUTO_SAVE_INTERVAL,
    DEFAULT_BACKUP_COUNT,
    VIM_KEYBINDINGS,
)
from src.core.types import ThemeType


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


@dataclass
class LoggingConfiguration:
    level: str = "INFO"
    daemon_log_dir: str = ""
    tui_log_dir: str = ""
    create_timestamped_daemon_logs: bool = True
    max_log_files: int = 30
    log_format: str = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    daemon_log_format: str = (
        "[%(asctime)s] DAEMON %(levelname)s %(name)s: %(message)s"
    )
    tui_log_format: str = (
        "[%(asctime)s] TUI %(levelname)s %(name)s: %(message)s"
    )


@dataclass
class UnifiedConfiguration:
    boards_path: str = str(DEFAULT_BOARDS_PATH)
    config_dir: str = ""
    auto_save: bool = True
    auto_save_interval: int = DEFAULT_AUTO_SAVE_INTERVAL
    backup_count: int = DEFAULT_BACKUP_COUNT
    theme: str = ThemeType.DARK.value
    show_parent_colors: bool = True
    default_parent_view: bool = False
    column_width: int = DEFAULT_COLUMN_WIDTH
    editor: str = "nvim"
    cli_editor: str = "neovide"
    shortcuts: Dict[str, str] = field(
        default_factory=lambda: VIM_KEYBINDINGS.copy()
    )
    daemon: DaemonConfiguration = field(default_factory=DaemonConfiguration)
    logging: LoggingConfiguration = field(
        default_factory=LoggingConfiguration
    )

    def __post_init__(self):
        if not self.config_dir:
            self.config_dir = str(DEFAULT_CONFIG_DIR)
        if not self.logging.daemon_log_dir:
            self.logging.daemon_log_dir = str(
                Path(self.config_dir) / "logs" / "daemon"
            )
        if not self.logging.tui_log_dir:
            self.logging.tui_log_dir = str(
                Path(self.config_dir) / "logs" / "tui"
            )


class ConfigurationManager:
    _instance: Optional["ConfigurationManager"] = None
    _config: Optional[UnifiedConfiguration] = None

    def __new__(cls) -> "ConfigurationManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_configuration()

    def _load_configuration(self) -> UnifiedConfiguration:
        config_path = self._get_config_file_path()

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                return self._create_config_from_dict(data)
            except (json.JSONDecodeError, TypeError):
                # Fallback to defaults if config is corrupted
                pass

        # Create default configuration
        config = UnifiedConfiguration()

        # Auto-save the default config when it doesn't exist
        self._save_config_to_file(config, config_path)
        return config

    def _create_config_from_dict(
        self, data: Dict[str, Any]
    ) -> UnifiedConfiguration:
        """Create configuration from dict, handling nested dataclasses."""
        # Handle nested daemon configuration
        daemon_data = data.get("daemon", {})
        if daemon_data:
            jira_data = daemon_data.get("jira", {})
            daemon_data["jira"] = (
                JiraConfiguration(**jira_data)
                if jira_data else JiraConfiguration()
            )
            data["daemon"] = DaemonConfiguration(**daemon_data)
        else:
            data["daemon"] = DaemonConfiguration()

        # Handle nested logging configuration
        logging_data = data.get("logging", {})
        if logging_data:
            data["logging"] = LoggingConfiguration(**logging_data)
        else:
            data["logging"] = LoggingConfiguration()

        return UnifiedConfiguration(**data)

    def _save_config_to_file(
        self, config: UnifiedConfiguration, config_path: Path
    ) -> None:
        """Save configuration to path, creating directories as needed."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(asdict(config), f, indent=2)

    def _get_config_file_path(self) -> Path:
        return DEFAULT_CONFIG_FILE

    @property
    def config(self) -> UnifiedConfiguration:
        if self._config is None:
            self._config = self._load_configuration()
        return self._config

    def get_boards_path(self) -> Path:
        return Path(self.config.boards_path).expanduser().resolve()

    def get_config_dir(self) -> Path:
        return Path(self.config.config_dir).expanduser().resolve()

    def get_editor(self) -> str:
        return os.environ.get("EDITOR") or self.config.editor

    def get_cli_editor(self) -> str:
        return self.config.cli_editor

    def is_debug_mode(self) -> bool:
        return self.config.logging.level == "DEBUG"

    def save_configuration(self, config_path: Optional[Path] = None) -> None:
        if config_path is None:
            config_path = self._get_config_file_path()

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)

    def update_configuration(self, **updates: Any) -> None:
        if self._config is None:
            self._config = self._load_configuration()

        for key, value in updates.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self.save_configuration()

    def reload_configuration(self) -> None:
        self._config = self._load_configuration()


def get_config() -> ConfigurationManager:
    return ConfigurationManager()
