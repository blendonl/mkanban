from unittest.mock import MagicMock
from typing import List, Optional, Dict, Any

from src.domain.entities.board import Board
from src.domain.entities.item import Item
from src.domain.repositories.board_repository import BoardRepository
from src.domain.repositories.storage_repository import StorageRepository
from src.services.validation_service import ValidationService
from src.utils.logger_factory import ContextAwareLogger
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver


class MockRepositoryFactory:
    """Factory for creating mock repository instances."""

    @staticmethod
    def create_board_repository(
        boards: Optional[List[Board]] = None,
        load_board_by_id_side_effect: Optional[callable] = None,
        load_board_by_name_side_effect: Optional[callable] = None
    ) -> MagicMock:
        """Create a mock board repository."""
        mock_repo = MagicMock(spec=BoardRepository)

        if boards is None:
            boards = []

        # Set up default return values
        mock_repo.load_all_boards.return_value = boards
        mock_repo.list_board_names.return_value = [board.name for board in boards]

        # Set up load_board_by_id behavior
        if load_board_by_id_side_effect:
            mock_repo.load_board_by_id.side_effect = load_board_by_id_side_effect
        else:
            def default_load_by_id(board_id: str) -> Optional[Board]:
                return next((b for b in boards if b.id == board_id), None)
            mock_repo.load_board_by_id.side_effect = default_load_by_id

        # Set up load_board_by_name behavior
        if load_board_by_name_side_effect:
            mock_repo.load_board_by_name.side_effect = load_board_by_name_side_effect
        else:
            def default_load_by_name(board_name: str) -> Optional[Board]:
                return next((b for b in boards if b.name == board_name), None)
            mock_repo.load_board_by_name.side_effect = default_load_by_name

        # Set up save_board behavior
        def save_board(board: Board) -> None:
            # Update existing board or add new one
            existing_index = next(
                (i for i, b in enumerate(boards) if b.id == board.id), None
            )
            if existing_index is not None:
                boards[existing_index] = board
            else:
                boards.append(board)

        mock_repo.save_board.side_effect = save_board

        # Set up delete_board behavior
        def delete_board(board_id: str) -> bool:
            original_count = len(boards)
            boards[:] = [b for b in boards if b.id != board_id]
            return len(boards) < original_count

        mock_repo.delete_board.side_effect = delete_board

        return mock_repo

    @staticmethod
    def create_storage_repository(
        items: Optional[List[Item]] = None,
        load_items_side_effect: Optional[callable] = None
    ) -> MagicMock:
        """Create a mock storage repository."""
        mock_repo = MagicMock(spec=StorageRepository)

        if items is None:
            items = []

        # Set up load_items behavior
        if load_items_side_effect:
            mock_repo.load_items.side_effect = load_items_side_effect
        else:
            def default_load_items(board_id: str, column_id: str) -> List[Item]:
                return [item for item in items
                       if item.column_id == column_id]
            mock_repo.load_items.side_effect = default_load_items

        # Set up save_item behavior
        def save_item(board_id: str, column_id: str, item: Item) -> bool:
            # Update existing item or add new one
            existing_index = next(
                (i for i, it in enumerate(items) if it.id == item.id), None
            )
            if existing_index is not None:
                items[existing_index] = item
            else:
                items.append(item)
            return True

        mock_repo.save_item.side_effect = save_item

        # Set up delete_item behavior
        def delete_item(board_id: str, column_id: str, item_id: str) -> bool:
            original_count = len(items)
            items[:] = [item for item in items if item.id != item_id]
            return len(items) < original_count

        mock_repo.delete_item.side_effect = delete_item

        return mock_repo


