import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.config.configuration_manager import (
    ConfigurationManager,
    DaemonConfiguration,
    LoggingConfiguration,
    get_config,
)
from src.core.types import ThemeType


class TestConfigurationManager:
    """Test cases for the ConfigurationManager class."""

    def setup_method(self):
        """Set up test dependencies."""
        # Reset singleton instance for each test
        ConfigurationManager._instance = None
        ConfigurationManager._config = None

    def test_default_configuration_creation(self):
        """Test that default configuration is created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()
                config = config_manager.config

                assert config.boards_path is not None
                assert config.theme == ThemeType.DARK.value
                assert config.auto_save is True
                assert config.editor == "nvim"
                assert config.cli_editor == "neovide"
                assert isinstance(config.daemon, DaemonConfiguration)
                assert isinstance(config.logging, LoggingConfiguration)

    def test_config_file_persistence(self):
        """Test that configuration is saved to and loaded from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                # Create and modify configuration
                config_manager = ConfigurationManager()
                config_manager.update_configuration(theme="light", editor="vim")

                # Create new instance to test loading
                ConfigurationManager._instance = None
                ConfigurationManager._config = None

                new_config_manager = ConfigurationManager()
                config = new_config_manager.config

                assert config.theme == "light"
                assert config.editor == "vim"

    def test_editor_resolution_priority(self):
        """Test that editor resolution follows correct priority: EDITOR env -> config.editor -> default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()

                # Test config value when no EDITOR env var
                with patch.dict(os.environ, {}, clear=True):
                    assert config_manager.get_editor() == "nvim"  # default from config

                # Test EDITOR env var takes priority
                with patch.dict(os.environ, {"EDITOR": "emacs"}, clear=True):
                    assert config_manager.get_editor() == "emacs"

                # Test custom config value
                config_manager.update_configuration(editor="nano")
                with patch.dict(os.environ, {}, clear=True):
                    assert config_manager.get_editor() == "nano"

    def test_cli_editor_from_config(self):
        """Test that CLI editor comes from config only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()

                # Test default CLI editor
                assert config_manager.get_cli_editor() == "neovide"

                # Test custom CLI editor
                config_manager.update_configuration(cli_editor="code")
                assert config_manager.get_cli_editor() == "code"

    def test_no_environment_variable_overrides(self):
        """Test that MKANBAN_* environment variables are no longer used."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                # Set various MKANBAN_* environment variables
                env_vars = {
                    "MKANBAN_THEME": "light",
                    "MKANBAN_AUTO_SAVE_INTERVAL": "60",
                    "MKANBAN_DEBUG": "true",
                    "MKANBAN_EDITOR": "emacs",
                    "MKANBAN_CLI_EDITOR": "code",
                }

                with patch.dict(os.environ, env_vars, clear=False):
                    config_manager = ConfigurationManager()
                    config = config_manager.config

                    # All should use default values, not environment variables
                    assert config.theme == ThemeType.DARK.value  # default
                    assert config.auto_save_interval == 30  # default
                    assert config.logging.level == "INFO"  # default
                    assert config.editor == "nvim"  # default
                    assert config.cli_editor == "neovide"  # default

    def test_corrupted_config_file_fallback(self):
        """Test that corrupted config file falls back to defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            # Create corrupted JSON file
            config_file.write_text("{ invalid json")

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()
                config = config_manager.config

                # Should fall back to defaults
                assert config.theme == ThemeType.DARK.value
                assert config.editor == "nvim"

    def test_nested_configuration_loading(self):
        """Test that nested configurations (daemon, logging, jira) are loaded properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            # Create config with nested structures
            config_data = {
                "theme": "light",
                "daemon": {
                    "enabled": False,
                    "polling_interval": 10,
                    "jira": {
                        "enabled": True,
                        "api_url": "https://test.atlassian.net",
                        "project_keys": ["TEST"]
                    }
                },
                "logging": {
                    "level": "DEBUG",
                    "max_log_files": 50
                }
            }

            config_file.write_text(json.dumps(config_data, indent=2))

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()
                config = config_manager.config

                assert config.theme == "light"
                assert config.daemon.enabled is False
                assert config.daemon.polling_interval == 10
                assert config.daemon.jira.enabled is True
                assert config.daemon.jira.api_url == "https://test.atlassian.net"
                assert config.daemon.jira.project_keys == ["TEST"]
                assert config.logging.level == "DEBUG"
                assert config.logging.max_log_files == 50

    def test_singleton_behavior(self):
        """Test that ConfigurationManager maintains singleton behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config1 = ConfigurationManager()
                config2 = ConfigurationManager()
                config3 = get_config()

                assert config1 is config2
                assert config2 is config3

    def test_update_and_save_configuration(self):
        """Test updating and saving configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()

                # Update multiple fields
                config_manager.update_configuration(
                    theme="light",
                    auto_save=False,
                    editor="vim",
                    cli_editor="code"
                )

                # Verify updates
                config = config_manager.config
                assert config.theme == "light"
                assert config.auto_save is False
                assert config.editor == "vim"
                assert config.cli_editor == "code"

                # Verify persistence
                assert config_file.exists()
                saved_data = json.loads(config_file.read_text())
                assert saved_data["theme"] == "light"
                assert saved_data["auto_save"] is False
                assert saved_data["editor"] == "vim"
                assert saved_data["cli_editor"] == "code"

    def test_debug_mode_detection(self):
        """Test debug mode detection from logging level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()

                # Default should not be debug mode
                assert not config_manager.is_debug_mode()

                # Update to debug level
                config_manager.config.logging.level = "DEBUG"
                assert config_manager.is_debug_mode()

    def test_path_resolution(self):
        """Test path resolution methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            boards_path = str(Path(temp_dir) / "boards")
            config_dir = str(Path(temp_dir) / "config")

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()
                config_manager.update_configuration(
                    boards_path=boards_path,
                    config_dir=config_dir
                )

                assert config_manager.get_boards_path() == Path(boards_path).resolve()
                assert config_manager.get_config_dir() == Path(config_dir).resolve()

    def test_reload_configuration(self):
        """Test configuration reloading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            with patch("src.config.configuration_manager.DEFAULT_CONFIG_FILE", config_file):
                config_manager = ConfigurationManager()

                # Get initial theme
                initial_theme = config_manager.config.theme

                # Manually modify config file
                config_data = json.loads(config_file.read_text())
                config_data["theme"] = "custom"
                config_file.write_text(json.dumps(config_data, indent=2))

                # Reload and verify change
                config_manager.reload_configuration()
                assert config_manager.config.theme == "custom"
                assert config_manager.config.theme != initial_theme