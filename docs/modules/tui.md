# TUI Components and Architecture

MKanban's Terminal User Interface (TUI) is built using the Textual framework, providing a rich, responsive interface with vim-style keybindings and real-time updates.

## Overview

The TUI architecture consists of:

- **MKanbanApp**: Main application class with screen management
- **Widget Components**: Specialized UI components for boards, columns, and items
- **Dialog System**: Modal dialogs for user interactions
- **Keybinding System**: Vim-inspired keyboard shortcuts
- **Theme Support**: Dark/light themes with customizable colors

## MKanbanApp

The main application class that orchestrates the entire TUI experience.

### Structure

```python
class MKanbanApp(App):
    """Main MKanban application using Textual framework."""

    CSS_PATH = "mkanban.css"
    BINDINGS = [
        ("g?", "help", "Help"),
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("w", "save", "Save"),
        # ... more bindings
    ]

    def __init__(self, board_name: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.board_name = board_name
        self.container = get_container()
        self.logger = self.container.get_tui_logger("app")
```

### Key Features

#### Screen Management

```python
SCREENS = {
    "board": BoardScreen,
    "help": HelpScreen,
    "settings": SettingsScreen,
}

def on_mount(self) -> None:
    """Initialize the application."""
    self.push_screen("board", board_name=self.board_name)

def action_help(self) -> None:
    """Show help screen."""
    self.push_screen("help")

def action_settings(self) -> None:
    """Show settings screen."""
    self.push_screen("settings")
```

#### Auto-save System

```python
def on_mount(self) -> None:
    config = self.container.get(ConfigurationManager).config
    if config.auto_save:
        self.set_interval(
            config.auto_save_interval,
            self.auto_save
        )

def auto_save(self) -> None:
    """Automatically save the current board."""
    current_screen = self.screen
    if hasattr(current_screen, 'save_board'):
        current_screen.save_board()
        self.logger.debug("Auto-save completed")
```

#### Theme Management

```python
def on_mount(self) -> None:
    config = self.container.get(ConfigurationManager).config
    self.dark = (config.theme == ThemeType.DARK.value)

def action_toggle_theme(self) -> None:
    """Toggle between dark and light themes."""
    self.dark = not self.dark
    config_manager = self.container.get(ConfigurationManager)
    new_theme = ThemeType.DARK.value if self.dark else ThemeType.LIGHT.value
    config_manager.update_configuration(theme=new_theme)
```

### Keybinding System

#### Vim-Style Navigation

```python
BINDINGS = [
    # Movement
    ("j", "focus_next", "Focus Next"),
    ("k", "focus_previous", "Focus Previous"),
    ("h", "focus_left", "Focus Left"),
    ("l", "focus_right", "Focus Right"),
    ("g,g", "focus_first", "Focus First"),
    ("G", "focus_last", "Focus Last"),

    # Actions
    ("o", "new_item", "New Item"),
    ("i", "edit_item", "Edit Item"),
    ("d", "delete_item", "Delete Item"),
    ("ctrl+h", "move_left", "Move Left"),
    ("ctrl+l", "move_right", "Move Right"),

    # Board operations
    ("p", "toggle_parents", "Toggle Parents"),
    ("w", "save", "Save"),
    ("r", "refresh", "Refresh"),
]
```

#### Dynamic Keybinding Configuration

```python
def setup_keybindings(self) -> None:
    """Setup keybindings from configuration."""
    config = self.container.get(ConfigurationManager).config
    shortcuts = config.shortcuts

    # Apply configured shortcuts
    self.BINDINGS = [
        (shortcuts.get("focus_next", "j"), "focus_next", "Focus Next"),
        (shortcuts.get("focus_previous", "k"), "focus_previous", "Focus Previous"),
        # ... more bindings from config
    ]
```

## BoardScreen

The main screen displaying the Kanban board with columns and items.

### Structure

```python
class BoardScreen(Screen):
    """Main board display screen."""

    def __init__(self, board_name: Optional[str] = None):
        super().__init__()
        self.board_name = board_name
        self.container = get_container()
        self.board_service = self.container.get(BoardService)
        self.logger = self.container.get_tui_logger("board_screen")

    def compose(self) -> ComposeResult:
        """Compose the board layout."""
        with Horizontal():
            yield BoardWidget(board_name=self.board_name)
            if self.show_sidebar:
                yield Sidebar()
```

### Features

#### Real-time Updates

