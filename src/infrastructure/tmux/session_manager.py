"""Tmux Session Manager

Provides utilities for detecting and managing tmux sessions,
particularly for identifying the current active session and its working directory.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

from core.exceptions import MKanbanError


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


class TmuxSessionManager:
    """Manages tmux session detection and information"""
    
    def __init__(self):
        self._check_tmux_available()
    
    def _check_tmux_available(self) -> None:
        """Check if tmux is available and we're in a tmux session"""
        try:
            subprocess.run(["tmux", "list-sessions"], 
                         capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # tmux might not be available or no sessions exist
            pass
    
    def is_in_tmux_session(self) -> bool:
        """Check if current process is running inside a tmux session"""
        return os.environ.get('TMUX') is not None
    
    def get_current_session(self) -> Optional[TmuxSession]:
        """Get information about the current tmux session"""
        if not self.is_in_tmux_session():
            return None
        
        try:
            # Get current session info
            result = subprocess.run([
                "tmux", "display-message", "-p", 
                "#{session_name}|#{session_id}|#{session_attached}|#{session_windows}"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) == 4:
                    name, session_id, attached, windows = parts
                    return TmuxSession(
                        name=name,
                        id=session_id,
                        attached=attached == '1',
                        windows=int(windows)
                    )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None
    
    def get_current_pane_info(self) -> Optional[TmuxPane]:
        """Get information about the current tmux pane"""
        if not self.is_in_tmux_session():
            return None
        
        try:
            result = subprocess.run([
                "tmux", "display-message", "-p",
                "#{pane_id}|#{session_name}|#{window_index}|#{pane_index}|#{pane_current_path}|#{pane_current_command}"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) == 6:
                    pane_id, session_name, window_idx, pane_idx, current_path, command = parts
                    return TmuxPane(
                        id=pane_id,
                        session_name=session_name,
                        window_index=int(window_idx),
                        pane_index=int(pane_idx),
                        working_directory=Path(current_path),
                        command=command,
                        active=True
                    )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None
    
    def get_session_working_directory(self, session_name: Optional[str] = None) -> Optional[Path]:
        """Get the working directory of a tmux session"""
        if session_name is None:
            # Get current session's working directory via current pane
            pane_info = self.get_current_pane_info()
            return pane_info.working_directory if pane_info else None
        
        try:
            # Get working directory of specific session
            result = subprocess.run([
                "tmux", "display-message", "-t", session_name, "-p", "#{pane_current_path}"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        return None
    
    def list_all_sessions(self) -> List[TmuxSession]:
        """List all tmux sessions"""
        sessions = []
        
        try:
            result = subprocess.run([
                "tmux", "list-sessions", "-F",
                "#{session_name}|#{session_id}|#{session_attached}|#{session_windows}"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) == 4:
                            name, session_id, attached, windows = parts
                            sessions.append(TmuxSession(
                                name=name,
                                id=session_id,
                                attached=attached == '1',
                                windows=int(windows)
                            ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return sessions
    
    def get_active_session_repository(self) -> Optional[Path]:
        """Get the git repository path for the active tmux session"""
        if not self.is_in_tmux_session():
            return None
        
        pane_info = self.get_current_pane_info()
        if not pane_info:
            return None
        
        # Start from current working directory and walk up to find .git
        current_path = pane_info.working_directory
        
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return current_path
            current_path = current_path.parent
        
        return None
    
    def should_monitor_session(self, session_name: str) -> bool:
        """Check if a session should be monitored (for future extensibility)"""
        # For now, only monitor the current active session
        current_session = self.get_current_session()
        return current_session is not None and current_session.name == session_name


def get_mkanban_data_path() -> Path:
    """Get the MKanban data path from environment or default to home directory"""
    mkanban_path = os.environ.get('MKANBAN_PATH')
    
    if mkanban_path:
        return Path(mkanban_path).expanduser().resolve()
    else:
        return Path.home() / ".mkanban"


def ensure_mkanban_directory() -> Path:
    """Ensure the MKanban directory exists and return its path"""
    data_path = get_mkanban_data_path()
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path