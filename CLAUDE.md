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
python src/main.py                        # Run with default data directory
python src/main.py --data-dir /path/to/data  # Use custom data directory
python src/main.py --board "board-name"     # Open specific board
python src/main.py --new-task-title "Task" --board "board-name"  # Create task via CLI
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

### Task Listing Command

```bash
mkanban list [OPTIONS]
```

- `--board BOARD_NAME`: Board to list tasks from (default: current tmux session board, tab completion available)
- `--columns COLUMN_LIST`: Comma-separated list of columns to include (default: all columns)

**Usage Examples:**

```bash
# List all tasks from a specific board
python -m src.main list --board my-project

# List tasks from specific columns
python -m src.main list --board my-project --columns "to-do,in-progress"

# Pipe to external tools for selection
python -m src.main list --board my-project | fzf
python -m src.main list --columns "to-do" --board my-project | rofi -dmenu
```

### Branch Checkout Command

```bash
mkanban checkout TASK [OPTIONS]
```

Creates or checks out a git branch based on a task, automatically managing task states in the kanban board.

**Options:**

- `TASK`: Task title, ID, or partial match (required)
- `--board BOARD_NAME`: Board to use (default: current tmux session board, tab completion available)

**Behavior:**

- Converts task title to git-safe branch name (lowercase, hyphens, no special chars)
- Creates branch if it doesn't exist, checks out if it does
- Moves all tasks from "in-progress" column to "to-do" column
- Moves the selected task to "in-progress" column
- Works with current tmux session's repository or specified board

**Usage Examples:**

```bash
# Checkout branch for a task (uses active tmux session board)
mkanban checkout "fix login bug"

# Checkout with specific board
mkanban checkout "implement feature X" --board my-project

# Partial match on task title
mkanban checkout "login"

# Using task ID
mkanban checkout task-123

# Pipe task from another command
mkanban list --columns "to-do" | fzf | mkanban checkout
echo "fix login bug" | mkanban checkout
mkanban list | rofi -dmenu | mkanban checkout --board my-project
```

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
- `default_issue_type`: Default issue type for manually created items (default: "Task"). Options include "Task", "Story", "Bug", "Epic". This affects the icon displayed for the item (📋 Task, 📖 Story, 🐛 Bug, 📚 Epic). Does not apply to JIRA-managed or Git-managed items.

**Editor Integration:**

- `editor`: Default text editor (default: "nvim")

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

**Basic Settings:**

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

**Hierarchy and Filtering:**

- `include_subtasks`: Fetch subtasks with parent tickets (default: true)
- `include_epics`: Fetch epic children with epics (default: true)
- `fetch_strategy`: Fetching strategy (default: "assigned")
  - `"assigned"`: Fetch tickets assigned to current user or unassigned
  - `"all_in_projects"`: Fetch all tickets in configured projects
  - `"custom_jql"`: Use custom JQL filter
- `max_hierarchy_depth`: Maximum hierarchy depth to fetch (default: 2)
  - `1`: No children, parent tickets only
  - `2`: Parent tickets and their direct children
  - `3+`: Multi-level nested hierarchy

**Subtask Handling:**

- `subtask_column_strategy`: How to place subtasks in columns (default: "same_as_jira")
  - `"same_as_parent"`: Always place subtasks in same column as parent
  - `"same_as_jira"`: Respect JIRA status for subtasks independently
  - `"custom"`: Custom column placement logic
- `move_subtasks_with_parent`: Move subtasks when parent moves (default: false)
- `auto_complete_subtasks`: Auto-complete subtasks when parent marked done (default: false)

**Metadata Synchronization:**

- `sync_priority`: Sync priority changes back to JIRA (default: true)
- `sync_labels`: Sync label changes back to JIRA (default: true)
- `sync_components`: Sync component changes back to JIRA (default: true)

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

### JIRA Hierarchy Support (NEW)

- **Epic Management**: Automatically fetches and syncs epics with their child stories
- **Subtask Support**: Fetches subtasks with parent tickets, preserving hierarchy
- **Multi-level Hierarchy**: Configurable depth for nested ticket structures (epic → story → subtask)
- **Parent-Child Relationships**: Automatically links items based on JIRA parent/epic relationships
- **Issue Links**: Syncs JIRA issue links (blocks, relates to, etc.) as cross-references
- **Smart Fetching**: Intelligent hierarchical fetching with configurable depth control

