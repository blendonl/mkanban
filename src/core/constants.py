from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mkanban"
DEFAULT_BOARDS_PATH = Path.home() / ".mkanban" / "boards"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

BOARD_FILENAME = "kanban.md"
COLUMN_METADATA_FILENAME = "column.md"
ITEMS_DIR_NAME = "items"

DEFAULT_COLUMN_WIDTH = 30
DEFAULT_AUTO_SAVE_INTERVAL = 30
DEFAULT_BACKUP_COUNT = 5

VIM_KEYBINDINGS = {
    "focus_next": "j",
    "focus_previous": "k",
    "focus_left": "h",
    "focus_right": "l",
    "focus_first": "gg",
    "focus_last": "G",
    "new_item": "o",
    "edit_item": "i",
    "delete_item": "d",
    "move_left": "ctrl+h",
    "move_right": "ctrl+l",
    "toggle_parents": "p",
    "save": "w",
    "refresh": "r",
    "help": "g?",
    "quit": "q",
}

MAX_FILENAME_RETRIES = 100
FILENAME_ID_SUFFIX_LENGTH = 8
