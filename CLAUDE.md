# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MKanban is a Terminal User Interface (TUI) Kanban board application built with Python and Textual. It manages tasks using markdown files stored in a hierarchical folder structure.

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
python test_operations.py  # Run specific debugging tests
```

### Building
```bash
make executable        # Build standalone executable with PyInstaller
make dist             # Create distribution packages (sdist/bdist_wheel)
```

### Running the Application
```bash
python main.py                        # Run with default data directory (./data)
python main.py --data-dir /path/to/data  # Use custom data directory
python main.py --board "board-name"     # Open specific board
python main.py --new-task-title "Task" --board "board-name"  # Create task via CLI
```

## Architecture

### Core Components

- **MKanbanApp** (`src/app.py`): Main Textual application with vim-style keybindings
- **BoardStorage** (`src/storage/board_storage.py`): Handles markdown file I/O and persistence
- **MarkdownStorage** (`src/storage/markdown_storage.py`): High-level storage interface
- **Models** (`src/models/`): Pydantic models for Board, Column, Item, Parent
- **Controllers** (`src/controllers/`): Business logic for board operations
- **UI Widgets** (`src/ui/widgets/`): Textual widgets for TUI components

### Data Structure

Boards are stored as markdown files with frontmatter metadata:
```
data/boards/{board-name}/
├── kanban.md           # Board metadata and structure
├── {column-name}/      # Column folders
│   ├── column.md       # Column metadata (optional)
│   └── *.md           # Item files
```

### Key Design Patterns

- **Storage Layer**: Separates file I/O from business logic using storage interfaces
- **MVC Pattern**: Controllers mediate between models and UI widgets  
- **Reactive UI**: Uses Textual's reactive properties for state management
- **File-based Persistence**: Each item is a markdown file with frontmatter metadata

### Vim-style Navigation

The application uses vim-inspired keybindings:
- `h/j/k/l`: Navigate left/down/up/right
- `H/L`: Move items between columns  
- `o`: Create new item
- `i`: Edit item
- `d`: Delete item
- `p`: Toggle parent grouping
- `g?`: Show help dialog

## Configuration

Configuration is handled through `src/utils/config.py` with settings for data directory, auto-save, and editor preferences.