### JIRA Metadata Display (NEW)

- **Visual Indicators**: Issue type icons (📚 Epic, 📖 Story, 🐛 Bug, ☑️ Subtask, 📋 Task)
- **Priority Badges**: Color-coded priority indicators (🔴 Highest, 🟠 High, 🟡 Medium, 🟢 Low, 🔵 Lowest)
- **Story Points**: Display story points on items
- **Sprint Information**: Show current sprint assignment
- **Subtask Count**: Display number of subtasks (☑️3)
- **Link Count**: Show number of issue links (🔗5)
- **Components & Labels**: Display first component/label with count of additional ones
- **Versions**: Track fix versions and affects versions

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

Also for each feature, create a new branch named `feature/<short-description>` and ensure all changes are committed with clear messages. The same for fixes

And for each feature, create or update tasks in the project management board to track progress. using this app's cli

## Documentation Update Process

1. Implement the feature
2. Update CLAUDE.md with feature documentation
3. Ensure examples and defaults are accurate
4. Test that all documented functionality works as described
5. Commit changes together with feature implementation

This keeps the documentation accurate and ensures Claude Code always has current information about the application's capabilities.


---

# ACTIONS/REMINDERS SYSTEM

## Overview

The Actions/Reminders system provides powerful automation and notification capabilities for mkanban. It supports time-based reminders, event-driven automations, inactivity watchers, and hooks that can trigger notifications and perform actions on tasks and boards.

## Core Concepts

### Action Types

- **reminder**: Time-based notifications (e.g., "Remind me at 5pm")
- **automation**: Event-driven actions (e.g., "Move stale tasks to to-do")
- **watcher**: Continuous monitoring with conditions
- **hook**: Pre/post event triggers
- **scheduled_job**: Recurring scheduled tasks

### Scope Levels

- **global**: Applies everywhere (e.g., daily standup reminder)
- **board**: Specific to one board (e.g., welcome message when opening project board)
- **task**: Specific to one task (e.g., deadline reminder for PROJ-123)

### Trigger Types

- **time**: Time-based (once, daily, weekly, monthly, cron)
- **board_switch**: When entering/exiting a board
- **task_state_change**: When task is created/updated/deleted/moved
- **git_event**: Git operations (branch created/deleted/merged)
- **jira_event**: JIRA ticket changes
- **inactivity**: After period of no activity

### Action Executors

- **notify**: Send multi-channel notifications
- **move_task**: Move tasks between columns
- **create_task**: Create new tasks
- **mark_complete**: Mark tasks as done
- **create_branch**: Create git branches
- **jira_update**: Update JIRA tickets
- **run_command**: Execute shell commands

## CLI Commands

### List Actions
```bash
# List all actions
mkanban action list

# Filter by scope
mkanban action list --scope global
mkanban action list --scope board --target-id my-project

# Filter by type
mkanban action list --type reminder
mkanban action list --type automation

# Show only enabled
mkanban action list --enabled-only
```

### Show Action Details
```bash
mkanban action show <action-id>
```

### Create Action
```bash
# Create a simple daily reminder
mkanban action create \
  --name "Daily Standup" \
  --time "09:00" \
  --message "Time for standup!" \
  --platforms desktop,mobile

# Create with specific scope
mkanban action create \
  --name "Board Welcome" \
  --scope board \
  --target-id my-project \
  --message "Welcome to my project!"
```

### Enable/Disable Actions
```bash
mkanban action enable <action-id>
mkanban action disable <action-id>
```

### Snooze Actions
```bash
# Snooze for 1 hour
mkanban action snooze <action-id> --duration 1h

# Snooze until tomorrow
mkanban action snooze <action-id> --duration tomorrow

# Clear snooze
mkanban action unsnooze <action-id>
```

### Delete Actions
```bash
# Delete with confirmation
mkanban action delete <action-id>

# Delete without confirmation
mkanban action delete <action-id> --yes
```

### View Execution History
```bash
mkanban action history <action-id>
```

### Clean Orphaned Actions
```bash
# Disable orphaned actions (default)
mkanban action clean-orphaned

# Delete orphaned actions
mkanban action clean-orphaned --delete
```

