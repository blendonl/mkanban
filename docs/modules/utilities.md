# Utilities

The utilities layer provides cross-cutting concerns and common functionality used throughout MKanban, including path management, logging infrastructure, and file operations.

## Overview

Core utilities include:

- **PathResolver**: Centralized path management with session awareness
- **LoggerFactory**: Context-aware logging infrastructure
- **FileOperations**: Safe file system operations
- **ContextAwareLogger**: Enhanced logging with structured metadata

## PathResolver

The `PathResolver` centralizes all path-related operations and provides session-aware directory management.

### Constructor

```python
class PathResolver:
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self._tmux_manager = None  # Lazy-loaded to avoid circular imports
```

### Core Path Methods

#### Data Directory Resolution

```python
def get_data_dir(self) -> Path:
    """Get the base data directory from configuration."""

def get_session_based_data_dir(self) -> Path:
    """Get data directory based on tmux session, fall back to configured data_dir."""

def get_boards_directory(self, base_path: Optional[Path] = None) -> Path:
    """Get the directory where board folders are located."""
```

**Usage:**
```python
from src.core.dependency_container import get_container

path_resolver = get_container().get(PathResolver)

# Get base data directory
data_dir = path_resolver.get_data_dir()
# → /home/user/.mkanban/boards

# Get session-aware directory
session_dir = path_resolver.get_session_based_data_dir()
# → /home/user/.mkanban/boards/my-session (if in tmux)
# → /home/user/.mkanban/boards (if not in tmux)

# Get boards directory
boards_dir = path_resolver.get_boards_directory()
```

#### Board Path Resolution

```python
def get_board_path(self, board_name: str, base_path: Optional[Path] = None) -> Path:
    """Get the path to a specific board directory."""

def get_board_file_path(self, board_name: str, base_path: Optional[Path] = None) -> Path:
    """Get the path to a board's kanban.md file."""

def get_column_path(self, board_name: str, column_name: str, base_path: Optional[Path] = None) -> Path:
    """Get the path to a specific column directory."""
```

**Usage:**
```python
# Get board directory
board_path = path_resolver.get_board_path("my-project")
# → /home/user/.mkanban/boards/my-session/my-project

# Get board file
board_file = path_resolver.get_board_file_path("my-project")
# → /home/user/.mkanban/boards/my-session/my-project/kanban.md

# Get column directory
column_path = path_resolver.get_column_path("my-project", "todo")
# → /home/user/.mkanban/boards/my-session/my-project/todo
```

### Session Awareness

The PathResolver integrates with tmux session management:

#### MKANBAN_PATH Environment Variable

```python
def _get_mkanban_path(self) -> Optional[str]:
    """Get MKANBAN_PATH environment variable."""
    return self.config_manager.get_mkanban_path()
```

**Behavior:**
- **If `MKANBAN_PATH` is set**: Uses the path directly as boards directory
- **If not set**: Uses session-based path `~/.mkanban/boards/{session_name}`
- **Fallback**: Uses configured `data_dir` if tmux detection fails

#### Session Detection

```python
def get_session_based_data_dir(self) -> Path:
    """Get data directory based on tmux session."""
    try:
        # Get current tmux session
        current_session = self._get_tmux_manager().get_current_session()
        if current_session:
            mkanban_path = self._get_mkanban_path()
            if mkanban_path:
                # Use MKANBAN_PATH directly
                session_path = Path(mkanban_path).expanduser().resolve()
            else:
                # Use session-based path
                session_path = Path.home() / ".mkanban" / "boards" / current_session.name

            session_path.mkdir(parents=True, exist_ok=True)
            return session_path
    except Exception:
        # Fall back to configured data_dir
        pass

    return self.get_data_dir()
```

### Path Utilities

```python
def ensure_path_exists(self, path: Path) -> bool:
    """Ensure a path exists, creating directories as needed."""

def get_relative_path(self, path: Path, base_path: Optional[Path] = None) -> Path:
    """Get a path relative to the base path."""

def is_valid_board_name(self, name: str) -> bool:
    """Check if a board name is valid for file system use."""
```

## LoggerFactory

The `LoggerFactory` creates context-aware loggers with structured metadata and component-specific formatting.

### Constructor

```python
class LoggerFactory:
    def __init__(self, config_manager: ConfigurationManager, path_resolver: PathResolver):
        self.config_manager = config_manager
        self.path_resolver = path_resolver
        self._loggers: Dict[str, ContextAwareLogger] = {}
```

### Logger Creation

#### Component-Specific Loggers

