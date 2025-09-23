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
make lint              # Run ruff linting
make format            # Format code with black
ruff check             # Run ruff linter directly (configured in ruff.toml)
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
python main.py new-task "Task" --board "board-name"  # Create task via CLI
python main.py new-task "Task" --board "board-name" --description "Task description" --column "in-progress"  # Create task with description and specific column
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

---

# COMPLETE FEATURES & CONFIGURATION REFERENCE

## Core Application Features

### TUI Kanban Board Interface
- **Board Management**: Create, load, and manage multiple Kanban boards
- **Column-based Task Organization**: Organize tasks in customizable columns (to-do, in-progress, done, etc.)
- **Markdown-based Storage**: All data stored as markdown files with YAML frontmatter
- **Parent/Child Task Grouping**: Hierarchical task organization with parent grouping toggle
- **Real-time Visual Updates**: Live board updates with responsive layout
- **Auto-save Functionality**: Configurable auto-save with custom intervals

### Vim-style Navigation & Controls (Complete Keybinding Reference)
- **Movement**: `h/j/k/l` for directional navigation
- **Task Management**: `o` (new item), `i` (edit), `d` (delete)
- **Board Navigation**: `H/L` (move items between columns)
- **View Controls**: `p` (toggle parent grouping), `r` (refresh)
- **Utility**: `g?` (help), `w` (save), `q` (quit), `ctrl+c` (quit)
- **Advanced Navigation**: `gg` (first item), `G` (last item), `ctrl+d/u` (scroll)
- **Column Controls**: `c` (column settings), `shift+j` (column scroll down)
- **Item Creation**: `a` (new item with editor)

### Task Creation & Management
- **Multiple Creation Methods**:
  - TUI dialog creation (`o`)
  - CLI command creation (`new-task`)
  - External editor integration (`a` - neovide, nvim)
- **Rich Task Properties**: Title, description, metadata, parent relationships
- **Task Movement**: Drag-and-drop style movement between columns (`H/L`)
- **Task Editing**: In-place editing (`i`) and external editor support

## CLI Commands & Options Reference

### Main Application Launch
```bash
python main.py [OPTIONS] [COMMAND]
```

**Global Options:**
- `--boards-path PATH`: Custom path to board files directory
- `--board BOARD_NAME`: Open specific board directly (supports tab completion)
- `--new-to-do`: Create new item with external editor (requires --board)
- `--show-current-task`: Show/edit first task in specified column (requires --board)
- `--column COLUMN_NAME`: Target column (default: "to-do", supports tab completion)
- `--list-todos SELECTOR_CMD`: List todos with pipe to selector command
- `--completion [bash|zsh|fish]`: Generate shell completion scripts

### Task Creation Command
```bash
mkanban new-task "Task Title" --board BOARD_NAME [OPTIONS]
```
- `--description TEXT`: Task description
- `--column COLUMN`: Target column (default: "to-do")
- `--board BOARD`: Target board (required, tab completion available)

### Daemon Management Commands
```bash
mkanban daemon [start|stop|status|restart] [OPTIONS]
```

**Daemon Start/Restart Options:**
- `--board-name NAME`: Git branch board name (default: "git-branches")
- `--polling-interval SECONDS`: Git polling frequency (default: 5)
- `--no-tmux-session-only`: Monitor all repos, not just tmux session
- `--disable-session-task-management`: Disable automatic session task management
- `--data-path PATH`: Custom data directory path