## Configuration

### Enable Actions System

Edit `~/.mkanban/config.json`:

```json
{
  "actions": {
    "enabled": true,
    "polling_interval": 30,
    "default_snooze_options": ["10m", "30m", "1h", "3h", "tomorrow", "next_week"],
    "max_concurrent_executions": 5,
    "execution_timeout": 300,
    "orphan_check_interval": 3600,
    "orphan_action": "auto_disable",
    "notifications": {
      "system": {
        "enabled": true,
        "command": "notify-send",
        "icon_path": null
      },
      "mobile_push": {
        "enabled": false,
        "provider": "ntfy",
        "ntfy_server": "https://ntfy.sh",
        "ntfy_topic": "mkanban-your-unique-id",
        "ntfy_token": null
      }
    }
  }
}
```

### Configuration Parameters

**Core Settings:**
- `enabled` (bool): Enable/disable actions system
- `polling_interval` (int): Seconds between time-based trigger checks (default: 30)
- `default_snooze_options` (list): Available snooze durations
- `max_concurrent_executions` (int): Maximum parallel action executions
- `execution_timeout` (int): Timeout in seconds for action execution
- `orphan_check_interval` (int): Seconds between orphan checks
- `orphan_action` (str): What to do with orphaned actions (auto_disable | auto_delete | warn_only)

**Notification Settings:**
- `system.enabled` (bool): Enable desktop notifications
- `system.command` (str): Command for system notifications (default: "notify-send")
- `system.icon_path` (str): Path to notification icon
- `mobile_push.enabled` (bool): Enable mobile push notifications
- `mobile_push.provider` (str): Push provider (default: "ntfy")
- `mobile_push.ntfy_server` (str): ntfy.sh server URL
- `mobile_push.ntfy_topic` (str): Your unique ntfy topic
- `mobile_push.ntfy_token` (str): Authentication token (optional)

## File Format

Actions are stored as YAML files in `~/.mkanban/actions/` organized by scope and type:

```
~/.mkanban/actions/
├── global/
│   ├── reminders/
│   ├── automations/
│   ├── watchers/
│   └── hooks/
├── boards/
│   └── {board-id}/
│       ├── reminders/
│       └── automations/
└── tasks/
    └── {task-id}/
        └── reminders/
```

### Example Action File

```yaml
id: action-rem-daily-standup-20241020
type: reminder
name: "Daily standup reminder"
description: "Reminds me about the daily standup every weekday morning"
enabled: true
created_at: "2024-10-20T10:00:00"
modified_at: "2024-10-20T10:00:00"

scope:
  type: global
  target_id: null

triggers:
  - type: time
    schedule:
      type: daily
      time: "09:00"
      days_of_week: [1, 2, 3, 4, 5]  # Monday-Friday
      timezone: "America/New_York"

conditions:
  - type: time_range
    start_time: "08:00"
    end_time: "18:00"

actions:
  - type: notify
    message: "Time for daily standup!"
    title: "MKanban - Daily Standup"
    platforms: ["desktop", "mobile"]
    channels: ["system", "mobile_push"]
    priority: normal

recurrence: null
snooze:
  enabled: true
  count: 0
  until: null
  options: ["10m", "30m", "1h"]

execution:
  last_triggered: null
  last_success: null
  last_failure: null
  last_error: null
  total_executions: 0
  successful_executions: 0
  consecutive_failures: 0

metadata:
  priority: 1
  max_retries: 3
  retry_delay: 300
  timeout: 30
  tags: ["daily", "meeting", "reminder"]
  custom: {}

on_success: []
on_failure: []
```

## Trigger Reference

### Time Trigger

```yaml
triggers:
  - type: time
    schedule:
      type: once  # once | daily | weekly | monthly | cron
      datetime: "2024-10-20T17:00:00"  # for 'once'
      time: "09:00"  # for daily/weekly/monthly
      days_of_week: [1, 2, 3, 4, 5]  # 1=Monday, 7=Sunday
      day_of_month: 15  # for monthly
      cron_expression: "0 9 * * 1-5"  # for cron
      timezone: "America/New_York"
```

### Board Switch Trigger

