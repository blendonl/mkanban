# MKanban

A Terminal User Interface (TUI) Kanban board application that stores data in Markdown files.

## Features

- 📋 **Multiple Boards**: Create and manage multiple kanban boards
- 📝 **Markdown Storage**: All data stored in human-readable `.md` files
- 👥 **Parent Grouping**: Organize items hierarchically with parent-child relationships
- ⌨️ **Keyboard Shortcuts**: Full keyboard navigation and control
- 🎨 **Customizable**: Configurable themes and shortcuts
- 💾 **Auto-save**: Automatic saving with backup support

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mkanban
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Basic Usage

- **Navigate**: Use arrow keys or Tab to move between items
- **Create Item**: Press `n` to create a new item
- **Edit Item**: Press `e` to edit the selected item
- **Delete Item**: Press `d` to delete the selected item
- **Move Item**: Press `m` to move item to different column
- **Toggle Parent View**: Press `p` to group items by parent
- **Save**: Press `s` to save changes
- **Quit**: Press `q` to exit

## File Format

MKanban stores boards as Markdown files with YAML frontmatter:

```markdown
---
title: My Project Board
description: Project management board
parents:
  - id: feature-dev
    name: Feature Development
    color: green
---

## To Do

- Setup project structure
- Create data models [parent:feature-dev]

## In Progress

- Implement UI components [parent:feature-dev]

## Done

- Initialize repository
```

## Configuration

Create a configuration file at `~/.mkanban/config.json`:

```json
{
  "data_dir": "./data",
  "auto_save": true,
  "theme": "dark",
  "show_parent_colors": true,
  "shortcuts": {
    "quit": "q",
    "new_item": "n",
    "edit_item": "e"
  }
}
```

## Project Structure

```
mkanban/
├── src/
│   ├── models/          # Data models (Board, Column, Item, Parent)
│   ├── storage/         # Markdown file handling
│   ├── ui/              # TUI components and screens
│   ├── controllers/     # Business logic
│   └── utils/           # Configuration and utilities
├── data/                # Default board storage location
├── tests/               # Test files
├── main.py              # Application entry point
└── README.md            # This file
```

## Development

### Running Tests

```bash
python test_structure.py
```

### Code Style

```bash
black src/
flake8 src/
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Roadmap

- [ ] Import/export from other formats (Trello, JSON)
- [ ] File watching for external changes
- [ ] Search and filtering
- [ ] Drag and drop interface
- [ ] Multiple theme support
- [ ] Undo/redo functionality
- [ ] Statistics and reporting