# MKanban Usage Guide

This guide covers how to use MKanban effectively for project management.

## Getting Started

### First Run

When you first run MKanban, it will create a sample board to get you started:

```bash
python main.py
```

This creates a default board in `./data/sample.md`. You can also specify a different data directory:

```bash
python main.py --data-dir ~/my-projects
```

### Loading Specific Boards

To load a specific board by name:

```bash
python main.py --board demo
```

This will load `./data/demo.md`.

## Keyboard Shortcuts

| Key     | Action         | Description                                   |
| ------- | -------------- | --------------------------------------------- |
| `q`     | Quit           | Exit the application                          |
| `n`     | New Item       | Create a new item                             |
| `e`     | Edit           | Edit the selected item                        |
| `d`     | Delete         | Delete the selected item                      |
| `m`     | Move           | Move item to different column                 |
| `p`     | Toggle Parents | Switch between column and parent-grouped view |
| `s`     | Save           | Save changes to file                          |
| `r`     | Refresh        | Refresh the display                           |
| `Tab`   | Navigate       | Move focus between items                      |
| `↑↓←→`  | Navigate       | Arrow key navigation                          |
| `Enter` | Select         | Select/activate focused item                  |
| `Esc`   | Cancel         | Cancel current dialog                         |

## Board Management

### Creating Boards

MKanban boards are just Markdown files. You can create them manually or through the application:

1. **Manual creation**: Create a `.md` file in your data directory
2. **Copy existing**: Duplicate and modify an existing board file
3. **Through app**: Use the application to create items and save

### Board Structure

Each board file contains:

- **YAML frontmatter**: Metadata including title, description, and parent definitions
- **Markdown content**: Columns (H2 headers) and items (bullet points)

Example structure:

```markdown
---
title: My Project
description: Project management board
parents:
  - id: feature-dev
    name: Feature Development
    color: green
---

## To Do

- Task 1
- Task 2 [parent:feature-dev]

## In Progress

- Task 3 [parent:feature-dev]

## Done

- Completed task
```

## Working with Items

### Creating Items

1. Press `n` to open the New Item dialog
2. Enter a title (required)
3. Select a column from the dropdown
4. Optionally assign a parent group
5. Click "Create" or press Enter

### Editing Items

1. Navigate to an item using Tab or arrow keys
2. Press `e` to open the Edit dialog
3. Modify title, description, column, or parent
4. Click "Update" to save changes

### Moving Items

1. Select an item
2. Press `m` to open the Move dialog
3. Choose the target column
4. Click "Move" to relocate the item

### Deleting Items

1. Select an item
2. Press `d` to delete
3. Confirm the deletion in the dialog

## Parent Groups

Parent groups allow you to organize related items across columns.

### Creating Parents

Parents are defined in the board's YAML frontmatter. You can add them by:

1. Editing the `.md` file directly
2. Using the board management features (if implemented)

### Assigning Items to Parents

When creating or editing items, select a parent from the dropdown menu. Items with parents will show the parent name below the title.

### Parent View Mode

Press `p` to toggle between:

- **Column View**: Traditional kanban columns
- **Parent View**: Items grouped by their parent, regardless of column

## File Format Details

### YAML Frontmatter

```yaml
---
title: Board Name
description: Board description
created_at: 2024-01-01T00:00:00
updated_at: 2024-01-01T00:00:00
board_metadata: {}
parents:
  - id: unique-parent-id
    name: Parent Display Name
    description: Parent description
    color: blue
    created_at: 2024-01-01T00:00:00
    updated_at: 2024-01-01T00:00:00
    metadata: {}
---
```

### Item Format

Basic item:

```markdown
- Item title
```

Item with parent:

```markdown
- Item title [parent:parent-id]
```

Item with metadata:

```markdown
- Item title {priority:high,assignee:john}
```

Item with both:

```markdown
- Item title [parent:parent-id] {priority:high}
```

## Configuration

Create `~/.mkanban/config.json` to customize settings:

```json
{
  "data_dir": "./data",
  "auto_save": true,
  "auto_save_interval": 30,
  "theme": "dark",
  "show_parent_colors": true,
  "default_parent_view": false,
  "shortcuts": {
    "quit": "q",
    "new_item": "n",
    "edit_item": "e",
    "delete_item": "d",
    "move_item": "m",
    "toggle_parents": "p",
    "save": "s",
    "refresh": "r"
  }
}
```

## Tips and Best Practices

### Organizing Projects

1. **Use descriptive column names**: Instead of "To Do", use "Backlog", "Sprint Planning", etc.
2. **Create meaningful parent groups**: Group by feature, epic, or team
3. **Keep items concise**: Use short titles and longer descriptions
4. **Regular maintenance**: Archive completed items periodically

### Keyboard Efficiency

1. **Learn the shortcuts**: Memorize common key bindings
2. **Use Tab navigation**: Faster than mouse for selection
3. **Batch operations**: Make multiple changes before saving

### File Management

1. **Backup regularly**: Keep copies of important boards
2. **Use version control**: Track board changes with git
3. **Descriptive filenames**: Use meaningful names like `project-alpha.md`
4. **Organize by project**: Use subdirectories for large projects

## Troubleshooting

### Common Issues

**Board won't load**

- Check file format and YAML syntax
- Ensure file exists in data directory
- Verify parent IDs are unique

**Items not displaying**

- Check column headers are H2 format (`## Column Name`)
- Verify item format with proper bullet points
- Ensure parent IDs match defined parents

**Can't save changes**

- Check file permissions
- Ensure data directory exists
- Verify disk space availability

### Getting Help

- Check the README.md for basic information
- Review sample boards for format examples
- Run tests to verify installation: `python test_structure.py`

