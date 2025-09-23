from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class TmuxSession:
    """Represents a tmux session"""

    name: str
    id: str
    attached: bool
    windows: int
    working_directory: Optional[Path] = None


@dataclass
class TmuxPane:
    """Represents a tmux pane"""

    id: str
    session_name: str
    window_index: int
    pane_index: int
    working_directory: Path
    command: str
    active: bool = False