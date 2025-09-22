# API Reference

This document provides a comprehensive reference for MKanban's APIs, including services, repositories, utilities, and models.

## Quick Reference

### Core Services

- [BoardService](services.md#boardservice) - Board management operations
- [ItemService](services.md#itemservice) - Item CRUD and relationships
- [ValidationService](services.md#validationservice) - Data validation

### Repositories

- [MarkdownBoardRepository](repositories.md#markdownboardrepository) - Board storage
- [MarkdownStorageRepository](repositories.md#markdownstoragerepository) - Item storage

### Utilities

- [ConfigurationManager](utilities.md#configurationmanager) - Configuration management
- [PathResolver](utilities.md#pathresolver) - Path resolution
- [LoggerFactory](utilities.md#loggerfactory) - Logging infrastructure
- [FileOperations](utilities.md#fileoperations) - Safe file operations

### Models

- [Board](models.md#board) - Board entity
- [Column](models.md#column) - Column entity
- [Item](models.md#item) - Item entity with Git/JIRA support
- [Parent](models.md#parent) - Parent grouping entity

## Dependency Injection

All services and utilities are managed through the dependency injection container:

```python
from src.core.dependency_container import get_container

# Get services
container = get_container()
board_service = container.get(BoardService)
item_service = container.get(ItemService)

# Or use convenience functions
from src.core.dependency_container import get_board_service, get_item_service
board_service = get_board_service()
item_service = get_item_service()
```

## Error Handling

MKanban uses Python exceptions with comprehensive logging:

```python
try:
    board = board_service.load_board("my-project")
except BoardNotFoundError:
    print("Board not found")
except StorageError as e:
    print(f"Storage error: {e}")
```

Most service methods also return `None` or `False` for failure cases:

```python
board = board_service.load_board("my-project")
if board is None:
    print("Failed to load board")

success = board_service.save_board(board)
if not success:
    print("Failed to save board")
```

## Configuration

Access configuration through the ConfigurationManager:

```python
from src.core.dependency_container import get_config_manager

config_manager = get_config_manager()
config = config_manager.config

# Access nested configuration
daemon_config = config.daemon
jira_config = config.daemon.jira
logging_config = config.logging
```

## Logging

Use context-aware loggers throughout the application:

```python
from src.core.dependency_container import get_daemon_logger

logger = get_daemon_logger("my_component")

# Set persistent context
logger.set_context(board="my-project", user="john")

# Log with temporary context
logger.info("Processing item", item="task-123", operation="update")

# Use context manager
with logger.with_context(batch_id="batch-456"):
    logger.debug("Batch processing started")
    # All logs in this block include batch_id
```

## Common Patterns

### Service Layer Pattern

```python
class MyService:
    def __init__(
        self,
        dependency1: SomeDependency,
        dependency2: AnotherDependency,
        logger: ContextAwareLogger
    ):
        self._dep1 = dependency1
        self._dep2 = dependency2
        self._logger = logger

    def perform_operation(self, data: str) -> bool:
        self._logger.info("Starting operation", data=data)

        try:
            result = self._dep1.process(data)
            if result:
                self._dep2.save(result)
                self._logger.info("Operation completed successfully")
                return True
            else:
                self._logger.warning("Processing failed")
                return False

        except Exception as e:
            self._logger.error("Operation failed", error=str(e))
            return False
```

### Repository Pattern

```python
class MyRepository:
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger

    def save_item(self, item: MyItem) -> bool:
        try:
            path = self.path_resolver.get_item_path(item.id)
            content = self._serialize_item(item)

            file_ops = get_container().get(FileOperations)
            success = file_ops.safe_write_file(path, content)

            if success:
                self.logger.info("Item saved", item_id=item.id)
            else:
                self.logger.error("Failed to save item", item_id=item.id)

            return success

        except Exception as e:
            self.logger.error("Error saving item", item_id=item.id, error=str(e))
            return False
```

### Model Pattern

```python
from pydantic import BaseModel, Field
from src.utils.date_utils import now

class MyModel(BaseModel):
    id: str = Field(default="")
    name: str
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = generate_id_from_name(self.name) or "unnamed"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()
```

## Type Definitions

Common type aliases used throughout the codebase:

```python
from src.core.types import (
    ItemId,        # str
    ColumnId,      # str
    BoardId,       # str
    ParentId,      # str
    FilePath,      # Union[str, Path]
    Timestamp,     # datetime
    Metadata,      # Dict[str, Union[str, int, bool, List, Dict]]
)
```

## Environment Variables

Configuration can be overridden with environment variables:

```bash
export MKANBAN_DATA_DIR="/custom/path"
export MKANBAN_CONFIG_DIR="/custom/config"
export MKANBAN_THEME="light"
export MKANBAN_DEBUG="true"
export MKANBAN_PATH="/project/specific/path"
```

## File Formats

### Board File (kanban.md)

```markdown
---
name: "My Project"
columns:
  - name: "To Do"
    position: 0
  - name: "In Progress"
    position: 1
  - name: "Done"
    position: 2
created_at: "2024-01-01T10:00:00"
---

# My Project Board

Board description goes here.
```

### Item File (item.md)

```markdown
---
id: "fix-auth-bug"
title: "Fix authentication bug"
column_id: "in-progress"
parent_id: "auth-parent"
created_at: "2024-01-01T10:00:00"
updated_at: "2024-01-01T11:00:00"
is_git_managed: true
git_metadata:
  repository_path: "/home/user/project"
  branch_name: "feature/fix-auth"
  is_current_branch: true
---

# Fix authentication bug

The login form is not validating credentials properly.

## Steps to reproduce
1. Go to login page
2. Enter invalid credentials
3. Form should show error

## Expected behavior
Show clear error message to user.
```

## Testing APIs

All APIs are designed to be easily testable:

```python
# Service testing with mocks
def test_board_service():
    mock_repository = Mock()
    mock_validator = Mock()
    mock_logger = Mock()

    service = BoardService(mock_repository, mock_validator, mock_logger)

    # Test operations
    board = service.create_board("test")
    assert board.name == "test"

# Repository testing with temp directories
def test_repository():
    with TemporaryDirectory() as temp_dir:
        path_resolver = Mock()
        path_resolver.get_board_path.return_value = Path(temp_dir)

        repository = MarkdownBoardRepository(path_resolver, Mock())

        # Test storage operations
        board = Board(name="test")
        success = repository.save_board(board)
        assert success
```

## Migration Guide

### From Legacy Code

When migrating from legacy patterns:

```python
# Old pattern
from src.config.settings import Settings
settings = Settings.load()

# New pattern
from src.core.dependency_container import get_config_manager
config_manager = get_config_manager()
settings = config_manager.config
```

```python
# Old pattern
repository = MarkdownStorageImpl()
service = BoardService(repository)

# New pattern
from src.core.dependency_container import get_board_service
service = get_board_service()
```

For detailed API documentation, see the individual module documentation files.