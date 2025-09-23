import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import asdict
from src.core.constants import DEFAULT_CONFIG_FILE
from .jira_config import JiraConfiguration
from .daemon_config import DaemonConfiguration
from .logging_config import LoggingConfiguration
from .unified_config import UnifiedConfiguration


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
