# Storage and Repository Layer

The storage layer provides a clean abstraction over the file system, implementing the repository pattern to separate storage concerns from business logic.

## Overview

The storage layer consists of:

- **Repository Interfaces**: Abstract contracts for storage operations
- **Markdown Repositories**: Concrete implementations using markdown files
- **Storage Separation**: Board-level vs item-level storage responsibilities
- **File System Abstraction**: Safe file operations with error handling

## Repository Pattern

MKanban uses the repository pattern to separate storage concerns:

### Interfaces

```python
# Board-level storage operations
class BoardRepository(ABC):
    @abstractmethod
    def load_board(self, name: str, base_path: Optional[Path] = None) -> Optional[Board]:
        pass

    @abstractmethod
    def save_board(self, board: Board, base_path: Optional[Path] = None) -> bool:
        pass

# Item-level storage operations
class StorageRepository(ABC):
    @abstractmethod
    def save_item(self, board: Board, item: Item, column: Column) -> bool:
        pass

    @abstractmethod
    def load_items_from_column(self, board: Board, column: Column) -> List[Item]:
        pass
```

### Benefits

- **Testability**: Easy to mock storage for unit tests
- **Flexibility**: Can swap storage backends without changing business logic
- **Separation**: Clear boundary between domain and infrastructure concerns
- **Single Responsibility**: Board vs item storage are separate concerns

## MarkdownBoardRepository

Handles board-level storage operations using markdown files.

### Constructor

```python
class MarkdownBoardRepository:
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger
```

### Board Operations

#### Loading Boards

```python
def load_board(self, name: str, base_path: Optional[Path] = None) -> Optional[Board]:
    """Load a board from the file system."""

def load_all_boards(self, base_path: Optional[Path] = None) -> List[Board]:
    """Load all available boards."""

def board_exists(self, name: str, base_path: Optional[Path] = None) -> bool:
    """Check if a board exists."""
```

**Implementation Details:**
- Reads `kanban.md` file in board directory
- Parses YAML frontmatter for board metadata
- Creates `Board` object with columns
- Handles missing or corrupted files gracefully

**File Format:**
```markdown
---
name: "my-project"
columns:
  - name: "to-do"
    position: 0
  - name: "in-progress"
    position: 1
  - name: "done"
    position: 2
created_at: "2024-01-01T10:00:00"
---

# My Project Board

This board tracks project tasks.
```

#### Saving Boards

```python
def save_board(self, board: Board, base_path: Optional[Path] = None) -> bool:
    """Save a board to the file system."""

def create_board_structure(self, board: Board, base_path: Optional[Path] = None) -> bool:
    """Create the directory structure for a new board."""
```

**Implementation Details:**
- Creates board directory if it doesn't exist
- Writes `kanban.md` with board metadata
- Creates column directories
- Sets up proper file permissions

#### Board Management

```python
def delete_board(self, name: str, base_path: Optional[Path] = None) -> bool:
    """Delete a board and all its contents."""

def rename_board(self, old_name: str, new_name: str, base_path: Optional[Path] = None) -> bool:
    """Rename a board directory."""
```

### Usage Example

```python
from src.core.dependency_container import get_container

# Get repository from container
container = get_container()
board_repo = container.get(MarkdownBoardRepository)

# Load board
board = board_repo.load_board("my-project")
if board:
    print(f"Loaded board: {board.name}")

# Save board
success = board_repo.save_board(board)
if success:
    print("Board saved successfully")
```

### Logging

```python
# Loading
self.logger.debug("Loading board from path", board=name, path=str(board_path))
self.logger.info("Board loaded successfully", board=name, columns=len(board.columns))

# Saving
self.logger.debug("Saving board to path", board=board.name, path=str(board_path))
self.logger.info("Board saved successfully", board=board.name)

# Errors
self.logger.error("Failed to load board", board=name, error=str(e))
```

