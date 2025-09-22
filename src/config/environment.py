import os
from pathlib import Path
from src.core.constants import DEFAULT_DATA_DIR, DEFAULT_CONFIG_DIR


class Environment:
    @staticmethod
    def get_data_dir() -> str:
        return os.environ.get("MKANBAN_DATA_DIR", DEFAULT_DATA_DIR)

    @staticmethod
    def get_config_dir() -> Path:
        config_dir_str = os.environ.get("MKANBAN_CONFIG_DIR")
        if config_dir_str:
            return Path(config_dir_str)
        return DEFAULT_CONFIG_DIR

    @staticmethod
    def get_editor() -> str:
        # Priority: EDITOR env var, then MKANBAN_EDITOR, then default to nvim
        return os.environ.get("EDITOR") or os.environ.get("MKANBAN_EDITOR", "nvim")

    @staticmethod
    def get_cli_editor() -> str:
        return os.environ.get("MKANBAN_CLI_EDITOR", "neovide")

    @staticmethod
    def is_debug_mode() -> bool:
        return os.environ.get("MKANBAN_DEBUG", "false").lower() in ("true", "1", "yes")

    @staticmethod
    def get_theme() -> str:
        return os.environ.get("MKANBAN_THEME", "dark")

    @staticmethod
    def get_auto_save_interval() -> int:
        try:
            return int(os.environ.get("MKANBAN_AUTO_SAVE_INTERVAL", "30"))
        except ValueError:
            return 30
