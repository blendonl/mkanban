import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from typing import Generator

from src.core.dependency_container import DependencyContainer, set_container
from src.config.configuration_manager import ConfigurationManager
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import LoggerFactory
from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.domain.entities.parent import Parent


@pytest.fixture(scope="session")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="mkanban_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config_manager(temp_data_dir: Path) -> ConfigurationManager:
    """Create a test configuration manager with temporary data directory."""
    config = ConfigurationManager()
    config._config_data = {
        "data_dir": str(temp_data_dir),
        "log_level": "DEBUG",
        "jira": {
            "enabled": False,
            "url": "https://test.atlassian.net",
            "username": "test@example.com",
            "api_token": "test_token"
        }
    }
    return config


@pytest.fixture
def test_path_resolver(test_config_manager: ConfigurationManager) -> PathResolver:
    """Create a test path resolver."""
    return PathResolver(test_config_manager)


@pytest.fixture
def test_logger_factory(test_config_manager: ConfigurationManager, test_path_resolver: PathResolver) -> LoggerFactory:
    """Create a test logger factory."""
    return LoggerFactory(test_config_manager, test_path_resolver)


@pytest.fixture
def test_container(temp_data_dir: Path) -> Generator[DependencyContainer, None, None]:
    """Create a test dependency container with mocked dependencies."""
    container = DependencyContainer()

    # Create test config
    config = ConfigurationManager()
    config._config_data = {
        "data_dir": str(temp_data_dir),
        "log_level": "DEBUG",
        "jira": {"enabled": False}
    }

    # Register test instances
    container.register_instance(ConfigurationManager, config)
    container.register_instance(PathResolver, PathResolver(config))
    container.register_instance(LoggerFactory, LoggerFactory(config, PathResolver(config)))

    # Set as global container
    original_container = None
    try:
        set_container(container)
        yield container
    finally:
        set_container(original_container)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock()


@pytest.fixture
def sample_board() -> Board:
    """Create a sample board for testing."""
    board = Board(
        name="Test Board",
        description="A test board for unit testing"
    )

    # Add some columns
    todo_column = board.add_column("To Do", 0)
    in_progress_column = board.add_column("In Progress", 1)
    done_column = board.add_column("Done", 2)

    # Add some items
    todo_column.items.append(Item(
        title="Task 1",
        description="First test task",
        column_id=todo_column.id
    ))

    in_progress_column.items.append(Item(
        title="Task 2",
        description="Second test task",
        column_id=in_progress_column.id
    ))

    return board


@pytest.fixture
def sample_column() -> Column:
    """Create a sample column for testing."""
    column = Column(name="Test Column", position=0)

    # Add some items
    column.items.append(Item(
        title="Test Item 1",
        description="First test item",
        column_id=column.id
    ))

    column.items.append(Item(
        title="Test Item 2",
        description="Second test item",
        column_id=column.id
    ))

    return column


@pytest.fixture
def sample_item() -> Item:
    """Create a sample item for testing."""
    return Item(
        title="Sample Task",
        description="A sample task for testing",
        tags=["test", "sample"],
        status="To Do"
    )


@pytest.fixture
def sample_parent() -> Parent:
    """Create a sample parent for testing."""
    return Parent(
        name="Test Epic",
        color="blue",
        description="A test epic for grouping tasks"
    )


@pytest.fixture(autouse=True)
def reset_dependency_container():
    """Reset dependency container after each test."""
    yield
    # Clear any test instances
    try:
        from src.core.dependency_container import get_container
        container = get_container()
        container.clear_instances()
    except:
        pass


class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def create_test_board_structure(base_path: Path, board_name: str = "test-board") -> Path:
        """Create a test board directory structure."""
        board_path = base_path / "boards" / board_name
        board_path.mkdir(parents=True, exist_ok=True)

        # Create kanban.md file
        kanban_file = board_path / "kanban.md"
        kanban_content = f"""---
name: {board_name}
description: Test board
columns:
  - name: To Do
    position: 0
  - name: In Progress
    position: 1
  - name: Done
    position: 2
---

# {board_name}

Test board for unit testing.
"""
        kanban_file.write_text(kanban_content)

        # Create column directories
        for column in ["to-do", "in-progress", "done"]:
            column_path = board_path / column
            column_path.mkdir(exist_ok=True)

        return board_path

    @staticmethod
    def create_test_item_file(column_path: Path, title: str, description: str = "") -> Path:
        """Create a test item markdown file."""
        item_file = column_path / f"{title.lower().replace(' ', '-')}.md"
        content = f"""---
title: {title}
description: {description}
status: To Do
tags: [test]
---

# {title}

{description}
"""
        item_file.write_text(content)
        return item_file


@pytest.fixture
def test_helpers():
    """Provide test helper methods."""
    return TestHelpers