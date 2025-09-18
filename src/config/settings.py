import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from core.constants import (
    DEFAULT_DATA_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_COLUMN_WIDTH,
    DEFAULT_AUTO_SAVE_INTERVAL,
    DEFAULT_BACKUP_COUNT,
    VIM_KEYBINDINGS
)
from core.types import ThemeType


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
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        if config_path is None:
            config_path = DEFAULT_CONFIG_FILE

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get_data_dir(self) -> Path:
        return Path(self.data_dir).expanduser().resolve()