class MockServiceFactory:
    """Factory for creating mock service instances."""

    @staticmethod
    def create_validation_service(
        validate_board_raises: Optional[Exception] = None,
        validate_column_name_raises: Optional[Exception] = None,
        validate_item_raises: Optional[Exception] = None
    ) -> MagicMock:
        """Create a mock validation service."""
        mock_service = MagicMock(spec=ValidationService)

        # Set up validation methods
        if validate_board_raises:
            mock_service.validate_board.side_effect = validate_board_raises
        else:
            mock_service.validate_board.return_value = None

        if validate_column_name_raises:
            mock_service.validate_column_name.side_effect = validate_column_name_raises
        else:
            mock_service.validate_column_name.return_value = None

        if validate_item_raises:
            mock_service.validate_item.side_effect = validate_item_raises
        else:
            mock_service.validate_item.return_value = None

        return mock_service

    @staticmethod
    def create_logger() -> MagicMock:
        """Create a mock logger."""
        mock_logger = MagicMock(spec=ContextAwareLogger)

        # Make all logging methods no-op by default
        mock_logger.debug.return_value = None
        mock_logger.info.return_value = None
        mock_logger.warning.return_value = None
        mock_logger.error.return_value = None
        mock_logger.critical.return_value = None

        return mock_logger


class MockConfigFactory:
    """Factory for creating mock configuration instances."""

    @staticmethod
    def create_config_manager(
        config_data: Optional[Dict[str, Any]] = None
    ) -> MagicMock:
        """Create a mock configuration manager."""
        mock_config = MagicMock(spec=ConfigurationManager)

        default_config = {
            "data_dir": "/tmp/test_mkanban",
            "log_level": "DEBUG",
            "jira": {
                "enabled": False,
                "url": "https://test.atlassian.net",
                "username": "test@example.com",
                "api_token": "test_token"
            },
            "git": {
                "enabled": True,
                "auto_create_tasks": True
            }
        }

        if config_data:
            default_config.update(config_data)

        # Set up property access
        mock_config.data_dir = default_config["data_dir"]
        mock_config.log_level = default_config["log_level"]
        mock_config.jira_enabled = default_config["jira"]["enabled"]
        mock_config.git_enabled = default_config["git"]["enabled"]

        # Set up method access
        mock_config.get.side_effect = lambda key, default=None: default_config.get(key, default)
        mock_config.get_jira_config.return_value = default_config["jira"]
        mock_config.get_git_config.return_value = default_config["git"]

        return mock_config

    @staticmethod
    def create_path_resolver(
        data_dir: str = "/tmp/test_mkanban",
        session_path: Optional[str] = None
    ) -> MagicMock:
        """Create a mock path resolver."""
        mock_resolver = MagicMock(spec=PathResolver)

        # Set up path resolution
        mock_resolver.get_data_dir.return_value = data_dir
        mock_resolver.get_boards_dir.return_value = f"{data_dir}/boards"
        mock_resolver.get_logs_dir.return_value = f"{data_dir}/logs"

        if session_path:
            mock_resolver.get_session_data_dir.return_value = session_path
        else:
            mock_resolver.get_session_data_dir.return_value = data_dir

        return mock_resolver


class MockBuilder:
    """Builder pattern for creating complex mock setups."""

    def __init__(self):
        self.boards: List[Board] = []
        self.items: List[Item] = []
        self.config_data: Dict[str, Any] = {}

    def with_boards(self, boards: List[Board]) -> 'MockBuilder':
        """Add boards to the mock setup."""
        self.boards = boards
        return self

    def with_items(self, items: List[Item]) -> 'MockBuilder':
        """Add items to the mock setup."""
        self.items = items
        return self

    def with_config(self, config_data: Dict[str, Any]) -> 'MockBuilder':
        """Add configuration data to the mock setup."""
        self.config_data.update(config_data)
        return self

    def build_board_repository(self) -> MagicMock:
        """Build a board repository with the configured data."""
        return MockRepositoryFactory.create_board_repository(self.boards)

    def build_storage_repository(self) -> MagicMock:
        """Build a storage repository with the configured data."""
        return MockRepositoryFactory.create_storage_repository(self.items)

    def build_config_manager(self) -> MagicMock:
        """Build a configuration manager with the configured data."""
        return MockConfigFactory.create_config_manager(self.config_data)

    def build_all(self) -> Dict[str, MagicMock]:
        """Build all mock components."""
        return {
            "board_repository": self.build_board_repository(),
            "storage_repository": self.build_storage_repository(),
            "config_manager": self.build_config_manager(),
            "validation_service": MockServiceFactory.create_validation_service(),
            "logger": MockServiceFactory.create_logger(),
        }