```python
def on_mount(self) -> None:
    """Setup real-time updates."""
    self.set_interval(5.0, self.check_for_updates)

def check_for_updates(self) -> None:
    """Check for external updates to the board."""
    if self.board_widget.needs_refresh():
        self.board_widget.refresh_board()
        self.logger.debug("Board refreshed from external changes")
```

#### Focus Management

```python
def action_focus_next(self) -> None:
    """Focus the next item."""
    current_focus = self.focused
    if isinstance(current_focus, ItemWidget):
        next_item = self.board_widget.get_next_item(current_focus)
        if next_item:
            next_item.focus()

def action_focus_column(self, column_index: int) -> None:
    """Focus a specific column."""
    column_widget = self.board_widget.get_column_widget(column_index)
    if column_widget:
        column_widget.focus()
```

## BoardWidget

The main widget displaying the Kanban board with columns and items.

### Structure

```python
class BoardWidget(Widget):
    """Widget displaying the full Kanban board."""

    def __init__(self, board_name: Optional[str] = None):
        super().__init__()
        self.board_name = board_name
        self.container = get_container()
        self.board_service = self.container.get(BoardService)
        self.item_service = self.container.get(ItemService)
        self.logger = self.container.get_tui_logger("board_widget")

    def compose(self) -> ComposeResult:
        """Compose the board layout."""
        if self.board:
            with Horizontal(classes="board-container"):
                for column in self.board.columns:
                    yield ColumnWidget(
                        board=self.board,
                        column=column,
                        show_parents=self.show_parents
                    )
```

### Features

#### Board Loading

```python
def on_mount(self) -> None:
    """Load the board on mount."""
    self.load_board()

def load_board(self) -> None:
    """Load board data from storage."""
    self.logger.set_context(board=self.board_name)

    try:
        self.board = self.board_service.load_board(self.board_name)
        if self.board:
            self.logger.info("Board loaded successfully")
            self.refresh_display()
        else:
            self.logger.warning("Board not found")
            self.show_board_not_found()
    except Exception as e:
        self.logger.error("Failed to load board", error=str(e))
        self.show_error("Failed to load board")
```

#### Parent Grouping

```python
def toggle_parent_view(self) -> None:
    """Toggle between parent-grouped and flat item view."""
    self.show_parents = not self.show_parents
    self.logger.debug("Toggled parent view", show_parents=self.show_parents)

    # Refresh all column widgets
    for column_widget in self.query(ColumnWidget):
        column_widget.show_parents = self.show_parents
        column_widget.refresh_items()
```

#### Drag and Drop

```python
def on_item_dropped(self, message: ItemDropped) -> None:
    """Handle item dropped on board."""
    item = message.item
    target_column = message.target_column
    target_position = message.target_position

    self.logger.debug("Item dropped",
                     item=item.title,
                     source_column=item.column_id,
                     target_column=target_column.id,
                     position=target_position)

    # Move item via service
    success = self.item_service.move_item(
        self.board, item, target_column, target_position
    )

    if success:
        self.refresh_display()
        self.logger.info("Item moved successfully", item=item.title)
    else:
        self.logger.error("Failed to move item", item=item.title)
```

## ColumnWidget

Widget representing an individual column with its items.

### Structure

```python
class ColumnWidget(Widget):
    """Widget for displaying a single column."""

    def __init__(
        self,
        board: Board,
        column: Column,
        show_parents: bool = False
    ):
        super().__init__()
        self.board = board
        self.column = column
        self.show_parents = show_parents
        self.container = get_container()
        self.logger = self.container.get_tui_logger("column_widget")

    def compose(self) -> ComposeResult:
        """Compose the column layout."""
        with Vertical(classes="column"):
            yield ColumnHeader(column=self.column)
            with ScrollableContainer(classes="column-items"):
                yield from self.render_items()
```

### Features

#### Item Rendering

```python
def render_items(self) -> Generator[Widget, None, None]:
    """Render items based on parent grouping setting."""
    if self.show_parents:
        yield from self.render_grouped_items()
    else:
        yield from self.render_flat_items()

def render_flat_items(self) -> Generator[ItemWidget, None, None]:
    """Render items in a flat list."""
    for item in self.column.items:
        yield ItemWidget(
            board=self.board,
            item=item,
            column=self.column
        )

def render_grouped_items(self) -> Generator[Widget, None, None]:
    """Render items grouped by parent."""
    # Group items by parent
    orphaned_items = []
    parent_groups = {}

    for item in self.column.items:
        if item.parent_id:
            if item.parent_id not in parent_groups:
                parent_groups[item.parent_id] = []
            parent_groups[item.parent_id].append(item)
        else:
            orphaned_items.append(item)

    # Render orphaned items first
    for item in orphaned_items:
        yield ItemWidget(board=self.board, item=item, column=self.column)

    # Render parent groups
    for parent_id, items in parent_groups.items():
        parent = self.board.get_parent_by_id(parent_id)
        if parent:
            yield ParentGroupWidget(
                board=self.board,
                parent=parent,
                items=items,
                column=self.column
            )
```