## MarkdownStorageRepository

Handles item-level storage operations within board structures.

### Constructor

```python
class MarkdownStorageRepository:
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger
```

### Item Operations

#### Loading Items

```python
def load_items_from_column(self, board: Board, column: Column) -> List[Item]:
    """Load all items from a specific column."""

def load_item(self, board: Board, item_id: str) -> Optional[Item]:
    """Load a specific item by ID."""

def get_item_file_path(self, board: Board, item: Item, column: Column) -> Path:
    """Get the file path for an item."""
```

**Implementation Details:**
- Scans column directory for `.md` files
- Parses YAML frontmatter for item metadata
- Handles parent/child relationships
- Sorts items by creation date or position

**Item File Format:**
```markdown
---
id: "abc123"
title: "Fix authentication bug"
status: "in-progress"
created_at: "2024-01-01T10:00:00"
updated_at: "2024-01-01T11:00:00"
parent: "parent-item-id"
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

#### Saving Items

```python
def save_item(self, board: Board, item: Item, column: Column) -> bool:
    """Save an item to a specific column."""

def save_items_to_column(self, board: Board, items: List[Item], column: Column) -> bool:
    """Save multiple items to a column."""
```

**Implementation Details:**
- Generates unique filename if needed
- Creates column directory if missing
- Writes item with YAML frontmatter
- Updates timestamps automatically

#### Item Management

```python
def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
    """Delete an item from a specific column."""

def move_item_between_columns(
    self,
    board: Board,
    item: Item,
    source_column: Column,
    target_column: Column
) -> bool:
    """Move an item from one column to another."""
```

### Directory Structure

Items are organized in a hierarchical directory structure:

```
boards/my-project/
├── kanban.md                    # Board metadata
├── to-do/                       # Column directory
│   ├── column.md               # Column metadata (optional)
│   ├── fix-auth-bug-abc123.md  # Item file
│   └── update-docs-def456.md   # Item file
├── in-progress/
│   └── refactor-api-ghi789.md
└── done/
    └── setup-ci-jkl012.md
```

### Usage Example

```python
# Get repository
storage_repo = container.get(MarkdownStorageRepository)

# Load items from column
items = storage_repo.load_items_from_column(board, todo_column)
print(f"Found {len(items)} items in {todo_column.name}")

# Save new item
success = storage_repo.save_item(board, new_item, todo_column)
if success:
    print("Item saved successfully")

# Move item between columns
success = storage_repo.move_item_between_columns(
    board, item, todo_column, in_progress_column
)
```

### Logging

```python
# Loading
self.logger.debug("Loading items from column",
                 board=board.name, column=column.name, path=str(column_path))
self.logger.info("Items loaded from column",
                board=board.name, column=column.name, count=len(items))

# Saving
self.logger.debug("Saving item to column",
                 board=board.name, column=column.name, item=item.title)
self.logger.info("Item saved successfully",
                board=board.name, column=column.name, item=item.title)

# Moving
self.logger.debug("Moving item between columns",
                 board=board.name, item=item.title,
                 source=source_column.name, target=target_column.name)
```

## File Operations Utility

The `FileOperations` class provides safe, logged file system operations.

### Constructor

```python
class FileOperations:
    def __init__(self, logger: ContextAwareLogger):
        self.logger = logger
```

### Core Operations

```python
def ensure_directory_exists(self, path: Path) -> bool:
    """Ensure a directory exists, creating it if necessary."""

def safe_write_file(self, file_path: Path, content: str) -> bool:
    """Safely write content to a file with error handling."""

def safe_read_file(self, file_path: Path) -> Optional[str]:
    """Safely read content from a file."""

def safe_delete_file(self, file_path: Path) -> bool:
    """Safely delete a file."""

def safe_move_file(self, source: Path, destination: Path) -> bool:
    """Safely move a file from source to destination."""
