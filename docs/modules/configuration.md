# Configuration System

The MKanban configuration system provides a unified approach to managing application settings with environment variable overrides, JSON persistence, and type safety.

## Overview

The configuration system consists of:

- **ConfigurationManager**: Main configuration interface
- **UnifiedConfiguration**: Type-safe configuration dataclass
- **Environment overrides**: `MKANBAN_*` environment variables
- **JSON persistence**: Settings stored in `~/.mkanban/config.json`

## ConfigurationManager

The `ConfigurationManager` is a singleton that manages all configuration aspects.

### Usage

```python
from src.config.configuration_manager import get_config

config_manager = get_config()
config = config_manager.config

# Access configuration
data_dir = config_manager.get_data_dir()
editor = config_manager.get_editor()
debug_mode = config_manager.is_debug_mode()
```

### Methods

#### Core Methods

- **`config`**: Property returning the current `UnifiedConfiguration`
- **`get_data_dir()`**: Returns resolved data directory path
- **`get_config_dir()`**: Returns resolved configuration directory path
- **`get_editor()`**: Returns preferred editor (EDITOR env var or configured)
- **`is_debug_mode()`**: Returns True if debug logging enabled
- **`get_mkanban_path()`**: Returns MKANBAN_PATH environment variable

#### Persistence Methods

- **`save_configuration()`**: Saves current configuration to JSON
- **`update_configuration(**updates)`**: Updates and saves configuration
- **`reload_configuration()`**: Reloads configuration from file/environment

### Example

```python
# Update configuration
config_manager.update_configuration(
    theme="light",
    auto_save_interval=60
)

# Access nested configuration
if config_manager.config.daemon.enabled:
    interval = config_manager.config.daemon.polling_interval
```

## Configuration Structure

### UnifiedConfiguration

```python
@dataclass
class UnifiedConfiguration:
    data_dir: str = DEFAULT_DATA_DIR
    config_dir: str = ""
    auto_save: bool = True
    auto_save_interval: int = DEFAULT_AUTO_SAVE_INTERVAL
    backup_count: int = DEFAULT_BACKUP_COUNT
    theme: str = ThemeType.DARK.value
    show_parent_colors: bool = True
    default_parent_view: bool = False
    column_width: int = DEFAULT_COLUMN_WIDTH
    shortcuts: Dict[str, str] = field(default_factory=lambda: VIM_KEYBINDINGS.copy())
    daemon: DaemonConfiguration = field(default_factory=DaemonConfiguration)
    logging: LoggingConfiguration = field(default_factory=LoggingConfiguration)
```

### DaemonConfiguration

```python
@dataclass
class DaemonConfiguration:
    enabled: bool = True
    polling_interval: int = 5
    tmux_session_only: bool = True
    enable_session_task_management: bool = True
    auto_complete_on_session_switch: bool = True
    auto_activate_on_session_switch: bool = True
    session_name: str = "git-branches"
    default_board: str = "git-branches"
    default_column: str = "to-do"
    in_progress_column: str = "in-progress"
    done_column: str = "done"
    branch_patterns: List[str] = field(default_factory=lambda: [
        "feature/*", "bugfix/*", "hotfix/*", "fix/*", "feat/*",
        "test", "test/*", "*"
    ])
    excluded_branches: List[str] = field(default_factory=lambda: [
        "main", "master", "develop", "staging", "production"
    ])
    jira: JiraConfiguration = field(default_factory=JiraConfiguration)
```

### JiraConfiguration

```python
@dataclass
class JiraConfiguration:
    enabled: bool = False
    api_url: str = ""
    username: str = ""
    api_token: str = ""
    project_keys: List[str] = field(default_factory=list)
    polling_interval: int = 300
    bidirectional_sync: bool = False
    backlog_limit: int = 50
    status_mapping: Dict[str, str] = field(default_factory=lambda: {
        "To Do": "to-do",
        "In Progress": "in-progress",
        "Done": "done",
        "Backlog": "backlog"
    })
    jql_filter: str = ""
    board_name: str = "jira-tickets"
    branch_patterns: List[str] = field(default_factory=lambda: [
        r".*[A-Z]+-\\d+.*",
        r"[A-Z]+-\\d+/.*",
        r".*/[A-Z]+-\\d+.*",
    ])
```

### LoggingConfiguration

```python
@dataclass
class LoggingConfiguration:
    level: str = "INFO"
    daemon_log_dir: str = ""
    tui_log_dir: str = ""
    create_timestamped_daemon_logs: bool = True
    max_log_files: int = 30
    log_format: str = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    daemon_log_format: str = "[%(asctime)s] DAEMON %(levelname)s %(name)s: %(message)s"
    tui_log_format: str = "[%(asctime)s] TUI %(levelname)s %(name)s: %(message)s"
```

## Environment Variables

Configuration can be overridden with environment variables:

### Core Settings
- **`MKANBAN_DATA_DIR`**: Override data directory
- **`MKANBAN_CONFIG_DIR`**: Override configuration directory
- **`MKANBAN_THEME`**: Set UI theme (dark/light)
- **`MKANBAN_AUTO_SAVE_INTERVAL`**: Auto-save interval in seconds
- **`MKANBAN_DEBUG`**: Enable debug logging (true/false/1/0/yes/no)

### Editor Settings
- **`EDITOR`**: System editor preference
- **`MKANBAN_EDITOR`**: MKanban-specific editor override
- **`MKANBAN_CLI_EDITOR`**: CLI editor preference

### Path Settings
- **`MKANBAN_PATH`**: Direct path for session-based boards

### Example

```bash
export MKANBAN_DATA_DIR="/home/user/projects/boards"
export MKANBAN_THEME="light"
export MKANBAN_DEBUG="true"
export EDITOR="vim"

python main.py
```

## Configuration File

Settings are persisted to `~/.mkanban/config.json`:

```json
{
  "data_dir": "./mkanban/boards",
  "config_dir": "/home/user/.mkanban",
  "auto_save": true,
  "auto_save_interval": 30,
  "backup_count": 5,
  "theme": "dark",
  "show_parent_colors": true,
  "default_parent_view": false,
  "column_width": 30,
  "shortcuts": {
    "focus_next": "j",
    "focus_previous": "k",
    "focus_left": "h",
    "focus_right": "l",
    "new_item": "o",
    "edit_item": "i",
    "delete_item": "d",
    "move_left": "ctrl+h",
    "move_right": "ctrl+l",
    "toggle_parents": "p",
    "save": "w",
    "refresh": "r",
    "help": "g?",
    "quit": "q"
  },
  "daemon": {
    "enabled": true,
    "polling_interval": 5,
    "tmux_session_only": true,
    "enable_session_task_management": true,
    "auto_complete_on_session_switch": true,
    "auto_activate_on_session_switch": true,
    "session_name": "git-branches",
    "default_board": "git-branches",
    "default_column": "to-do",
    "in_progress_column": "in-progress",
    "done_column": "done",
    "branch_patterns": [
      "feature/*",
      "bugfix/*",
      "hotfix/*",
      "fix/*",
      "feat/*",
      "test",
      "test/*",
      "*"
    ],
    "excluded_branches": [
      "main",
      "master",
      "develop",
      "staging",
      "production"
    ],
    "jira": {
      "enabled": false,
      "api_url": "",
      "username": "",
      "api_token": "",
      "project_keys": [],
      "polling_interval": 300,
      "bidirectional_sync": false,
      "backlog_limit": 50,
      "status_mapping": {
        "To Do": "to-do",
        "In Progress": "in-progress",
        "Done": "done",
        "Backlog": "backlog"
      },
      "jql_filter": "",
      "board_name": "jira-tickets",
      "branch_patterns": [
        ".*[A-Z]+-\\\\d+.*",
        "[A-Z]+-\\\\d+/.*",
        ".*/[A-Z]+-\\\\d+.*"
      ]
    }
  },
  "logging": {
    "level": "INFO",
    "daemon_log_dir": "/home/user/.mkanban/logs/daemon",
    "tui_log_dir": "/home/user/.mkanban/logs/tui",
    "create_timestamped_daemon_logs": true,
    "max_log_files": 30,
    "log_format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    "daemon_log_format": "[%(asctime)s] DAEMON %(levelname)s %(name)s: %(message)s",
    "tui_log_format": "[%(asctime)s] TUI %(levelname)s %(name)s: %(message)s"
  }
}
```

## Loading Priority

Configuration is loaded in this priority order:

1. **Environment variables** (highest priority)
2. **JSON configuration file**
3. **Default values** (lowest priority)

## Session-based Configuration

MKanban supports session-aware data directories:

### MKANBAN_PATH Behavior
- **If set**: Used directly as the boards directory
- **If not set**: Uses `~/.mkanban/boards/{session_name}`

### Tmux Integration
- Automatically detects tmux sessions
- Creates session-specific board directories
- Falls back to configured `data_dir` if not in tmux

## Error Handling

- **Corrupted JSON**: Falls back to defaults with warning
- **Invalid environment variables**: Ignores invalid values
- **Missing directories**: Creates directories as needed
- **Permission errors**: Logs errors and continues with defaults

## Best Practices

### For Users
1. Use environment variables for temporary overrides
2. Edit JSON file for persistent changes
3. Use `MKANBAN_PATH` for project-specific setups
4. Enable debug mode when troubleshooting

### For Developers
1. Always use `get_config()` to access configuration
2. Add new settings to appropriate dataclass
3. Provide sensible defaults
4. Add environment variable mapping for user convenience
5. Document new configuration options

## Migration

The configuration system replaces the legacy `Settings` and `Environment` classes. Legacy code should be updated to use `ConfigurationManager`:

```python
# Old way
from src.config.settings import Settings
settings = Settings.load()

# New way
from src.config.configuration_manager import get_config
config_manager = get_config()
settings = config_manager.config
```