import pytest
from unittest.mock import MagicMock

from src.core.dependency_container import DependencyContainer, get_container, set_container
from src.config.configuration_manager import ConfigurationManager
from src.services.board_service import BoardService
from src.services.item_service import ItemService


class TestDependencyContainer:
    """Test cases for the DependencyContainer class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.container = DependencyContainer()

    def test_get_registered_service(self):
        """Test getting a registered service."""
        config_manager = self.container.get(ConfigurationManager)

        assert config_manager is not None
        assert isinstance(config_manager, ConfigurationManager)

    def test_singleton_behavior(self):
        """Test that services are returned as singletons."""
        config1 = self.container.get(ConfigurationManager)
        config2 = self.container.get(ConfigurationManager)

        assert config1 is config2

    def test_dependency_injection(self):
        """Test that dependencies are properly injected."""
        board_service = self.container.get(BoardService)

        assert board_service is not None
        assert isinstance(board_service, BoardService)

    def test_register_custom_factory(self):
        """Test registering a custom factory."""
        mock_service = MagicMock()
        self.container.register_factory(str, lambda: mock_service)

        result = self.container.get(str)

        assert result is mock_service

    def test_register_instance(self):
        """Test registering a specific instance."""
        mock_config = MagicMock()
        self.container.register_instance(ConfigurationManager, mock_config)

        result = self.container.get(ConfigurationManager)

        assert result is mock_config

    def test_clear_instances(self):
        """Test clearing all instances."""
        # Get a service to create instance
        config1 = self.container.get(ConfigurationManager)

        # Clear instances
        self.container.clear_instances()

        # Get service again - should be new instance
        config2 = self.container.get(ConfigurationManager)

        assert config1 is not config2

    def test_setup_for_testing(self):
        """Test setting up container for testing."""
        # Get a service to create instance
        config1 = self.container.get(ConfigurationManager)

        # Setup for testing
        self.container.setup_for_testing()

        # Get service again - should be new instance
        config2 = self.container.get(ConfigurationManager)

        assert config1 is not config2

    def test_get_logger_convenience_methods(self):
        """Test logger convenience methods."""
        daemon_logger = self.container.get_daemon_logger("test")
        tui_logger = self.container.get_tui_logger("test")

        assert daemon_logger is not None
        assert tui_logger is not None

    def test_unregistered_service_raises_error(self):
        """Test that requesting unregistered service raises error."""
        class UnregisteredService:
            pass

        with pytest.raises(ValueError) as exc_info:
            self.container.get(UnregisteredService)

        assert "No factory registered" in str(exc_info.value)

    def test_global_container_functions(self):
        """Test global container access functions."""
        global_container = get_container()
        assert global_container is not None

        # Test setting custom container
        custom_container = DependencyContainer()
        set_container(custom_container)

        new_global = get_container()
        assert new_global is custom_container

    def test_complex_dependency_chain(self):
        """Test that complex dependency chains work correctly."""
        # BoardService depends on BoardRepository, ValidationService, and Logger
        # These in turn depend on other services
        board_service = self.container.get(BoardService)
        item_service = self.container.get(ItemService)

        assert board_service is not None
        assert item_service is not None

        # Verify dependencies are injected
        assert hasattr(board_service, '_repository')
        assert hasattr(board_service, '_validator')
        assert hasattr(board_service, '_logger')

        assert hasattr(item_service, '_storage')
        assert hasattr(item_service, '_validator')
        assert hasattr(item_service, '_logger')