```python
def get_logger(self, name: str, component: str = "daemon") -> ContextAwareLogger:
    """Get a logger for a specific component."""

def get_daemon_logger(self, name: str) -> ContextAwareLogger:
    """Get a daemon-specific logger with timestamped files."""

def get_tui_logger(self, name: str) -> ContextAwareLogger:
    """Get a TUI-specific logger for interactive sessions."""
```

**Usage:**
```python
logger_factory = get_container().get(LoggerFactory)

# Get daemon logger (for background operations)
daemon_logger = logger_factory.get_daemon_logger("board_service")

# Get TUI logger (for interactive sessions)
tui_logger = logger_factory.get_tui_logger("keyboard_handler")

# Get generic logger
logger = logger_factory.get_logger("custom_component", "daemon")
```

### Logger Configuration

#### Timestamped Daemon Logs

```python
def _setup_daemon_logging(self) -> None:
    """Set up daemon logging with timestamped files."""
    if self.config_manager.config.logging.create_timestamped_daemon_logs:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"daemon_{timestamp}.log"
    else:
        log_file = "daemon.log"
```

#### Log Directories

- **Daemon logs**: `~/.mkanban/logs/daemon/`
- **TUI logs**: `~/.mkanban/logs/tui/`
- **Custom paths**: Configurable via `LoggingConfiguration`

### Log Rotation

```python
def _cleanup_old_logs(self, log_dir: Path) -> None:
    """Remove old log files beyond the configured limit."""
    max_files = self.config_manager.config.logging.max_log_files

    log_files = sorted(
        log_dir.glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    for old_file in log_files[max_files:]:
        old_file.unlink()
```

## ContextAwareLogger

Enhanced logger that adds structured context to all log messages.

### Constructor

```python
class ContextAwareLogger:
    def __init__(self, logger: logging.Logger, component: str = "daemon"):
        self.logger = logger
        self.component = component
        self._context: Dict[str, Any] = {}
```

### Context Management

#### Setting Context

```python
def set_context(self, **context) -> None:
    """Set persistent context for this logger."""

def update_context(self, **context) -> None:
    """Update context with new values."""

def clear_context(self) -> None:
    """Clear all context."""
```

**Usage:**
```python
# Set persistent context
logger.set_context(board="my-project", session="development")

# All subsequent logs include this context
logger.info("Processing items")
# → [2024-01-01T10:00:00] DAEMON INFO component: Processing items [board=my-project, session=development]

# Update context
logger.update_context(column="todo", item_count=5)
logger.debug("Items loaded")
# → [board=my-project, session=development, column=todo, item_count=5]
```

#### Temporary Context

```python
def with_context(self, **context) -> ContextManager:
    """Temporarily add context for a block of operations."""
```

**Usage:**
```python
with logger.with_context(operation="sync", jira_ticket="PROJ-123"):
    logger.info("Starting sync")
    # → [board=my-project, operation=sync, jira_ticket=PROJ-123]

    logger.debug("Fetching data")
    # → [board=my-project, operation=sync, jira_ticket=PROJ-123]
# Context automatically removed after block
```

### Logging Methods

#### Standard Levels

```python
def debug(self, message: str, **extra_context) -> None:
def info(self, message: str, **extra_context) -> None:
def warning(self, message: str, **extra_context) -> None:
def error(self, message: str, **extra_context) -> None:
def critical(self, message: str, **extra_context) -> None:
```

**Usage:**
```python
# Simple logging
logger.info("Board loaded")

# With extra context
logger.debug("Processing item", item="Fix bug", status="in-progress")

# Error logging
logger.error("Failed to save", error="Permission denied", path="/invalid/path")
```

### Message Formatting

#### Context Integration

```python
def _format_message(self, message: str, extra_context: Optional[Dict[str, Any]] = None) -> str:
    """Format message with context information."""

    # Combine persistent and temporary context
    full_context = {**self._context}
    if extra_context:
        full_context.update(extra_context)

    # Special handling for JIRA tickets
    if jira_ticket := full_context.get("jira_ticket"):
        context_parts.append(f"JIRA:{jira_ticket}")

    # Format context as key=value pairs
    if context_parts:
        context_str = ", ".join(context_parts)
        return f"{message} [{context_str}]"

    return message
```

#### JIRA Integration

Special formatting for JIRA-related operations:

```python
logger.info("Syncing ticket", jira_ticket="PROJ-123")
# → [2024-01-01T10:00:00] DAEMON INFO jira_service: [JIRA:PROJ-123] Syncing ticket [board=jira-tickets]
```

## FileOperations

Safe file system operations with comprehensive error handling and logging.

### Constructor

```python
class FileOperations:
    def __init__(self, logger: ContextAwareLogger):
        self.logger = logger
```