```yaml
triggers:
  - type: board_switch
    event: enter  # enter | exit
    board_id: "my-board"
```

### Task State Change Trigger

```yaml
triggers:
  - type: task_state_change
    events: ["moved", "created", "deleted", "updated"]
```

### Git Event Trigger

```yaml
triggers:
  - type: git_event
    events: ["branch_created", "branch_deleted", "branch_merged", "commit_made"]
```

### Inactivity Trigger

```yaml
triggers:
  - type: inactivity
    check_interval: 3600  # check every hour
    inactive_duration: 172800  # 48 hours
```

## Condition Reference

### Time Range Condition

```yaml
conditions:
  - type: time_range
    start_time: "09:00"
    end_time: "17:00"
```

### Day of Week Condition

```yaml
conditions:
  - type: day_of_week
    days: [1, 2, 3, 4, 5]  # Monday=1, Sunday=7
```

### Task in Column Condition

```yaml
conditions:
  - type: task_in_column
    column_ids: ["to-do", "in-progress"]
```

### Task Property Condition

```yaml
conditions:
  - type: task_property
    field: "is_git_managed"
    operator: equals  # equals | not_equals | greater_than | less_than | contains | in | matches_regex
    value: false
```

## Action Executor Reference

### Notify Action

```yaml
actions:
  - type: notify
    message: "Your message here (supports {task_title}, {board_name})"
    title: "Notification Title"
    platforms: ["desktop", "mobile"]  # desktop | mobile | both
    channels: ["system", "mobile_push", "email"]
    priority: normal  # low | normal | high | urgent
```

### Move Task Action

```yaml
actions:
  - type: move_task
    target_column: "done"
```

### Create Task Action

```yaml
actions:
  - type: create_task
    task_title: "New task title"
    task_description: "Description"
    task_column: "to-do"
    board_id: "my-board"
```

### Run Command Action

```yaml
actions:
  - type: run_command
    command: "echo 'Task completed' >> ~/log.txt"
    working_dir: "/path/to/dir"
    environment:
      TASK_ID: "{task_id}"
```

## Variables

The following variables can be used in messages and commands:

- `{task_title}` - Title of the task
- `{task_id}` - ID of the task
- `{task_description}` - Description of the task
- `{board_name}` - Name of the board
- `{board_id}` - ID of the board

Example: `"Don't forget to work on {task_title} today!"`

## Mobile Push Notifications

### Setup ntfy.sh

1. Install ntfy app on your phone: https://ntfy.sh/
2. Choose a unique topic name (e.g., `mkanban-john-12345`)
3. Subscribe to that topic in the ntfy app
4. Update config:

```json
{
  "actions": {
    "notifications": {
      "mobile_push": {
        "enabled": true,
        "ntfy_topic": "mkanban-john-12345"
      }
    }
  }
}
```

5. Test:
```bash
curl -d "Test message" https://ntfy.sh/mkanban-john-12345
```

## Common Use Cases

### Daily Standup Reminder

```yaml
# ~/.mkanban/actions/global/reminders/standup.yaml
id: action-rem-standup
type: reminder
name: "Daily standup reminder"
enabled: true

scope:
  type: global
  target_id: null

triggers:
  - type: time
    schedule:
      type: daily
      time: "09:00"
      days_of_week: [1, 2, 3, 4, 5]

actions:
  - type: notify
    message: "Time for daily standup!"
    platforms: ["desktop", "mobile"]
```

### Stale Task Automation

```yaml
# ~/.mkanban/actions/global/automations/stale-tasks.yaml
id: action-aut-stale
type: automation
name: "Move stale tasks"
enabled: true

scope:
  type: global
  target_id: null

triggers:
  - type: inactivity
    check_interval: 3600
    inactive_duration: 172800  # 48 hours

conditions:
  - type: task_in_column
    column_ids: ["in-progress"]
  - type: task_property
    field: is_git_managed
    operator: equals
    value: false

actions:
  - type: move_task
    target_column: "to-do"
  - type: notify
    message: "Task '{task_title}' moved to to-do due to inactivity"
```

### Board Welcome Hook