#### WIP Limits

```python
def render_header(self) -> ColumnHeader:
    """Render column header with WIP limit indicator."""
    item_count = len(self.column.items)
    is_over_limit = (
        self.column.limit is not None and
        item_count > self.column.limit
    )

    return ColumnHeader(
        column=self.column,
        item_count=item_count,
        is_over_limit=is_over_limit
    )
```

#### Drag and Drop Support

```python
def on_item_drag_start(self, message: ItemDragStart) -> None:
    """Handle start of item drag operation."""
    self.add_class("drag-source")
    self.logger.debug("Drag started", item=message.item.title)

def on_item_drag_end(self, message: ItemDragEnd) -> None:
    """Handle end of item drag operation."""
    self.remove_class("drag-source")
    self.remove_class("drag-target")

def can_accept_drop(self, item: Item) -> bool:
    """Check if this column can accept a dropped item."""
    if self.column.limit is None:
        return True
    return len(self.column.items) < self.column.limit
```

## ItemWidget

Widget representing individual items within columns.

### Structure

```python
class ItemWidget(Widget):
    """Widget for displaying individual items."""

    def __init__(
        self,
        board: Board,
        item: Item,
        column: Column
    ):
        super().__init__()
        self.board = board
        self.item = item
        self.column = column
        self.container = get_container()
        self.logger = self.container.get_tui_logger("item_widget")

    def compose(self) -> ComposeResult:
        """Compose the item layout."""
        with Horizontal(classes="item"):
            yield ItemIcon(item=self.item)
            yield ItemContent(item=self.item)
            if self.item.has_parent:
                yield ParentIndicator(parent_id=self.item.parent_id)
```

### Features

#### Item Display

```python
def render_content(self) -> RenderableType:
    """Render item content with metadata."""
    content = Text()

    # Add title
    content.append(self.item.title, style="bold")

    # Add Git information
    if self.item.is_git_managed and self.item.git_metadata:
        branch_style = "green" if self.item.git_metadata.is_current_branch else "dim"
        content.append(f" [{self.item.git_metadata.branch_name}]", style=branch_style)

        if commit := self.item.get_short_commit_hash():
            content.append(f" ({commit})", style="dim")

    # Add JIRA information
    if self.item.is_jira_managed and self.item.jira_metadata:
        content.append(f" [JIRA:{self.item.jira_metadata.ticket_key}]", style="blue")

    # Add description preview
    if self.item.description:
        preview = self.item.description[:50] + "..." if len(self.item.description) > 50 else self.item.description
        content.append(f"\n{preview}", style="dim")

    return content
```

#### Interaction Handling

```python
def on_click(self, event: Click) -> None:
    """Handle item click."""
    self.focus()
    self.logger.debug("Item clicked", item=self.item.title)

def on_key(self, event: Key) -> None:
    """Handle item key events."""
    if event.key == "i":
        self.edit_item()
    elif event.key == "d":
        self.delete_item()
    elif event.key == "enter":
        self.view_item_details()

def edit_item(self) -> None:
    """Open item for editing."""
    self.app.push_screen(
        EditItemDialog(
            board=self.board,
            item=self.item,
            column=self.column
        )
    )
```

#### Status Indicators

```python
def get_item_style(self) -> str:
    """Get CSS class based on item status."""
    classes = ["item"]

    if self.item.is_git_managed:
        classes.append("git-item")
        if self.item.git_metadata and self.item.git_metadata.is_current_branch:
            classes.append("current-branch")

    if self.item.is_jira_managed:
        classes.append("jira-item")

    if self.item.has_parent:
        classes.append("has-parent")

    return " ".join(classes)
```

## Dialog System

Modal dialogs for user interactions and data entry.

### EditItemDialog

