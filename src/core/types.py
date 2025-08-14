from enum import Enum
from typing import Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime

ItemId = str
ColumnId = str
BoardId = str
ParentId = str
FilePath = Union[str, Path]
Timestamp = datetime
Metadata = Dict[str, Union[str, int, bool, List, Dict]]


class RefreshType(Enum):
    FULL = "full"
    PARTIAL = "partial"
    ITEMS_ONLY = "items_only"


class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"


class ParentColor(Enum):
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"
    CYAN = "cyan"
    ORANGE = "orange"