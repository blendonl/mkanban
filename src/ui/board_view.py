"""Board view widget for displaying kanban boards."""

from typing import Optional, List, Dict
from textual.widgets import Static, Markdown, TextArea
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual import events
from textual.reactive import reactive

from ..models import Board, Column, Item, Parent
from .vim_widgets import VimTextArea


class EditableItemWidget(Vertical):
    """Widget for inline editing of items with markdown."""

    def __init__(self, item: Optional[Item] = None, parent_name: Optional[str] = None,
                 is_new: bool = False, on_save: Optional[callable] = None,
                 on_cancel: Optional[callable] = None):
        """Initialize editable item widget."""
        self.item = item
        self.parent_name = parent_name
        self.is_new = is_new
        self.on_save = on_save
        self.on_cancel = on_cancel
        super().__init__(classes="editable-item")
        self.can_focus = True

    def compose(self):
        """Compose the editable item."""
        if self.item and self.item.description:
            initial_text = self.item.description
        elif self.item:
            initial_text = f"# {self.item.title}\n\n"
        else:
            initial_text = "# New Item\n\n"

        yield VimTextArea(initial_text, id="item_editor", classes="item-editor")

    def on_mount(self) -> None:
        """Focus the editor when mounted."""
        editor = self.query_one("#item_editor", VimTextArea)
        editor.focus()

    def save_item(self) -> None:
        """Save the item content."""
        editor = self.query_one("#item_editor", VimTextArea)
        content = editor.text.strip()

        if not content:
            return

        # Extract title from first # line
        lines = content.split('\n')
        title = "Untitled"
        for line in lines:
            if line.strip().startswith('# '):
                title = line.strip()[2:].strip()
                break

        if self.on_save:
            self.on_save(title, content)

    def cancel_edit(self) -> None:
        """Cancel editing."""
        if self.on_cancel:
            self.on_cancel()

    def on_key(self, event) -> None:
        """Handle key events."""
        if event.key == "escape":
            self.save_item()
            event.prevent_default()


class ItemWidget(Vertical):
    """Widget representing a single kanban item."""

    def __init__(self, item: Item, parent_name: Optional[str] = None):
        """Initialize item widget."""
        self.item = item
        self.parent_name = parent_name
        super().__init__(classes="item")
        self.can_focus = True

    def compose(self):
        yield MarkDown(self.item)

    def on_focus(self) -> None:
        """Handle focus event."""
        self.add_class("selected")

    def on_blur(self) -> None:
        """Handle blur event."""
        self.remove_class("selected")


class MarkDown(Markdown):
    """Widget representing a single kanban item."""

    def __init__(self, item: Item, parent_name: Optional[str] = None):
        """Initialize item widget."""
        self.item = item
        self.parent_name = parent_name

        """Compose the item display with markdown content."""
        # Create markdown content from item description
        markdown_content = self.item.description or f"# {
            self.item.title}\n\nNo content available."

        # Add parent information if present
        if self.parent_name:
            markdown_content += f"\n\n*Parent: {self.parent_name}*"

        super().__init__(markdown_content, classes="item-content")
        self.can_focus = True

    def on_focus(self) -> None:
        """Handle focus event."""
        self.add_class("selected")

    def on_blur(self) -> None:
        """Handle blur event."""
        self.remove_class("selected")


class ColumnWidget(Vertical):
    """Widget representing a kanban column."""

    def __init__(self, column: Column, items: List[Item], parents: Dict[str, Parent],
                 board_view: Optional['BoardView'] = None):
        """Initialize column widget."""
        self.column = column
        self.items = items
        self.parents = parents
        self.board_view = board_view
        self.editing_widget = None

        super().__init__(classes="column")
        self.border_title = f"{column.name} ({len(items)})"
        self.can_focus = True

    def compose(self):
        """Compose the column layout."""
        # Scrollable items container
        with Vertical(classes="items-container") as items_container:
            with VerticalScroll(classes="items-scroll"):
                # Items
                for item in self.items:
                    parent_name = None
                    if item.parent_id and item.parent_id in self.parents:
                        parent_name = self.parents[item.parent_id].name

                    yield ItemWidget(item, parent_name)

    def add_new_item_inline(self) -> None:
        """Add a new item inline for editing."""
        if self.editing_widget:
            return  # Already editing

        def on_save(title: str, content: str):
            # Create new item
            if self.board_view and hasattr(self.board_view.app, 'controller'):
                controller = self.board_view.app.controller
                controller.add_item(title, self.column.id, None, content)
                self.board_view.refresh_board()
                self.board_view.app.notify(f"Created item: {title}")
            self._finish_editing()

        def on_cancel():
            self._finish_editing()

        self.editing_widget = EditableItemWidget(
            is_new=True,
            on_save=on_save,
            on_cancel=on_cancel
        )

        # Add to items container
        items_container = self.query_one(".items-container", Vertical)
        items_container.mount(self.editing_widget)

    def _finish_editing(self):
        """Clean up after editing."""
        if self.editing_widget:
            self.editing_widget.remove()
            self.editing_widget = None

    def on_focus(self) -> None:
        """Handle focus event."""
        self.add_class("focused")

    def on_blur(self) -> None:
        """Handle blur event."""
        self.remove_class("focused")