```python
class EditItemDialog(ModalScreen):
    """Dialog for editing item details."""

    def __init__(self, board: Board, item: Item, column: Column):
        super().__init__()
        self.board = board
        self.item = item
        self.column = column

    def compose(self) -> ComposeResult:
        with Container():
            yield Input(value=self.item.title, placeholder="Item title", id="title")
            yield TextArea(text=self.item.description, id="description")
            yield Select(
                [(col.name, col.id) for col in self.board.columns],
                value=self.item.column_id,
                id="column"
            )
            yield Select(
                [("None", None)] + [(parent.name, parent.id) for parent in self.board.parents],
                value=self.item.parent_id,
                id="parent"
            )
            with Horizontal():
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_item()
        else:
            self.dismiss()

    def save_item(self) -> None:
        """Save item changes."""
        title = self.query_one("#title", Input).value
        description = self.query_one("#description", TextArea).text
        column_id = self.query_one("#column", Select).value
        parent_id = self.query_one("#parent", Select).value

        # Update item via service
        item_service = get_container().get(ItemService)
        success = item_service.update_item(
            self.board,
            self.item,
            title=title,
            description=description
        )

        if success and column_id != self.item.column_id:
            target_column = self.board.get_column_by_id(column_id)
            if target_column:
                item_service.move_item(self.board, self.item, target_column)

        if success:
            self.item.set_parent(parent_id)

        self.dismiss(success)
```

### ConfirmationDialog

```python
class ConfirmationDialog(ModalScreen):
    """Generic confirmation dialog."""

    def __init__(self, message: str, title: str = "Confirm"):
        super().__init__()
        self.message = message
        self.title = title

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.title, classes="dialog-title")
            yield Label(self.message)
            with Horizontal():
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")
```

## CSS Theming

Comprehensive CSS styling with theme support.

### Base Styles

```css
/* Dark theme */
App.-dark-mode {
    background: #1e1e1e;
    color: #ffffff;
}

App.-dark-mode .board-container {
    background: #2d2d2d;
}

App.-dark-mode .column {
    background: #3d3d3d;
    border: 1px solid #555555;
}

/* Light theme */
App {
    background: #ffffff;
    color: #000000;
}

.board-container {
    background: #f5f5f5;
}

.column {
    background: #ffffff;
    border: 1px solid #cccccc;
}
```

### Component Styles

```css
.item {
    padding: 1;
    margin: 1;
    border-radius: 1;
}

.item:focus {
    border: 2px solid #0066cc;
}

.git-item {
    border-left: 3px solid #00aa00;
}

.jira-item {
    border-left: 3px solid #0052cc;
}

.current-branch {
    background: rgba(0, 170, 0, 0.1);
}

.has-parent {
    margin-left: 2;
}
```

## Performance Optimizations

### Virtual Scrolling

```python
class VirtualScrollableContainer(ScrollableContainer):
    """Scrollable container with virtual rendering for large lists."""

    def __init__(self, items: List[Item], item_height: int = 3):
        super().__init__()
        self.items = items
        self.item_height = item_height
        self.visible_start = 0
        self.visible_count = 10

    def render_visible_items(self) -> None:
        """Render only visible items for performance."""
        visible_items = self.items[self.visible_start:self.visible_start + self.visible_count]

        # Clear current items
        self.query(ItemWidget).remove()

        # Add visible items
        for item in visible_items:
            self.mount(ItemWidget(item=item))
```

### Efficient Updates

```python
def refresh_items(self, changed_items: Optional[Set[str]] = None) -> None:
    """Efficiently refresh only changed items."""
    if changed_items is None:
        # Full refresh
        self.refresh()
        return

    # Partial refresh - only update changed items
    for item_widget in self.query(ItemWidget):
        if item_widget.item.id in changed_items:
            item_widget.refresh()
```

## Best Practices

### Widget Development

1. **Single Responsibility**: Each widget should have one clear purpose
2. **Reactive Updates**: Use reactive properties for automatic updates
3. **Event Handling**: Handle events at the appropriate level
4. **CSS Classes**: Use CSS classes for styling instead of inline styles
5. **Accessibility**: Support keyboard navigation and screen readers

### Performance

1. **Virtual Rendering**: Use virtual scrolling for large lists
2. **Selective Updates**: Only refresh changed components
3. **Lazy Loading**: Load content on demand
4. **Debounced Input**: Debounce user input for better performance
5. **Memory Management**: Remove event listeners when widgets are destroyed

### User Experience

1. **Consistent Keybindings**: Follow vim conventions consistently
2. **Visual Feedback**: Provide clear feedback for all actions
3. **Error Handling**: Show helpful error messages
4. **Progressive Disclosure**: Hide complexity behind simple interfaces
5. **Responsive Design**: Adapt to different terminal sizes

The TUI architecture provides a rich, responsive interface that feels natural to vim users while offering modern UI patterns and excellent performance.