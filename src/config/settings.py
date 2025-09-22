import json
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from src.core.constants import (
    DEFAULT_DATA_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_COLUMN_WIDTH,
    DEFAULT_AUTO_SAVE_INTERVAL,
    DEFAULT_BACKUP_COUNT,
    VIM_KEYBINDINGS,
)
from src.core.types import ThemeType
from src.infrastructure.tmux.session_manager import TmuxSessionManager


@dataclass
class Settings:
    data_dir: str = DEFAULT_DATA_DIR
    auto_save: bool = True
    auto_save_interval: int = DEFAULT_AUTO_SAVE_INTERVAL
    backup_count: int = DEFAULT_BACKUP_COUNT

    theme: str = ThemeType.DARK.value
    show_parent_colors: bool = True
    default_parent_view: bool = False
    column_width: int = DEFAULT_COLUMN_WIDTH

    shortcuts: Dict[str, str] = None

    def __post_init__(self):
        if self.shortcuts is None:
            self.shortcuts = VIM_KEYBINDINGS.copy()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        if config_path is None:
            config_path = DEFAULT_CONFIG_FILE

        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r") as f:
                data = json.load(f)

            return cls(**data)
        except (json.JSONDecodeError, TypeError) as e:
            # Use logging instead of print, but import at function level to avoid circular imports
            import logging
            logger = logging.getLogger("mkanban.config")
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        if config_path is None:
            config_path = DEFAULT_CONFIG_FILE

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get_data_dir(self) -> Path:
        return Path(self.data_dir).expanduser().resolve()

    def get_session_based_data_dir(self) -> Path:
        """Get data directory based on tmux session, fall back to data_dir"""
        tmux_manager = TmuxSessionManager()

        try:
            current_session = tmux_manager.get_current_session()
            if current_session:
                # Get base path from MKANBAN_PATH or default to ~/.mkanban
                mkanban_path = os.environ.get("MKANBAN_PATH")
                if mkanban_path:
                    # Use MKANBAN_PATH directly - don't add session name
                    session_path = Path(mkanban_path).expanduser().resolve()
                else:
                    # Use ~/.mkanban/boards/{session_name} for default case
                    session_path = (
                        Path.home() / ".mkanban" / "boards" / current_session.name
                    )

                session_path.mkdir(parents=True, exist_ok=True)
                return session_path
        except Exception:
            # If tmux detection fails, fall back to configured data_dir
            pass

        return self.get_data_dir()

    def get_boards_directory(self) -> Path:
        """Get the directory where board folders are located"""
        data_dir = self.get_session_based_data_dir()

        # If MKANBAN_PATH is set, the data_dir IS the boards directory
        # Otherwise, boards are in data_dir/boards
        mkanban_path = os.environ.get("MKANBAN_PATH")
        if mkanban_path:
            return data_dir
        else:
            boards_dir = data_dir / "boards"
            boards_dir.mkdir(parents=True, exist_ok=True)
            return boards_dir