```

### Error Handling

```python
def safe_write_file(self, file_path: Path, content: str) -> bool:
    try:
        self.ensure_directory_exists(file_path.parent)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.debug("File written successfully", path=str(file_path))
        return True

    except IOError as e:
        self.logger.error("Failed to write file", path=str(file_path), error=str(e))
        return False
    except Exception as e:
        self.logger.error("Unexpected error writing file", path=str(file_path), error=str(e))
        return False
```

## Path Resolution

The `PathResolver` provides centralized path management with session awareness.

### Session-Based Paths

```python
def get_boards_directory(self) -> Path:
    """Get the directory where board folders are located."""

def get_session_based_data_dir(self) -> Path:
    """Get data directory based on tmux session."""

def get_board_path(self, board_name: str, base_path: Optional[Path] = None) -> Path:
    """Get the path to a specific board directory."""
```

### Usage with MKANBAN_PATH

```python
# If MKANBAN_PATH is set
export MKANBAN_PATH="/home/user/projects/current-project"
# Result: /home/user/projects/current-project/

# If not set, uses session-based approach
# Result: ~/.mkanban/boards/{session_name}/
```

## Error Handling Strategy

### Repository Level

```python
def load_board(self, name: str) -> Optional[Board]:
    try:
        # Attempt to load board
        return self._load_board_from_file(name)
    except FileNotFoundError:
        self.logger.warning("Board file not found", board=name)
        return None
    except PermissionError:
        self.logger.error("Permission denied accessing board", board=name)
        return None
    except Exception as e:
        self.logger.error("Unexpected error loading board", board=name, error=str(e))
        return None
```

### File Operations Level

```python
def safe_read_file(self, file_path: Path) -> Optional[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        self.logger.debug("File not found", path=str(file_path))
        return None
    except PermissionError:
        self.logger.error("Permission denied reading file", path=str(file_path))
        return None
    except UnicodeDecodeError:
        self.logger.error("File encoding error", path=str(file_path))
        return None
```

## Testing Strategy

### Unit Testing with Mocks

```python
def test_board_loading():
    # Mock dependencies
    mock_path_resolver = Mock()
    mock_logger = Mock()

    # Create repository
    repo = MarkdownBoardRepository(mock_path_resolver, mock_logger)

    # Test loading
    board = repo.load_board("test-board")

    # Verify interactions
    mock_path_resolver.get_board_path.assert_called_once_with("test-board", None)
```

### Integration Testing

```python
def test_full_storage_cycle(tmp_path):
    # Create real repository with test path
    path_resolver = PathResolver(test_config)
    logger = Mock()
    repo = MarkdownBoardRepository(path_resolver, logger)

    # Test complete cycle
    board = Board(name="test", columns=[...])

    # Save
    success = repo.save_board(board)
    assert success

    # Load
    loaded_board = repo.load_board("test")
    assert loaded_board.name == "test"
```

## Best Practices

### Repository Implementation

1. **Single Responsibility**: Separate board and item storage
2. **Error Handling**: Always handle file system errors gracefully
3. **Logging**: Log all operations with appropriate context
4. **Path Safety**: Use PathResolver for all path operations
5. **Atomic Operations**: Ensure save operations are atomic when possible

### Using Repositories

1. **Dependency Injection**: Get repositories from container
2. **Handle None Returns**: Always check for None returns
3. **Error Monitoring**: Monitor logs for storage errors
4. **Path Management**: Use provided path resolution methods

```python
# Good usage
board_repo = container.get(MarkdownBoardRepository)
board = board_repo.load_board("my-project")
if board:
    # Process board
    success = board_repo.save_board(board)
    if not success:
        print("Failed to save board")
else:
    print("Board not found")

# Avoid direct file operations
# with open("/path/to/board.md") as f:  # Don't do this
```

The storage layer provides a robust, well-tested foundation for all data persistence in MKanban, with comprehensive error handling and logging throughout.