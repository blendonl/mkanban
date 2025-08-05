# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MKanban is a Terminal User Interface (TUI) Kanban board application written in Python. It stores data in Markdown files and supports hierarchical item organization through parent-child relationships.

## Architecture

### Core Components

- **Models**: Data classes for Board, Column, Item, and Parent entities
- **Storage**: Markdown file I/O handling with frontmatter parsing
- **UI**: TUI components using textual framework
- **Controllers**: Business logic for managing boards, items, and relationships

### File Structure Recommendations

```
mkanban/
├── src/
│   ├── models/          # Data models (Board, Column, Item, Parent)
│   ├── storage/         # Markdown file handling
│   ├── ui/              # TUI components and screens
│   ├── controllers/     # Business logic
│   └── utils/           # Helper functions
├── data/                # Default location for .md board files
├── tests/               # Test files
└── main.py              # Entry point
```

## Key Implementation Guidelines

### Vim Motions

- The tui should be navigatable by vim motions
- The textareas should be editable with vim motions

### Markdown Format Design

- For each board there should be created a new folder named by the board
- The board should create a new board.md file inside that folder
- Represent columns as H2 headers (`## Column Name`)
- For each column a new folder should be created inside that folder
- Each item of a column should be a link to a new .md file inside the column folder where the title of the link is the first heading of the new file
- Items as bullet points with optional sub-items for parent-child relationships
- Use consistent metadata format in item descriptions

### TUI Framework Choice

Recommend **Textual** over alternatives:

- Modern, actively maintained
- Rich widget ecosystem
- Good documentation and examples
- Built-in CSS-like styling
- Reactive programming model

### Data Flow

1. Load .md files into memory models on startup
2. Keep models synchronized with UI state
3. Write changes back to .md files on modification
4. Implement auto-save with debouncing

### Parent-Child Relationships

- Store parent ID in item metadata
- Provide toggle view: flat list vs grouped by parent
- Allow move with vim keybinds between parents and columns
- Support nested hierarchies (parent → child → grandchild)

## Development Commands

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Or install manually if pip is not available:
# You may need to install dependencies through your system package manager
# For example on Arch Linux: pacman -S python-textual python-pydantic python-frontmatter python-click

# Alternative installation without pip:
# 1. Download dependencies manually from PyPI
# 2. Use system package managers where available
# 3. Use conda or other package managers
```

### Running

```bash
python main.py
```

### Testing

```bash
pytest
python -m pytest tests/ -v
```

### Code Quality

```bash
black src/
flake8 src/
mypy src/
```

## Suggested Libraries

- **textual**: TUI framework
- **pydantic**: Data validation and models
- **python-frontmatter**: YAML frontmatter parsing
- **click**: CLI argument parsing
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking

## Implementation Status

### ✅ Completed Features

1. **Core Data Models**: Board, Column, Item, Parent with full relationships
2. **Markdown Storage**: Complete parser and generator for .md files with YAML frontmatter
3. **TUI Framework**: Full Textual-based interface with keyboard navigation
4. **Board Management**: Load, create, and manage multiple boards
5. **Item Operations**: Create, edit, delete, move items with dialog interfaces
6. **Parent Grouping**: Hierarchical organization with toggle views
7. **Configuration System**: JSON-based config with customizable shortcuts
8. **Documentation**: Complete README, USAGE guide, and examples

### 🔄 Future Enhancements

1. **Real-time file watching**: Monitor external changes to .md files
2. **Search and filtering**: Find items by title, parent, or metadata
3. **Import/export**: Support for Trello, JSON, and other formats
4. **Undo/redo system**: Track and revert changes
5. **Advanced themes**: Multiple color schemes and layouts
6. **Drag-and-drop**: Mouse-based item movement
7. **Statistics**: Board analytics and reporting
8. **Vim Motions**: Complete vim motions integration

## File Naming Conventions

- Board folder: `{board-name}.md` (lowercase, hyphens for space)
- Board files: `board.md`
- Column folders: `{column-name}.md` (lowercase, hyphens for space)
- Item files: `{item-name}.md` (lowercase, hyphens for space)
- Code files: snake_case for Python modules
- Test files: `test_{module_name}.py`

## Error Handling

- Graceful degradation when .md files are malformed
- User-friendly error messages in TUI
- Automatic backup before destructive operations
- Validate data integrity on load and save

## Performance Considerations

- Lazy load large boards
- Debounce file writes to avoid excessive I/O
- Cache parsed markdown in memory
- Efficient UI updates (only refresh changed components)

