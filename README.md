# MKanban

A powerful Terminal User Interface (TUI) Kanban board application built with Python and Textual. MKanban manages tasks using markdown files stored in a hierarchical folder structure, providing a vim-inspired interface for efficient task management.

## Features

- **Vim-style Navigation**: Navigate with `hjkl` keys and vim-inspired keybindings
- **Markdown-based Storage**: Tasks stored as markdown files with frontmatter metadata
- **Session-aware**: Automatically organizes boards by tmux session
- **JIRA Integration**: Synchronize with JIRA projects and tickets
- **Daemon Mode**: Background process for automatic task synchronization
- **Customizable**: Configurable themes, keybindings, and data directories
- **Parent/Child Tasks**: Hierarchical task organization with grouping
- **Auto-save**: Automatic saving with configurable intervals

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mkanban

# Set up the environment
make setup

# Run the application
python main.py
```

### Basic Usage

```bash
# Start with default settings
python main.py

# Use a specific data directory
python main.py --data-dir /path/to/boards

# Open a specific board
python main.py --board "my-project"

# Create a task via CLI
python main.py --new-task-title "Fix bug" --board "my-project"
```

## Key Bindings

| Key | Action |
|-----|--------|
| `h/j/k/l` | Navigate left/down/up/right |
| `H/L` | Move items between columns |
| `o` | Create new item |
| `i` | Edit item |
| `d` | Delete item |
| `p` | Toggle parent grouping |
| `w` | Save |
| `r` | Refresh |
| `g?` | Show help |
| `q` | Quit |

## Configuration

MKanban uses a unified configuration system with environment variable overrides:

### Environment Variables

- `MKANBAN_DATA_DIR`: Data directory path
- `MKANBAN_CONFIG_DIR`: Configuration directory path
- `MKANBAN_THEME`: UI theme (dark/light)
- `MKANBAN_DEBUG`: Enable debug logging (true/false)
- `MKANBAN_PATH`: Direct path for session-based boards
- `EDITOR`: Preferred text editor
- `MKANBAN_CLI_EDITOR`: CLI editor preference

### Configuration File

Configuration is stored in `~/.mkanban/config.json`:

```json
{
  "data_dir": "./mkanban/boards",
  "theme": "dark",
  "auto_save": true,
  "auto_save_interval": 30,
  "daemon": {
    "enabled": true,
    "polling_interval": 5,
    "jira": {
      "enabled": false,
      "api_url": "",
      "username": "",
      "api_token": ""
    }
  }
}
```

## Data Structure

Boards are organized in a hierarchical folder structure:

```
data/boards/{board-name}/
├── kanban.md           # Board metadata and structure
├── {column-name}/      # Column folders
│   ├── column.md       # Column metadata (optional)
│   └── *.md           # Item files
```

### Board Structure

Each board contains:
- **kanban.md**: Board metadata with column definitions
- **Column folders**: Named directories for each column
- **Item files**: Markdown files with frontmatter metadata

### Item Format

Items are stored as markdown files with YAML frontmatter:

```markdown
---
title: "Task Title"
status: "in-progress"
created_at: "2024-01-01T10:00:00"
parent: "parent-task-id"
---

# Task Description

Detailed description of the task...
```

## JIRA Integration

MKanban can synchronize with JIRA projects:

1. **Configure JIRA settings** in config.json
2. **Enable daemon mode** for automatic synchronization
3. **Map JIRA statuses** to board columns
4. **Set up JQL filters** for specific ticket queries

## Development

### Commands

```bash
make setup              # Create venv and install dependencies
make lint              # Run linting (flake8, mypy, ruff)
make format            # Format code with black
make test              # Run pytest tests
make executable        # Build standalone executable
make dist             # Create distribution packages
```

### Architecture

MKanban follows clean architecture principles:

- **Domain Layer**: Models and core business logic
- **Service Layer**: Business operations and orchestration
- **Infrastructure Layer**: Storage, JIRA integration, TUI
- **Dependency Injection**: Centralized container for all dependencies

See the [Architecture Documentation](docs/architecture/) for detailed information.

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- [Architecture Overview](docs/architecture/README.md)
- [Module Documentation](docs/modules/)
- [Development Guide](docs/guides/development.md)
- [API Reference](docs/api/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `make test`
4. Ensure code quality: `make lint`
5. Submit a pull request

## License

[License information here]

## Support

For issues and feature requests, please use the GitHub issue tracker.