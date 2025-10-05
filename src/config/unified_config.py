from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
from src.core.constants import (
    DEFAULT_BOARDS_PATH,
    DEFAULT_CONFIG_DIR,
    DEFAULT_COLUMN_WIDTH,
    DEFAULT_AUTO_SAVE_INTERVAL,
    DEFAULT_BACKUP_COUNT,
    VIM_KEYBINDINGS,
)
from src.core.types import ThemeType
from .daemon_config import DaemonConfiguration
from .logging_config import LoggingConfiguration


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
    shortcuts: Dict[str, str] = field(default_factory=lambda: VIM_KEYBINDINGS.copy())
    daemon: DaemonConfiguration = field(default_factory=DaemonConfiguration)
    logging: LoggingConfiguration = field(default_factory=LoggingConfiguration)

    def __post_init__(self):
        if not self.config_dir:
            self.config_dir = str(DEFAULT_CONFIG_DIR)
        if not self.logging.daemon_log_dir:
            self.logging.daemon_log_dir = str(Path(self.config_dir) / "logs" / "daemon")
        if not self.logging.tui_log_dir:
            self.logging.tui_log_dir = str(Path(self.config_dir) / "logs" / "tui")