### Core Operations

#### Directory Operations

```python
def ensure_directory_exists(self, path: Path) -> bool:
    """Ensure a directory exists, creating it if necessary."""

def safe_remove_directory(self, path: Path, recursive: bool = False) -> bool:
    """Safely remove a directory."""
```

#### File Operations

```python
def safe_write_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Safely write content to a file."""

def safe_read_file(self, file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """Safely read content from a file."""

def safe_delete_file(self, file_path: Path) -> bool:
    """Safely delete a file."""

def safe_move_file(self, source: Path, destination: Path) -> bool:
    """Safely move a file from source to destination."""

def safe_copy_file(self, source: Path, destination: Path) -> bool:
    """Safely copy a file."""
```

### Error Handling

```python
def safe_write_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    try:
        # Ensure parent directory exists
        self.ensure_directory_exists(file_path.parent)

        # Write file atomically
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        with open(temp_path, 'w', encoding=encoding) as f:
            f.write(content)

        # Atomic move
        temp_path.rename(file_path)

        self.logger.debug("File written successfully", path=str(file_path))
        return True

    except IOError as e:
        self.logger.error("IO error writing file", path=str(file_path), error=str(e))
        return False
    except Exception as e:
        self.logger.error("Unexpected error writing file", path=str(file_path), error=str(e))
        return False
```

### Usage Example

```python
file_ops = get_container().get(FileOperations)

# Write file safely
content = "# My Board\n\nBoard content here..."
success = file_ops.safe_write_file(Path("/path/to/board.md"), content)
if success:
    print("File written successfully")

# Read file safely
content = file_ops.safe_read_file(Path("/path/to/board.md"))
if content:
    print(f"File content: {content}")

# Ensure directory exists
file_ops.ensure_directory_exists(Path("/path/to/boards"))
```

## Integration Examples

### Service with Full Utility Stack

```python
class ExampleService:
    def __init__(
        self,
        path_resolver: PathResolver,
        file_operations: FileOperations,
        logger: ContextAwareLogger
    ):
        self.path_resolver = path_resolver
        self.file_ops = file_operations
        self.logger = logger

    def process_board(self, board_name: str) -> bool:
        # Set context for all operations
        self.logger.set_context(board=board_name)

        # Get board path
        board_path = self.path_resolver.get_board_path(board_name)
        self.logger.debug("Processing board", path=str(board_path))

        # Read board file
        board_file = self.path_resolver.get_board_file_path(board_name)
        content = self.file_ops.safe_read_file(board_file)

        if content:
            self.logger.info("Board processed successfully")
            return True
        else:
            self.logger.error("Failed to read board file")
            return False
```

### Tmux-Aware Path Resolution

```python
def setup_project_board():
    path_resolver = get_container().get(PathResolver)

    # Automatically uses current tmux session
    boards_dir = path_resolver.get_boards_directory()
    print(f"Boards directory: {boards_dir}")
    # → /home/user/.mkanban/boards/my-session

    # Or with MKANBAN_PATH set
    # export MKANBAN_PATH="/home/user/projects/current"
    # → /home/user/projects/current
```

## Best Practices

### PathResolver Usage

1. **Always use PathResolver**: Don't construct paths manually
2. **Session awareness**: Let PathResolver handle tmux session detection
3. **Base path overrides**: Use base_path parameter for testing
4. **Path validation**: Use provided validation methods

### Logger Usage

1. **Set context early**: Establish context at service boundaries
2. **Use structured logging**: Include relevant context in all messages
3. **Component-specific loggers**: Use daemon vs TUI loggers appropriately
4. **JIRA operations**: Include jira_ticket in context for JIRA operations

### FileOperations Usage

1. **Always use safe methods**: Don't use raw file operations
2. **Check return values**: All methods return success/failure status
3. **Monitor logs**: File operation errors are logged automatically
4. **Atomic operations**: Safe methods ensure atomic file operations

```python
# Good practices
path_resolver = get_container().get(PathResolver)
logger = get_container().get_daemon_logger("my_service")
file_ops = get_container().get(FileOperations)

logger.set_context(component="board_processor")
board_path = path_resolver.get_board_path("my-project")
success = file_ops.safe_write_file(board_path / "data.json", json_content)

# Avoid
# board_path = Path(f"/home/user/.mkanban/boards/{board_name}")  # Don't construct manually
# with open(board_path / "data.json", 'w') as f:  # Don't use raw file operations
#     f.write(json_content)
```

The utilities layer provides a robust foundation for all cross-cutting concerns in MKanban, ensuring consistent path handling, comprehensive logging, and safe file operations throughout the application.