from pathlib import Path
from typing import Optional
from src.config.configuration_manager import ConfigurationManager
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.utils.string_utils import get_safe_filename


class PathResolver:
    def __init__(self, config_manager: ConfigurationManager, tmux_manager: Optional[TmuxSessionManager] = None):
        self.config_manager = config_manager
        self.tmux_manager = tmux_manager or TmuxSessionManager()

    def get_data_dir(self) -> Path:
        return self.config_manager.get_data_dir()

    def get_session_based_data_dir(self) -> Path:
        mkanban_path = self.config_manager.get_mkanban_path()

        if mkanban_path:
            return Path(mkanban_path).expanduser().resolve()

        try:
            current_session = self.tmux_manager.get_current_session()
            if current_session:
                session_path = (
                    Path.home() / ".mkanban" / "boards" / current_session.name
                )
                session_path.mkdir(parents=True, exist_ok=True)
                return session_path
        except Exception:
            pass

        return self.get_data_dir()

    def get_boards_directory(self) -> Path:
        data_dir = self.get_session_based_data_dir()
        mkanban_path = self.config_manager.get_mkanban_path()

        if mkanban_path:
            return data_dir
        else:
            boards_dir = data_dir / "boards"
            boards_dir.mkdir(parents=True, exist_ok=True)
            return boards_dir

    def get_board_directory(self, board_name: str) -> Path:
        boards_dir = self.get_boards_directory()
        safe_board_name = get_safe_filename(board_name)
        board_dir = boards_dir / safe_board_name
        board_dir.mkdir(parents=True, exist_ok=True)
        return board_dir

    def get_column_directory(self, board_name: str, column_name: str) -> Path:
        board_dir = self.get_board_directory(board_name)
        safe_column_name = get_safe_filename(column_name)
        column_dir = board_dir / safe_column_name
        column_dir.mkdir(parents=True, exist_ok=True)
        return column_dir

    def get_socket_path(self, session_name: Optional[str] = None) -> Path:
        config = self.config_manager.config

        if config.daemon.tmux_session_only and session_name:
            safe_session_name = get_safe_filename(session_name)
            return self.get_data_dir() / safe_session_name / "daemon.sock"
        else:
            return self.get_data_dir() / "daemon.sock"

    def get_log_directory(self, component: str = "daemon") -> Path:
        config = self.config_manager.config

        if component == "daemon":
            log_dir = Path(config.logging.daemon_log_dir)
        elif component == "tui":
            log_dir = Path(config.logging.tui_log_dir)
        else:
            log_dir = self.config_manager.get_config_dir() / "logs" / component

        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def resolve_path(self, path: str) -> Path:
        return Path(path).expanduser().resolve()

    def ensure_directory_exists(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path