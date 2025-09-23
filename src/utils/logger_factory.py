import logging
import logging.handlers
from datetime import datetime
from typing import Optional
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver
from .context_logger import ContextAwareLogger


class LoggerFactory:
    _instance: Optional['LoggerFactory'] = None
    _initialized: bool = False

    def __new__(cls, config_manager: Optional[ConfigurationManager] = None,
                path_resolver: Optional[PathResolver] = None) -> 'LoggerFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager: Optional[ConfigurationManager] = None,
                 path_resolver: Optional[PathResolver] = None):
        if not self._initialized:
            self.config_manager = config_manager or ConfigurationManager()
            self.path_resolver = path_resolver or PathResolver(self.config_manager)
            self._setup_logging()
            self._initialized = True

    def _setup_logging(self) -> None:
        config = self.config_manager.config.logging

        log_level = getattr(logging, config.level.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format=config.log_format,
            handlers=[]
        )

        self._setup_daemon_logging()
        self._setup_tui_logging()

    def _setup_daemon_logging(self) -> None:
        config = self.config_manager.config.logging
        daemon_log_dir = self.path_resolver.get_log_directory("daemon")

        if config.create_timestamped_daemon_logs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"daemon_{timestamp}.log"
        else:
            log_filename = "daemon.log"

        log_file = daemon_log_dir / log_filename

        daemon_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=config.max_log_files
        )

        daemon_formatter = logging.Formatter(config.daemon_log_format)
        daemon_handler.setFormatter(daemon_formatter)

        daemon_logger = logging.getLogger("mkanban.daemon")
        daemon_logger.addHandler(daemon_handler)
        daemon_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    def _setup_tui_logging(self) -> None:
        config = self.config_manager.config.logging
        tui_log_dir = self.path_resolver.get_log_directory("tui")

        log_file = tui_log_dir / "tui.log"

        tui_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )

        tui_formatter = logging.Formatter(config.tui_log_format)
        tui_handler.setFormatter(tui_formatter)

        tui_logger = logging.getLogger("mkanban.tui")
        tui_logger.addHandler(tui_handler)
        tui_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    def get_logger(self, name: str, component: str = "daemon") -> ContextAwareLogger:
        if component == "daemon":
            base_name = f"mkanban.daemon.{name}"
        elif component == "tui":
            base_name = f"mkanban.tui.{name}"
        else:
            base_name = f"mkanban.{component}.{name}"

        logger = logging.getLogger(base_name)
        return ContextAwareLogger(logger, component)

    def get_daemon_logger(self, name: str) -> ContextAwareLogger:
        return self.get_logger(name, "daemon")

    def get_tui_logger(self, name: str) -> ContextAwareLogger:
        return self.get_logger(name, "tui")

    def cleanup_old_logs(self) -> None:
        config = self.config_manager.config.logging
        daemon_log_dir = self.path_resolver.get_log_directory("daemon")

        if not config.create_timestamped_daemon_logs:
            return

        log_files = sorted(
            daemon_log_dir.glob("daemon_*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        if len(log_files) > config.max_log_files:
            for old_log in log_files[config.max_log_files:]:
                old_log.unlink()


def get_logger_factory() -> LoggerFactory:
    return LoggerFactory()


def get_daemon_logger(name: str) -> ContextAwareLogger:
    return get_logger_factory().get_daemon_logger(name)


def get_tui_logger(name: str) -> ContextAwareLogger:
    return get_logger_factory().get_tui_logger(name)