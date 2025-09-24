from dataclasses import dataclass


@dataclass
class LoggingConfiguration:
    level: str = "INFO"
    daemon_log_dir: str = ""
    tui_log_dir: str = ""
    create_timestamped_daemon_logs: bool = True
    max_log_files: int = 30
    log_format: str = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    daemon_log_format: str = "[%(asctime)s] DAEMON %(levelname)s %(name)s: %(message)s"
    tui_log_format: str = "[%(asctime)s] TUI %(levelname)s %(name)s: %(message)s"