```yaml
# ~/.mkanban/actions/boards/my-project/hooks/welcome.yaml
id: action-hoo-welcome
type: hook
name: "Welcome message"
enabled: true

scope:
  type: board
  target_id: "my-project"

triggers:
  - type: board_switch
    event: enter
    board_id: "my-project"

actions:
  - type: notify
    message: "Welcome to My Project board!"
    platforms: ["desktop"]
```

### Task Deadline Reminder

```yaml
# ~/.mkanban/actions/tasks/PROJ-123/reminders/deadline.yaml
id: action-rem-deadline
type: reminder
name: "Task deadline reminder"
enabled: true

scope:
  type: task
  target_id: "PROJ-123"

triggers:
  - type: time
    schedule:
      type: once
      datetime: "2024-10-25T17:00:00"

actions:
  - type: notify
    message: "Deadline for {task_title} is in 2 days!"
    platforms: ["desktop", "mobile"]
    priority: high
```

## Architecture

### Event Flow

```
User Action (TUI/CLI)
        ↓
Service Layer (BoardService/ItemService)
        ↓
Event Bus (publish event)
        ↓
ActionDaemon (subscribed to events)
        ↓
ActionEngine (evaluate triggers & conditions)
        ↓
Execute Actions (notifications, task operations, etc.)
```

### Components

**Domain Layer:**
- `Action` - Main action entity
- `ActionScope` - Scope definition (global/board/task)
- `Trigger` - Trigger configuration
- `Condition` - Condition rules
- `ActionExecutor` - Action execution configuration

**Repository Layer:**
- `ActionRepository` - Abstract repository interface
- `YamlActionRepository` - YAML file-based implementation

**Service Layer:**
- `ActionService` - CRUD operations, validation, orphan cleanup
- `ActionEngine` - Trigger evaluation, condition checking, execution
- `NotificationService` - Multi-channel notification dispatcher

**Infrastructure Layer:**
- `SystemNotifier` - Desktop notifications (notify-send)
- `MobilePushProvider` - Mobile push via ntfy.sh

**Daemon:**
- `ActionDaemon` - Background service for polling and event handling

**Event Bus:**
- `EventBus` - Simple pub/sub system for inter-service communication

## Dependencies

Required packages:

```
croniter>=1.3.0  # For cron expression parsing
pyyaml>=6.0      # For YAML file handling
requests>=2.31.0 # For ntfy.sh HTTP requests
```

Install:
```bash
pip install croniter pyyaml requests
```

## Troubleshooting

### Actions Not Triggering

1. Check daemon is running: `mkanban daemon status`
2. Check actions are enabled: `mkanban action list --enabled-only`
3. Check logs: `tail -f ~/.mkanban/logs/daemon/daemon.log`
4. Verify trigger time is correct and in future
5. Ensure `actions.enabled: true` in config

### Notifications Not Appearing

1. Check notify-send is installed: `which notify-send`
2. Test manually: `notify-send "Test" "Message"`
3. Verify `actions.notifications.system.enabled: true`
4. Check system notification settings
5. Look for errors in daemon logs

### Mobile Push Not Working

1. Test ntfy.sh: `curl -d "Test" https://ntfy.sh/your-topic`
2. Verify topic name matches in app and config
3. Check ntfy app is subscribed to topic
4. Ensure `mobile_push.enabled: true`
5. Topic names are case-sensitive

### Events Not Firing

1. Ensure daemon started AFTER config changes
2. Check event bus subscriptions in logs
3. Verify services are emitting events
4. Look for event handler errors in logs
5. Test event emission manually

## Examples

See `examples/actions/` directory for:
- `daily-standup-reminder.yaml` - Time-based reminder
- `stale-task-watcher.yaml` - Inactivity automation
- `board-enter-notification.yaml` - Event-based hook
- `README.md` - Comprehensive usage guide

## Performance

- Polling interval: 30 seconds (configurable)
- Event handling: Async, non-blocking
- Action execution: Queued with timeout
- Memory usage: ~10MB for action daemon
- CPU usage: Negligible when idle

## Security

- YAML files stored in user directory only
- No remote code execution
- Commands run as user
- ntfy.sh uses HTTPS
- No credentials stored in action files
- Validation of all inputs

## Maintenance

When adding new features:
1. Update this CLAUDE.md documentation
2. Add examples to `examples/actions/`
3. Update configuration schema
4. Test all documented functionality
5. Commit changes together

