"""Configuration management for MKanban."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Application configuration."""

    # Data settings
    data_dir: str = "./data"
    auto_save: bool = True
    auto_save_interval: int = 30  # seconds
    backup_count: int = 5

    # UI settings
    theme: str = "dark"
    show_parent_colors: bool = True
    default_parent_view: bool = False
    column_width: int = 30

    # Keyboard shortcuts
    shortcuts: Dict[str, str] = None

    def __post_init__(self):
        """Initialize default vim-style shortcuts."""
        if self.shortcuts is None:
            self.shortcuts = {
                # Navigation (vim-style)
                "focus_next": "j",
                "focus_previous": "k",
                "focus_left": "h",
                "focus_right": "l",
                "focus_first": "gg",
                "focus_last": "G",

                # Item operations (vim-style)
                "new_item": "o",
                "edit_item": "i",
                "delete_item": "d",
                "move_left": "ctrl+h",
                "move_right": "ctrl+l",

                # View operations
                "toggle_parents": "p",
                "save": "w",
                "refresh": "r",

                # Other
                "help": "g?",
                "quit": "q"
            }

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file."""
        if config_path is None:
            config_path = Path.home() / ".mkanban" / "config.json"

        if not config_path.exists():
            return cls()

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            return cls(**data)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".mkanban" / "config.json"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def get_data_dir(self) -> Path:
        """Get the data directory as a Path object."""
        return Path(self.data_dir).expanduser().resolve()
