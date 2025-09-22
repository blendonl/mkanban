from typing import Dict, Any, Type, TypeVar, Optional
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import LoggerFactory, ContextAwareLogger
from src.utils.file_operations import FileOperations
from src.infrastructure.storage.markdown_board_repository import MarkdownBoardRepository
from src.infrastructure.storage.markdown_storage_repository import (
    MarkdownStorageRepository,
)
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.services.validation_service import ValidationService


T = TypeVar("T")


class DependencyContainer:
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._setup_default_factories()

    def _setup_default_factories(self):
        """Set up default factories for core dependencies."""

        # Configuration
        self._factories[ConfigurationManager] = lambda: ConfigurationManager()

        # Utilities
        self._factories[PathResolver] = lambda: PathResolver(
            self.get(ConfigurationManager)
        )
        self._factories[LoggerFactory] = lambda: LoggerFactory(
            self.get(ConfigurationManager), self.get(PathResolver)
        )

        # File operations
        self._factories[FileOperations] = lambda: FileOperations(
            self.get(LoggerFactory).get_daemon_logger("file_operations")
        )

        # Repositories
        self._factories[MarkdownBoardRepository] = lambda: MarkdownBoardRepository(
            self.get(PathResolver),
            self.get(LoggerFactory).get_daemon_logger("board_repository"),
        )

        self._factories[MarkdownStorageRepository] = lambda: MarkdownStorageRepository(
            self.get(PathResolver),
            self.get(LoggerFactory).get_daemon_logger("storage_repository"),
        )

        # Services
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

    def get_logger(self, name: str, component: str = "daemon") -> ContextAwareLogger:
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
def get_board_service() -> BoardService:
    return get_container().get(BoardService)


def get_item_service() -> ItemService:
    return get_container().get(ItemService)


def get_config_manager() -> ConfigurationManager:
    return get_container().get(ConfigurationManager)


def get_path_resolver() -> PathResolver:
    return get_container().get(PathResolver)


def get_logger_factory() -> LoggerFactory:
    return get_container().get(LoggerFactory)


def get_daemon_logger(name: str) -> ContextAwareLogger:
    return get_container().get_daemon_logger(name)


def get_tui_logger(name: str) -> ContextAwareLogger:
    return get_container().get_tui_logger(name)

