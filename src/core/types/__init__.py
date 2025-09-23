from typing import Dict, List, Union
from pathlib import Path
from datetime import datetime

from .enums import RefreshType, ThemeType, ParentColor

ItemId = str
ColumnId = str
BoardId = str
ParentId = str
FilePath = Union[str, Path]
Timestamp = datetime
Metadata = Dict[str, Union[str, int, bool, List, Dict]]

__all__ = [
    "ItemId",
    "ColumnId",
    "BoardId",
    "ParentId",
    "FilePath",
    "Timestamp",
    "Metadata",
    "RefreshType",
    "ThemeType",
    "ParentColor",
]