from typing import Dict, Any, Type, TypeVar, Optional
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import LoggerFactory, ContextAwareLogger
from src.utils.file_operations import FileOperations
from src.infrastructure.storage.markdown_board_repository import (
    MarkdownBoardRepository,
)
from src.infrastructure.storage.markdown_storage_repository import (
    MarkdownStorageRepository,
)
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.services.validation_service import ValidationService
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.infrastructure.git.repository import GitOperations
from src.daemon.core.configuration_service import ConfigurationService
from src.daemon.jira.jira_client import JiraClient
from src.daemon.jira.jira_daemon import JiraDaemon
from src.daemon.jira.jira_sync_coordinator import JiraSyncCoordinator
from src.daemon.git_monitor import GitMonitor
from src.daemon.core.session_context_manager import SessionContextManager

# CLI components imported lazily to avoid circular imports
from src.controllers.item_controller import ItemController
from src.controllers.column_controller import ColumnController


T = TypeVar("T")


class DependencyContainer:
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._setup_default_factories()

    def _setup_default_factories(self):
        """Set up default factories for core dependencies."""
        self._setup_configuration_factories()
        self._setup_utility_factories()
        self._setup_infrastructure_factories()
        self._setup_jira_factories()
        self._setup_daemon_factories()
        self._setup_repository_factories()
        self._setup_service_factories()
        self._setup_cli_factories()

    def _setup_configuration_factories(self):
        """Set up configuration-related factories."""
        self._factories[ConfigurationManager] = lambda: ConfigurationManager()
        self._factories[ConfigurationService] = lambda: ConfigurationService()

    def _setup_utility_factories(self):
        """Set up utility and helper factories."""
        self._factories[PathResolver] = lambda: PathResolver(
            self.get(ConfigurationManager)
        )
        self._factories[LoggerFactory] = lambda: LoggerFactory(
            self.get(ConfigurationManager), self.get(PathResolver)
        )
        self._factories[FileOperations] = lambda: FileOperations(
            self.get(LoggerFactory).get_daemon_logger("file_operations")
        )

    def _setup_infrastructure_factories(self):
        """Set up infrastructure service factories."""
        self._factories[TmuxSessionManager] = lambda: TmuxSessionManager()

    def _setup_jira_factories(self):
        """Set up JIRA integration factories."""
        self._factories[JiraClient] = lambda: JiraClient(
            self.get(ConfigurationService).get_jira_config()
        )
        self._factories[JiraSyncCoordinator] = lambda: JiraSyncCoordinator(
            self.get(ConfigurationService)
        )
        self._factories[JiraDaemon] = lambda: JiraDaemon(
            self.get(ConfigurationService)
        )

    def _setup_daemon_factories(self):
        """Set up daemon and monitoring factories."""
        self._factories[SessionContextManager] = lambda: SessionContextManager(
            self.get(ConfigurationService).config.tmux_session_only
        )
        self._factories[GitMonitor] = lambda: GitMonitor(
            polling_interval=self.get(
                ConfigurationService
            ).config.polling_interval,
        )

    def _setup_repository_factories(self):
        """Set up repository factories."""
        self._factories[MarkdownBoardRepository] = (
            lambda: MarkdownBoardRepository(
                self.get(PathResolver),
                self.get(LoggerFactory).get_daemon_logger("board_repository"),
            )
        )
        self._factories[MarkdownStorageRepository] = (
            lambda: MarkdownStorageRepository(
                self.get(PathResolver),
                self.get(LoggerFactory).get_daemon_logger(
                    "storage_repository"
                ),
            )
        )

    def _setup_service_factories(self):
        """Set up business service factories."""
        self._factories[ValidationService] = lambda: ValidationService()
        self._factories[BoardService] = lambda: BoardService(
            self.get(MarkdownBoardRepository),
            self.get(ValidationService),
            self.get(LoggerFactory).get_daemon_logger("board_service"),
        )
        self._factories[ItemService] = lambda: ItemService(
            self.get(MarkdownStorageRepository),
            self.get(ValidationService),
            self.get(LoggerFactory).get_daemon_logger("item_service"),
        )

    def _setup_cli_factories(self):
        """Set up CLI component factories with lazy imports."""

        def _create_task_creator():
            from src.infrastructure.cli.task_creator import TaskCreator

            return TaskCreator(self, self.get(PathResolver).get_boards_path())

        def _create_todo_selector():
            from src.infrastructure.cli.todo_selector import TodoSelector

            return TodoSelector(self, self.get(PathResolver).get_boards_path())

        def _create_daemon_manager():
            from src.infrastructure.cli.daemon_manager import DaemonManager

            return DaemonManager()

        self._factories["TaskCreator"] = _create_task_creator
        self._factories["TodoSelector"] = _create_todo_selector
        self._factories["DaemonManager"] = _create_daemon_manager

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Register a factory function for an interface."""
        self._factories[interface] = factory

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        self._instances[interface] = instance

    def get(self, interface: Type[T]) -> T:
        """Get an instance of the requested interface."""
        # Return singleton if already created
        if interface in self._instances:
            return self._instances[interface]

        # Create instance using factory
        if interface in self._factories:
            instance = self._factories[interface]()
            self._instances[interface] = instance
            return instance

        raise ValueError(f"No factory registered for {interface}")

    def get_logger(
        self, name: str, component: str = "daemon"
    ) -> ContextAwareLogger:
        """Convenience method to get a logger."""
        logger_factory = self.get(LoggerFactory)
        return logger_factory.get_logger(name, component)

    def get_daemon_logger(self, name: str) -> ContextAwareLogger:
        """Convenience method to get a daemon logger."""
        return self.get_logger(name, "daemon")

    def get_tui_logger(self, name: str) -> ContextAwareLogger:
        """Convenience method to get a TUI logger."""
        return self.get_logger(name, "tui")

    def clear_instances(self) -> None:
        """Clear all singleton instances (useful for testing)."""
        self._instances.clear()
        # Reset ConfigurationManager singleton state
        ConfigurationManager._instance = None
        ConfigurationManager._config = None

    def setup_for_testing(self) -> None:
        """Set up container for testing with mock dependencies."""
        self.clear_instances()
        # Test-specific setup could be added here


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def set_container(container: DependencyContainer) -> None:
    """Set the global dependency container (useful for testing)."""
    global _container
    _container = container


# Convenience functions
# NOTE: For new code, prefer using get_container().get(ServiceType) directly
# to reduce indirection and improve clarity


def get_config_manager() -> ConfigurationManager:
    return get_container().get(ConfigurationManager)


def get_logger_factory() -> LoggerFactory:
    return get_container().get(LoggerFactory)


def get_daemon_logger(name: str) -> ContextAwareLogger:
    return get_container().get_daemon_logger(name)


def get_tui_logger(name: str) -> ContextAwareLogger:
    return get_container().get_tui_logger(name)


def create_git_operations(repo_path) -> GitOperations:
    """Factory function to create GitOperations for a specific repository path"""
    return GitOperations(repo_path)


def get_jira_daemon() -> JiraDaemon:
    return get_container().get(JiraDaemon)


def get_git_monitor() -> GitMonitor:
    return get_container().get(GitMonitor)


def get_session_context_manager() -> SessionContextManager:
    return get_container().get(SessionContextManager)


def get_task_creator():
    return get_container().get("TaskCreator")


def get_todo_selector():
    return get_container().get("TodoSelector")


def get_daemon_manager():
    return get_container().get("DaemonManager")


def create_item_controller(board, item) -> ItemController:
    """Factory function to create ItemController with specific board and item"""
    container = get_container()
    return ItemController(
        board=board,
        item=item,
        board_service=container.get(BoardService),
        item_service=container.get(ItemService),
    )


def create_column_controller(board, column) -> ColumnController:
    """Factory function to create ColumnController with specific board and column"""
    container = get_container()
    return ColumnController(
        board=board,
        column=column,
        board_service=container.get(BoardService),
        item_service=container.get(ItemService),
    )
