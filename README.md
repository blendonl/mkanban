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

MKanban can be installed in three different ways depending on your needs:

#### Option 1: Install with pip (Recommended)

Best for development and regular use. Installs `mkanban` and `mkanban-daemon` commands globally.

```bash
# Clone the repository
git clone <repository-url>
cd mkanban

# Install in development mode (changes to code are immediately reflected)
pip install -e .

# Or for regular installation
pip install .
```

After installation, the commands are available globally:
```bash
mkanban --help
mkanban-daemon --help
```

**Note:** Ensure `~/.local/bin` is in your PATH. Add to `~/.bashrc` or `~/.zshrc` if needed:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

#### Option 2: Build Arch Linux Package

Best for Arch Linux users who want proper system integration with pacman.

```bash
# Clone the repository
git clone <repository-url>
cd mkanban

# Build and install the package
makepkg -si
```

This installs mkanban to `/usr/bin/mkanban` and is managed by pacman. To uninstall:
```bash
sudo pacman -R mkanban
```

#### Option 3: Build Standalone Executable

Best for creating a portable single-file executable (no Python runtime required at runtime).

```bash
# Clone the repository
git clone <repository-url>
cd mkanban

# Set up the environment (required for building)
make setup

# Build the executable
make executable

# Copy to a directory in your PATH
mkdir -p ~/.local/bin
cp dist/mkanban ~/.local/bin/

# Ensure ~/.local/bin is in PATH
export PATH="$HOME/.local/bin:$PATH"
```

The executable will be ~50MB and includes all dependencies.

#### Running from Source (Development)

If you prefer to run without installing:

```bash
# Set up the environment
make setup

# Run the application
python src/main.py
```

### Basic Usage

After installation (using any of the methods above):

```bash
# Start with default settings
mkanban

# Open a specific board
mkanban --board "my-project"

# Create a new task
mkanban new-task "Fix bug" --board "my-project"

# List tasks from a board
mkanban list --board "my-project"

# Checkout a git branch for a task
mkanban checkout "Fix bug" --board "my-project"

# Start the daemon for automatic git/JIRA sync
mkanban-daemon start
```

If running from source without installation:

```bash
python src/main.py --board "my-project"
```

## Key Bindings

| Key       | Action                      |
| --------- | --------------------------- |
| `h/j/k/l` | Navigate left/down/up/right |
| `H/L`     | Move items between columns  |
| `o`       | Create new item             |
| `i`       | Edit item                   |
| `d`       | Delete item                 |
| `p`       | Toggle parent grouping      |
| `w`       | Save                        |
| `r`       | Refresh                     |
| `g?`      | Show help                   |
| `q`       | Quit                        |

## Configuration

MKanban uses a unified configuration system with environment variable overrides:

### Environment Variables

- `MKANBAN_DATA_DIR`: Data directory path
- `MKANBAN_CONFIG_DIR`: Configuration directory path
- `MKANBAN_THEME`: UI theme (dark/light)
- `MKANBAN_DEBUG`: Enable debug logging (true/false)
- `MKANBAN_PATH`: Direct path for session-based boards
- `EDITOR`: Preferred text editor

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
make executable        # Build standalone executable with PyInstaller (~50MB)
make dist             # Create distribution packages (wheel/sdist)
make clean             # Clean build artifacts
make clean-all         # Clean everything including venv
```

### Building & Distribution

```bash
# Install locally for development
pip install -e .

# Build standalone executable (requires PyInstaller)
make executable        # Output: dist/mkanban

# Build distribution packages
make dist             # Output: dist/*.whl and dist/*.tar.gz

# Build Arch Linux package
makepkg -si           # Creates and installs .pkg.tar.zst
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