**JIRA Integration Options:**
- `--enable-jira`: Enable JIRA integration
- `--jira-url URL`: JIRA instance URL (e.g., https://company.atlassian.net)
- `--jira-username USERNAME`: JIRA username (or set JIRA_USERNAME env var)
- `--jira-api-token TOKEN`: JIRA API token (or set JIRA_API_TOKEN env var)
- `--jira-projects KEYS`: Comma-separated project keys (e.g., 'PROJ,FEAT')
- `--jira-board-name NAME`: JIRA board name (default: "jira-tickets")
- `--jira-polling-interval SECONDS`: JIRA polling frequency (default: 300)
- `--jira-bidirectional-sync`: Enable bidirectional JIRA sync
- `--jira-jql-filter JQL`: Additional JQL filter (e.g., 'assignee = currentUser()')
- `--jira-backlog-limit NUMBER`: Backlog ticket limit (default: 50, -1 for unlimited)

## Complete Configuration Parameters

### Main Configuration (`~/.config/mkanban/config.json`)

**Storage & Paths:**
- `boards_path`: Board files location (default: `~/.mkanban/boards`)
- `config_dir`: Configuration directory (default: `~/.config/mkanban`)

**UI & Behavior:**
- `auto_save`: Enable auto-save (default: true)
- `auto_save_interval`: Auto-save frequency in seconds (default: 30)
- `backup_count`: Number of backups to retain (default: 5)
- `theme`: UI theme ("dark" or "light", default: "dark")
- `show_parent_colors`: Enable parent-based color coding (default: true)
- `default_parent_view`: Start with parent grouping enabled (default: false)
- `column_width`: Default column width (default: 30)

**Editor Integration:**
- `editor`: Default text editor (default: "nvim")
- `cli_editor`: CLI editor for new items (default: "neovide")

**Keyboard Shortcuts:**
- `shortcuts`: Customizable vim-style keybindings dictionary with keys:
  - `focus_next`: "j", `focus_previous`: "k"
  - `focus_left`: "h", `focus_right`: "l"
  - `focus_first`: "gg", `focus_last`: "G"
  - `new_item`: "o", `edit_item`: "i", `delete_item`: "d"
  - `move_left`: "ctrl+h", `move_right`: "ctrl+l"
  - `toggle_parents`: "p", `save`: "w", `refresh`: "r"
  - `help`: "g?", `quit`: "q"

### Daemon Configuration
- `enabled`: Enable daemon service (default: true)
- `polling_interval`: Git monitoring frequency (default: 5 seconds)
- `tmux_session_only`: Monitor only active tmux session (default: true)
- `enable_session_task_management`: Auto task management on session switch (default: true)
- `auto_complete_on_session_switch`: Auto-complete tasks when switching (default: true)
- `auto_activate_on_session_switch`: Auto-activate tasks on switch (default: true)
- `session_name`: Session identifier (default: "git-branches")
- `default_board`: Default board name (default: "git-branches")
- `default_column`: Default column name (default: "to-do")
- `in_progress_column`: In-progress column name (default: "in-progress")
- `done_column`: Completion column name (default: "done")

**Git Branch Patterns:**
- `branch_patterns`: Monitored branch patterns (default: ["feature/*", "bugfix/*", "hotfix/*", "fix/*", "feat/*", "test", "test/*", "*"])
- `excluded_branches`: Ignored branches (default: ["main", "master", "develop", "staging", "production"])

### JIRA Configuration
- `enabled`: Enable JIRA integration (default: false)
- `api_url`: JIRA instance URL
- `username`: JIRA username
- `api_token`: JIRA API token
- `project_keys`: List of monitored project keys
- `polling_interval`: JIRA polling frequency (default: 300 seconds)
- `bidirectional_sync`: Enable two-way sync (default: false)
- `backlog_limit`: Maximum backlog tickets (default: 50)
- `jql_filter`: Additional JQL query filter
- `board_name`: JIRA tickets board name (default: "jira-tickets")

**JIRA Status Mapping:**
- `status_mapping`: Maps JIRA statuses to board columns:
  - "Backlog" → "backlog"
  - "To Do" → "to-do"
  - "In Progress" → "in-progress"
  - "Done" → "done"

**JIRA Branch Patterns:**
- `branch_patterns`: Regex patterns for JIRA ticket detection:
  - `.*[A-Z]+-\d+.*`
  - `[A-Z]+-\d+/.*`
  - `.*/[A-Z]+-\d+.*`

### Logging Configuration
- `level`: Log level ("DEBUG", "INFO", "WARNING", "ERROR", default: "INFO")
- `daemon_log_dir`: Daemon log directory (default: `~/.config/mkanban/logs/daemon`)
- `tui_log_dir`: TUI log directory (default: `~/.config/mkanban/logs/tui`)
- `create_timestamped_daemon_logs`: Create timestamped daemon logs (default: true)
- `max_log_files`: Maximum log files to retain (default: 30)
- `log_format`: General log format string
- `daemon_log_format`: Daemon-specific log format
- `tui_log_format`: TUI-specific log format

## Git Integration Features

### Automatic Branch Monitoring
- **Real-time Git Repository Monitoring**: Watches for branch changes, commits, checkouts
- **Branch-based Task Creation**: Automatically creates tasks from branch names
- **Session-aware Monitoring**: Focuses on current tmux session's repository
- **Multi-repository Support**: Can monitor multiple repositories simultaneously

### Git Branch Lifecycle Management
- **Branch Creation Detection**: Creates tasks when new branches are made
- **Branch Switch Tracking**: Moves tasks between columns based on branch status
- **Completion Detection**: Marks tasks done when branches are merged/deleted
- **Commit Tracking**: Updates tasks with latest commit information

### Tmux Session Integration
- **Session-based Board Isolation**: Each tmux session gets its own board
- **Automatic Board Switching**: Boards change automatically with session switches
- **Session Path Resolution**: Resolves project paths based on tmux session context
- **Global vs Session Data**: Supports both session-specific and global data storage

## JIRA Integration Features

### Bidirectional Synchronization
- **JIRA to MKanban Sync**: Automatically imports JIRA tickets as kanban tasks
- **MKanban to JIRA Sync**: Updates JIRA ticket status when tasks are moved
- **Real-time Polling**: Configurable polling intervals for JIRA updates
- **Conflict Resolution**: Handles conflicts between local and JIRA changes

### Advanced JIRA Features
- **Multi-project Support**: Monitors multiple JIRA projects simultaneously
- **Custom JQL Filtering**: Additional filtering with custom JQL queries
- **Status Mapping**: Configurable mapping between JIRA statuses and board columns
- **Branch-ticket Linking**: Automatically links git branches to JIRA tickets
- **Backlog Management**: Configurable limits for backlog ticket fetching

### JIRA Authentication & Security
- **API Token Authentication**: Secure authentication using JIRA API tokens
- **Environment Variable Support**: Credentials can be set via environment variables
- **Connection Validation**: Validates JIRA connection on daemon startup

## Daemon Mode Capabilities

### Background Service Management
- **PID File Management**: Proper daemon lifecycle management
- **Signal Handling**: Graceful shutdown on system signals
- **IPC Communication**: Inter-process communication for status/control
- **Logging Separation**: Separate logs for daemon vs TUI operations

### Automatic Task Management
- **Branch Lifecycle Tracking**: Automatically manages task states based on git branches
- **Session Context Switching**: Manages tasks across different development sessions
- **Intelligent Task State Transitions**: Smart movement between to-do, in-progress, and done states
- **Conflict Prevention**: Prevents duplicate tasks and handles state conflicts

### Service Coordination
- **Multi-service Architecture**: Coordinates Git monitoring, JIRA sync, and session management
- **Configurable Polling**: Independent polling intervals for different services
- **Error Recovery**: Resilient error handling and automatic service recovery
- **Resource Management**: Efficient resource usage with intelligent scheduling

## UI & UX Features

### Responsive Design
- **Adaptive Column Widths**: Automatically adjusts to terminal size
- **Compact Mode**: Optimized layout for smaller terminals (min width: 18)
- **Dynamic Resizing**: Real-time layout updates on terminal resize
- **Column Width Constants**: Default: 27, Min: 20, Max: 50

### Visual Enhancements
- **Parent Color Coding**: Visual grouping with color-coded parent relationships
- **Status Indicators**: Visual indicators for task states and metadata
- **Help System**: Built-in help dialog with keybinding reference (`g?`)
- **Theme Support**: Dark and light theme options

### User Experience
- **Vim-inspired Workflow**: Familiar navigation for vim users
- **Minimal Cognitive Load**: Clean, distraction-free interface
- **Keyboard-first Design**: Complete functionality available via keyboard
- **Context-aware Actions**: Smart defaults based on current selection and state

---

# MAINTENANCE GUIDELINES

## When Adding New Features

**IMPORTANT**: When implementing new features, update this CLAUDE.md file to include:

1. **New CLI Options**: Add to CLI Commands & Options Reference section
2. **New Configuration Parameters**: Add to Complete Configuration Parameters section
3. **New Keybindings**: Update Vim-style Navigation & Controls section
4. **New Integration Features**: Update Git/JIRA Integration Features sections
5. **New UI Elements**: Update UI & UX Features section
6. **Architecture Changes**: Update Architecture section if patterns change

## Documentation Update Process

1. Implement the feature
2. Update CLAUDE.md with feature documentation
3. Ensure examples and defaults are accurate
4. Test that all documented functionality works as described
5. Commit changes together with feature implementation

This keeps the documentation accurate and ensures Claude Code always has current information about the application's capabilities.
