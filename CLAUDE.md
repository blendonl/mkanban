# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MKanban is a Terminal User Interface (TUI) Kanban board application built with Python and Textual. It manages tasks using markdown files stored in a hierarchical folder structure, providing a vim-inspired interface for efficient task management with Git branch tracking and JIRA integration.

## Development Commands

### Environment Setup
```bash
make setup              # Create venv and install dependencies
```

### Code Quality
```bash
make lint              # Run flake8 and mypy linting
make format            # Format code with black
ruff check             # Run ruff linter (configured in ruff.toml)
```

### Testing
```bash
make test              # Run pytest tests
python test/test_operations.py  # Run specific debugging tests
pytest tests/unit/test_services/test_board_service.py::TestBoardService::test_create_board  # Run single test
```

### Building
```bash
make executable        # Build standalone executable with PyInstaller
make dist             # Create distribution packages (sdist/bdist_wheel)
```

### Running the Application
```bash
python main.py                        # Run with default data directory
python main.py --data-dir /path/to/data  # Use custom data directory
python main.py --board "board-name"     # Open specific board
python main.py --new-task-title "Task" --board "board-name"  # Create task via CLI
```

## Architecture

### Clean Architecture with Dependency Injection

The codebase follows clean architecture principles with clear separation of concerns:

- **Domain Layer** (`src/domain/`): Entities (Board, Column, Item, Parent) and repository interfaces
- **Service Layer** (`src/services/`): Business logic (BoardService, ItemService, ValidationService)
- **Infrastructure Layer** (`src/infrastructure/`): Storage implementations, JIRA integration, tmux management
- **Application Layer** (`src/app.py`): Main TUI application
- **Core** (`src/core/`): Dependency injection container, types, constants

### Dependency Injection Pattern

All services are managed by a central DI container (`src/core/dependency_container.py`):

```python
# Get services via container
container = get_container()
board_service = container.get(BoardService)

# Or use convenience functions
from src.core.dependency_container import get_board_service
board_service = get_board_service()
```

Services declare dependencies in constructors and are automatically resolved:

```python
class BoardService:
    def __init__(
        self,
        board_repository: BoardRepository,
        validation_service: ValidationService,
        logger: ContextAwareLogger
    ):
        # Dependencies injected automatically
```

### Configuration System

Unified configuration with environment overrides (`src/config/configuration_manager.py`):

- **JSON config**: `~/.mkanban/config.json`
- **Environment variables**: `MKANBAN_*` prefixed variables
- **Session awareness**: tmux session-based data directories

### Context-Aware Logging

Structured logging with board/column/item context (`src/utils/logger_factory.py`):

```python
logger.info("Loading board", board="my-project")
# Output: [2024-01-01T10:00:00] DAEMON INFO service: Loading board [board=my-project]
```

### Data Structure

Boards are stored as markdown files with frontmatter metadata:
```
data/boards/{board-name}/
├── kanban.md           # Board metadata and structure
├── {column-name}/      # Column folders
│   ├── column.md       # Column metadata (optional)
│   └── *.md           # Item files with YAML frontmatter
```

### Git & JIRA Integration

- **Git Integration**: Automatic task creation from branch patterns, current branch tracking
- **JIRA Integration**: Bidirectional sync with JIRA projects via REST API
- **Daemon Mode**: Background process for automatic synchronization

### Key Design Patterns

- **Repository Pattern**: Storage abstracted behind interfaces (`BoardRepository`, `StorageRepository`)
- **Service Layer**: Business logic encapsulated in services
- **Factory Pattern**: LoggerFactory for context-aware logging
- **Dependency Injection**: All dependencies managed by container

### Vim-style Navigation

The application uses vim-inspired keybindings:
- `h/j/k/l`: Navigate left/down/up/right
- `H/L`: Move items between columns
- `o`: Create new item
- `i`: Edit item
- `d`: Delete item
- `p`: Toggle parent grouping
- `g?`: Show help dialog

## Important Architecture Notes

### Adding New Services

1. Create service class with constructor dependencies
2. Register factory in `src/core/dependency_container.py`
3. Services automatically get dependencies injected

### Repository Pattern

- `MarkdownBoardRepository`: Board-level operations (load/save boards)
- `MarkdownStorageRepository`: Item-level operations (CRUD items)
- Both implement abstract interfaces for testability

### Session-Aware Paths

Path resolution is handled by `PathResolver` which supports:
- tmux session detection
- `MKANBAN_PATH` environment variable
- Fallback to configured data directory

### Error Handling

Services return `None`/`False` for failures and use comprehensive logging:
- All operations logged with relevant context
- JIRA operations prefixed with `[JIRA:TICKET-123]`
- Daemon vs TUI logging separation

## Testing

Tests are organized by layer:
- `tests/unit/`: Unit tests with mocked dependencies
- `tests/integration/`: Integration tests with real storage
- Use dependency injection for easy mocking in tests