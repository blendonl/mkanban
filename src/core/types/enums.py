from enum import Enum


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