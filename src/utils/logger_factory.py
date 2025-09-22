import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver


class ContextAwareLogger:
    def __init__(self, logger: logging.Logger, component: str = ""):
        self._logger = logger
        self._component = component
        self._context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        self._context.update(context)

    def clear_context(self) -> None:
        self._context.clear()

    def _format_message(self, message: str, extra_context: Optional[Dict[str, Any]] = None) -> str:
        context = {**self._context}
        if extra_context:
            context.update(extra_context)

        context_parts = []

        if board := context.get("board"):
            context_parts.append(f"board={board}")

        if column := context.get("column"):
            context_parts.append(f"column={column}")

        if item := context.get("item"):
            context_parts.append(f"item={item}")

        if jira_ticket := context.get("jira_ticket"):
            context_parts.append(f"JIRA:{jira_ticket}")

        if correlation_id := context.get("correlation_id"):
            context_parts.append(f"id={correlation_id}")

        if context_parts:
            context_str = f"[{', '.join(context_parts)}]"
            return f"{context_str} {message}"

        return message

    def debug(self, message: str, **context: Any) -> None:
        self._logger.debug(self._format_message(message, context))

    def info(self, message: str, **context: Any) -> None:
        self._logger.info(self._format_message(message, context))

    def warning(self, message: str, **context: Any) -> None:
        self._logger.warning(self._format_message(message, context))

    def error(self, message: str, **context: Any) -> None:
        self._logger.error(self._format_message(message, context))

    def critical(self, message: str, **context: Any) -> None:
        self._logger.critical(self._format_message(message, context))

    def exception(self, message: str, **context: Any) -> None:
        self._logger.exception(self._format_message(message, context))


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