class ParentGroupWidget(Vertical):
    """Widget for displaying items grouped by parent."""

    def __init__(self, parent: Parent, items: List[Item]):
        """Initialize parent group widget."""
        self.parent = parent
        self.items = items

        super().__init__(classes="parent-group")
        self.border_title = f"{parent.name} ({len(items)})"

    def compose(self):
        """Compose the parent group layout."""
        yield Static(f"📁 {self.parent.name}", classes="parent-header")

        for item in self.items:
            yield ItemWidget(item)

    def on_key(self, event) -> None:
        """Handle key presses for navigation and closing dialog."""
        # Vim-style scrolling
        scroll_container = self.query_one(VerticalScroll)
        if event.key == "j":
            scroll_container.scroll_down()
        elif event.key == "k":
            scroll_container.scroll_up()
        elif event.key == "ctrl+d":
            scroll_container.scroll_page_down()
        elif event.key == "ctrl+u":
            scroll_container.scroll_page_up()
        elif event.key == "g":
            scroll_container.scroll_home()
        elif event.key == "G":
            scroll_container.scroll_end()
        # Close dialog
        elif event.key in ("q", "enter"):
            self.dismiss()


class BoardView(Widget):
    """Main board view widget."""

    show_parents: reactive[bool] = reactive(False)

    def __init__(self):
        """Initialize board view."""
        super().__init__(classes="board-view")
        self.board: Optional[Board] = None
        self.selected_item: Optional[Item] = None

    def set_board(self, board: Board) -> None:
        """Set the board to display."""
        self.board = board
        self.refresh_board()

    def refresh_board(self) -> None:
        """Refresh the board display."""
        if not self.board:
            return

        # Clear existing content
        self.remove_children()

        if self.show_parents:
            self._render_parent_grouped_view()
        else:
            self._render_column_view()

    def _render_column_view(self) -> None:
        """Render the traditional column-based kanban view."""
        if not self.board:
            return

        # Create parent lookup
        parents = {p.id: p for p in self.board.parents}

        columns_container = Horizontal()
        self.mount(columns_container)

        for column in sorted(self.board.columns, key=lambda c: c.position):
            items = self.board.get_column_items(column.id)
            columns_container.mount(ColumnWidget(column, items, parents, self))

    def _render_parent_grouped_view(self) -> None:
        """Render the parent-grouped view."""
        if not self.board:
            return

        container = Vertical()
        self.mount(container)

        # Group items by parent
        parent_groups = {}
        orphaned_items = []

        for item in self.board.items:
            if item.parent_id:
                if item.parent_id not in parent_groups:
                    parent_groups[item.parent_id] = []
                parent_groups[item.parent_id].append(item)
            else:
                orphaned_items.append(item)

        # Display parent groups
        for parent in self.board.parents:
            if parent.id in parent_groups:
                items = parent_groups[parent.id]
                container.mount(ParentGroupWidget(parent, items))

        # Display orphaned items
        if orphaned_items:
            orphaned_parent = Parent(name="No Parent", color="gray")
            container.mount(ParentGroupWidget(orphaned_parent, orphaned_items))

    def toggle_parent_grouping(self) -> None:
        """Toggle between column and parent-grouped views."""
        self.show_parents = not self.show_parents
        self.refresh_board()

    def get_selected_item(self) -> Optional[Item]:
        """Get the currently selected item."""
        focused = self.app.focused
        if isinstance(focused, ItemWidget):
            return focused.item
        return None

    def show_new_item_dialog(self) -> None:
        """Create a new item inline in the focused column."""
        if not self.board:
            return

        # Find the currently focused column
        focused = self.app.focused
        target_column = None

        # Try to find which column we're in
        if isinstance(focused, ItemWidget):
            target_column = self._find_column_for_item(focused.item)
        elif isinstance(focused, ColumnWidget):
            target_column = focused
        else:
            # Default to first column if no specific column is focused
            columns = list(self.query(ColumnWidget))
            if columns:
                target_column = columns[0]

        if target_column:
            target_column.add_new_item_inline()
        else:
            self.app.notify("No column available for new item",
                            severity="error")

    def _find_column_for_item(self, item: Item) -> Optional[ColumnWidget]:
        """Find the column widget containing a specific item."""
        for column_widget in self.query(ColumnWidget):
            if column_widget.column.id == item.column_id:
                return column_widget
        return None

    def delete_selected_item(self) -> None:
        """Delete the currently selected item."""
        selected = self.get_selected_item()
        if not selected:
            return

        def confirm_delete() -> None:
            if hasattr(self.app, 'controller') and self.app.controller:
                controller = self.app.controller
                if controller.delete_item(selected.id):
                    self.refresh_board()
                    self.app.notify(f"Deleted item: {selected.title}")
                else:
                    self.app.notify("Failed to delete item", severity="error")

        from .dialogs import ConfirmDialog
        dialog = ConfirmDialog(
            "Delete Item",
            f"Are you sure you want to delete '{selected.title}'?",
            confirm_delete
        )
        self.app.push_screen(dialog)

    def edit_selected_item(self) -> None:
        """Edit the currently selected item inline."""
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        # Find the item widget and replace it with an editable version
        focused_widget = self.app.focused
        if not isinstance(focused_widget, ItemWidget):
            return

        # Find the column containing this item
        target_column = self._find_column_for_item(selected)
        if not target_column:
            return

        def on_save(title: str, content: str):
            if hasattr(self.app, 'controller') and self.app.controller:
                controller = self.app.controller
                controller.update_item(
                    selected.id, title=title, description=content)
                self.refresh_board()
                self.app.notify(f"Updated item: {title}")

        def on_cancel():
            self.refresh_board()  # Just refresh to restore original view

        # Replace the item widget with an editable version
        parent = focused_widget.parent
        if parent:
            # Create editable widget
            editable_widget = EditableItemWidget(
                item=selected,
                on_save=on_save,
                on_cancel=on_cancel
            )

            # Replace the focused widget
            focused_widget.remove()
            parent.mount(editable_widget)

    def show_move_item_dialog(self) -> None:
        """Show dialog for moving an item."""
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        def move_item(target_column_id: str) -> None:
            if hasattr(self.app, 'controller') and self.app.controller:
                controller = self.app.controller
                controller.move_item(selected.id, target_column_id)
                self.refresh_board()
                self.app.notify(f"Moved item: {selected.title}")

        from .dialogs import MoveItemDialog
        dialog = MoveItemDialog(self.board, selected.column_id, move_item)
        self.app.push_screen(dialog)

    def watch_show_parents(self, show_parents: bool) -> None:
        """React to show_parents changes."""
        self.refresh_board()

    # Vim-style navigation methods
    def move_focus_left(self) -> None:
        """Move focus to the left column (vim h)."""
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            return

        # Find all focusable widgets in a left-to-right order
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if not focusable:
            return

        try:
            current_idx = focusable.index(focused)
            # Find item in previous column
            current_column = self._get_column_for_item(focused.item)
            for i in range(current_idx - 1, -1, -1):
                item_column = self._get_column_for_item(focusable[i].item)
                if item_column != current_column:
                    focusable[i].focus()
                    break
        except (ValueError, AttributeError):
            pass

    def move_focus_right(self) -> None:
        """Move focus to the right column (vim l)."""
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            return

        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if not focusable:
            return

        try:
            current_idx = focusable.index(focused)
            current_column = self._get_column_for_item(focused.item)
            for i in range(current_idx + 1, len(focusable)):
                item_column = self._get_column_for_item(focusable[i].item)
                if item_column != current_column:
                    focusable[i].focus()
                    break
        except (ValueError, AttributeError):
            pass

    def move_focus_first(self) -> None:
        """Move focus to the first item (vim gg)."""
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if focusable:
            focusable[0].focus()

    def move_focus_last(self) -> None:
        """Move focus to the last item (vim G)."""
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if focusable:
            focusable[-1].focus()

    def _get_column_for_item(self, item: Item) -> Optional[str]:
        """Get the column ID for an item."""
        return item.column_id if item else None

    def scroll_down(self) -> None:
        """Scroll down in the current view."""
        if self.show_parents:
            # For parent view, scroll the main container
            container = self.query_one(Vertical)
            if hasattr(container, 'scroll_down'):
                container.scroll_down()
        else:
            # For column view, scroll the focused column or first available column
            focused = self.app.focused
            target_scroll = None

            # Try to find scroll container from focused widget
            if isinstance(focused, ItemWidget):
                # Find the column containing this item
                column_widget = self._find_column_for_item(focused.item)
                if column_widget:
                    target_scroll = column_widget.query_one(VerticalScroll)

            # If no specific column found, use first column
            if not target_scroll:
                columns = list(self.query(ColumnWidget))
                if columns:
                    target_scroll = columns[0].query_one(VerticalScroll)

            if target_scroll:
                target_scroll.scroll_page_down()

    def scroll_up(self) -> None:
        """Scroll up in the current view."""
        if self.show_parents:
            # For parent view, scroll the main container
            container = self.query_one(Vertical)
            if hasattr(container, 'scroll_up'):
                container.scroll_up()
        else:
            # For column view, scroll the focused column or first available column
            focused = self.app.focused
            target_scroll = None

            # Try to find scroll container from focused widget
            if isinstance(focused, ItemWidget):
                # Find the column containing this item
                column_widget = self._find_column_for_item(focused.item)
                if column_widget:
                    target_scroll = column_widget.query_one(VerticalScroll)

            # If no specific column found, use first column
            if not target_scroll:
                columns = list(self.query(ColumnWidget))
                if columns:
                    target_scroll = columns[0].query_one(VerticalScroll)

            if target_scroll:
                target_scroll.scroll_page_up()

    def column_scroll_down(self) -> None:
        """Scroll focused column down."""
        focused = self.app.focused
        target_scroll = None

        if isinstance(focused, ItemWidget):
            # Find the column containing this item
            column_widget = self._find_column_for_item(focused.item)
            if column_widget:
                target_scroll = column_widget.query_one(VerticalScroll)
        elif isinstance(focused, ColumnWidget):
            target_scroll = focused.query_one(VerticalScroll)

        if not target_scroll:
            # Default to first column
            columns = list(self.query(ColumnWidget))
            if columns:
                target_scroll = columns[0].query_one(VerticalScroll)

        if target_scroll:
            target_scroll.scroll_down()

    def column_scroll_up(self) -> None:
        """Scroll focused column up."""
        focused = self.app.focused
        target_scroll = None

        if isinstance(focused, ItemWidget):
            # Find the column containing this item
            column_widget = self._find_column_for_item(focused.item)
            if column_widget:
                target_scroll = column_widget.query_one(VerticalScroll)
        elif isinstance(focused, ColumnWidget):
            target_scroll = focused.query_one(VerticalScroll)

        if not target_scroll:
            # Default to first column
            columns = list(self.query(ColumnWidget))
            if columns:
                target_scroll = columns[0].query_one(VerticalScroll)

        if target_scroll:
            target_scroll.scroll_up()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard events."""
        # Let normal j/k navigation work, scrolling is handled by Shift+j/k
        pass

    def show_help_dialog(self) -> None:
        """Show help dialog with all keybindings."""
        help_text = """
# MKanban - Vim Keybindings

## Navigation
- j/Down    : Move down (navigate items)
- k/Up      : Move up (navigate items)
- h         : Move left (previous column)
- l         : Move right (next column)
- gg        : Go to first item
- G         : Go to last item

## Scrolling
- Shift+J   : Scroll column down
- Shift+K   : Scroll column up  
- Ctrl+D    : Scroll down (page)
- Ctrl+U    : Scroll up (page)

## Item Operations
- o         : Create new item (inline markdown editor)
- i         : Edit item (inline markdown editor)
- dd        : Delete item
- m         : Move item to different column

## Text Editing (Vim Motions)
### Normal Mode
- i         : Insert mode at cursor
- I         : Insert mode at line start
- a         : Insert mode after cursor
- A         : Insert mode at line end
- o         : New line below and insert
- O         : New line above and insert
- h/j/k/l   : Navigate cursor
- w         : Next word
- b         : Previous word
- 0         : Beginning of line
- $         : End of line
- gg        : First line
- G         : Last line
- x         : Delete character
- X         : Delete char before cursor
- dd        : Delete line
- v         : Visual mode
- Escape    : Return to normal mode

### Insert Mode
- Escape    : Return to normal mode
- Normal typing works

### Visual Mode
- h/j/k/l   : Extend selection
- d/x       : Delete selection
- Escape    : Return to normal mode

## Dialog Navigation (Vim Style)
- j/k       : Navigate between fields
- i         : Enter insert mode for current field
- Enter     : Confirm action
- Escape    : Cancel/Exit

## Inline Editing
- Ctrl+S    : Save item while editing
- Escape    : Cancel editing (from normal mode)
- # Title   : First # line becomes item title

## View Operations  
- p         : Toggle parent grouping
- w         : Save board
- r         : Refresh view

## Other
- g?        : Show this help
- q/Escape  : Quit
- Ctrl+C    : Force quit"""

        from .dialogs import HelpDialog
        dialog = HelpDialog(help_text)
        self.app.push_screen(dialog)
