
from typing import Optional, List, Dict
from enum import Enum
from textual.widgets import Static, Markdown
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.reactive import reactive

from ..models import Board, Column, Item, Parent
from .vim_widgets import VimTextArea


class RefreshType(Enum):
    FULL = "full"
    ITEMS = "items"
    COLUMNS = "columns"
    LAYOUT = "layout"


class EditableItemWidget(Vertical):
    def __init__(self, item: Optional[Item] = None, parent_name: Optional[str] = None,
                 is_new: bool = False, on_save: Optional[callable] = None,
                 on_cancel: Optional[callable] = None):
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
        editor = self.query_one("#item_editor", VimTextArea)
        editor.focus()

    def save_item(self) -> None:
        editor = self.query_one("#item_editor", VimTextArea)
        content = editor.text.strip()

        if not content:
            return

        lines = content.split('\n')
        title = "Untitled"
        for line in lines:
            if line.strip().startswith('# '):
                title = line.strip()[2:].strip()
                break

        if self.on_save:
            self.on_save(title, content)

    def cancel_edit(self) -> None:
        if self.on_cancel:
            self.on_cancel()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.save_item()
            event.prevent_default()


class ItemWidget(Vertical):

    def __init__(self, item: Item, parent_name: Optional[str] = None):
        self.item = item
        self.parent_name = parent_name
        super().__init__(classes="item", id=f"item_{
            item.id.replace("-", "_")}")
        self.can_focus = True

    def compose(self):
        yield MarkDown(self.item)

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")


class MarkDown(Markdown):

    def __init__(self, item: Item, parent_name: Optional[str] = None):
        self.item = item
        self.parent_name = parent_name

        markdown_content = self.item.description or f"# {
            self.item.title}\n\nNo content available."

        if self.parent_name:
            markdown_content += f"\n\n*Parent: {self.parent_name}*"

        super().__init__(markdown_content, classes="item-content")
        self.can_focus = True

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")


class ColumnWidget(Vertical):

    def __init__(self, column: Column, items: List[Item],
                 board_view: Optional['BoardView'] = None):
        self.column = column
        self.items = items
        self.board_view = board_view
        self.editing_widget = None

        super().__init__(classes="column", id=f"column_{
            column.id.replace("-", "_")}")
        self.border_title = f"{column.name} ({len(items)})"
        self.can_focus = True

    def compose(self):
        with Vertical(classes="items-container") as items_container:
            with VerticalScroll(classes="items-scroll"):
                for item in self.items:
                    yield ItemWidget(item)

    def add_new_item_inline(self) -> None:
        if self.editing_widget:
            return

        def on_save(title: str, content: str):
            if self.board_view and hasattr(self.board_view.app, 'controller'):
                controller = self.board_view.app.controller
                controller.add_item(title, self.column.id, None, content)
                self.board_view.refresh_board()
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
        if self.editing_widget:
            self.editing_widget.remove()
            self.editing_widget = None

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")


class BoardView(Widget):
    show_parents: reactive[bool] = reactive(False)

    def __init__(self):
        super().__init__(classes="board-view")
        self.board: Optional[Board] = None
        self.selected_item: Optional[Item] = None

    def set_board(self, board: Board) -> None:
        self.board = board
        self.refresh_board()

    def refresh_board(self, focus_item_id: Optional[str] = None,
                      refresh_type: RefreshType = RefreshType.FULL) -> None:
        if not self.board:
            return

        if refresh_type == RefreshType.FULL:
            self._full_refresh()
        elif refresh_type == RefreshType.ITEMS:
            self._refresh_items_only()
        elif refresh_type == RefreshType.COLUMNS:
            self._refresh_columns_only()
        elif refresh_type == RefreshType.LAYOUT:
            self._refresh_layout_only()

        # Schedule focus restoration after rendering
        if focus_item_id:
            self.call_after_refresh(self._restore_focus_to_item, focus_item_id)

    def _full_refresh(self) -> None:
        self.remove_children()

        if self.show_parents:
            self._render_parent_grouped_view()
        else:
            self._render_column_view()

    def _refresh_items_only(self) -> None:
        if not self.board:
            return

        for item_widget in self.query(ItemWidget):
            updated_item = None
            for item in self.board.items:
                if item.id == item_widget.item.id:
                    updated_item = item
                    break

            if updated_item:
                item_widget.item = updated_item
                markdown_widget = item_widget.query_one(MarkDown)
                if markdown_widget:
                    parent_name = None
                    if updated_item.parent_id:
                        parent = next(
                            (p for p in self.board.columns[0].parents if p.id == updated_item.parent_id), None)
                        if parent:
                            parent_name = parent.name

                    markdown_content = updated_item.description or f"# {
                        updated_item.title}\n\nNo content available."
                    if parent_name:
                        markdown_content += f"\n\n*Parent: {parent_name}*"

                    markdown_widget.update(markdown_content)

    def _refresh_columns_only(self) -> None:
        if not self.board:
            return

        for column_widget in self.query(ColumnWidget):
            updated_column = None
            for column in self.board.columns:
                if column.id == column_widget.column.id:
                    updated_column = column
                    break

            if updated_column:
                column_widget.column = updated_column
                items = self.board.get_column_by_id(
                    updated_column.id).get_column_items(updated_column.id)
                column_widget.items = items
                column_widget.border_title = f"{
                    updated_column.name} ({len(items)})"

    def _refresh_layout_only(self) -> None:
        pass

    def _render_column_view(self) -> None:
        if not self.board:
            return

        columns_container = Horizontal()
        self.mount(columns_container)

        for column in sorted(self.board.columns, key=lambda c: c.position):
            items = self.board.get_column_by_id(
                column.id).get_column_items(column.id)
            columns_container.mount(ColumnWidget(column, items, self))

    def _render_parent_grouped_view(self) -> None:
        """Render the parent-grouped view."""
        if not self.board:
            return

        container = Vertical()
        self.mount(container)

        parent_groups = {}
        orphaned_items = []

        for item in self.board.items:
            if item.parent_id:
                if item.parent_id not in parent_groups:
                    parent_groups[item.parent_id] = []
                parent_groups[item.parent_id].append(item)
            else:
                orphaned_items.append(item)

    def toggle_parent_grouping(self) -> None:
        """Toggle between column and parent-grouped views."""
        self.show_parents = not self.show_parents
        self.refresh_board(refresh_type=RefreshType.FULL)

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

        focused = self.app.focused
        target_column = None

        if isinstance(focused, ItemWidget):
            target_column = self._find_column_for_item(focused.item)
        elif isinstance(focused, ColumnWidget):
            target_column = focused
        else:
            columns = list(self.query(ColumnWidget))
            if columns:
                target_column = columns[0]

        if target_column:
            target_column.add_new_item_inline()
        else:
            self.app.notify("No column available for new item",
                            severity="error")

    def _find_column_for_item(self, item: Item) -> Optional[ColumnWidget]:
        for column_widget in self.query(ColumnWidget):
            if column_widget.column.id == item.column_id:
                return column_widget
        return None

    def delete_selected_item(self) -> None:
        selected = self.get_selected_item()
        if not selected:
            return

        if hasattr(self.app, 'controller') and self.app.controller:
            controller = self.app.controller
            if controller.delete_item(selected.id):
                self.refresh_board()

    def edit_selected_item(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        focused_widget = self.app.focused
        if not isinstance(focused_widget, ItemWidget):
            return

        target_column = self._find_column_for_item(selected)
        if not target_column:
            return

        def on_save(title: str, content: str):
            if hasattr(self.app, 'controller') and self.app.controller:
                controller = self.app.controller
                controller.update_item(
                    selected.id, title=title, description=content)
                self.refresh_board()

        def on_cancel():
            self.refresh_board()

        parent = focused_widget.parent
        if parent:
            editable_widget = EditableItemWidget(
                item=selected,
                on_save=on_save,
                on_cancel=on_cancel
            )

            focused_widget.remove()
            parent.mount(editable_widget)

    async def move_right(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        async def move_item(target_column_id: str) -> None:
            if hasattr(self.app, 'controller') and self.app.controller:
                items_container = self.query_one(
                    f"#column_{target_column_id.replace("-", "_")}", Vertical)

                item = self.query_one(f"#item_{selected.id.replace("-", "_")}")

                await item.remove()
                items_container.children[0].children[0].mount(item)
                items_container.items.append(item)
                item.focus()

                controller = self.app.controller
                controller.move_item(selected.id, target_column_id)

        column = None

        for index, value in enumerate(self.board.columns):
            if value.id == selected.column_id:
                if index == len(self.board.columns) - 1:
                    return
                column = self.board.columns[index + 1]
                await move_item(column.id)
                return

    async def move_left(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        async def move_item(target_column_id: str) -> None:
            if hasattr(self.app, 'controller') and self.app.controller:
                items_container = self.query_one(
                    f"#column_{target_column_id.replace("-", "_")}", Vertical)

                item = self.query_one(f"#item_{selected.id.replace("-", "_")}")
                await item.remove()
                items_container.children[0].children[0].mount(item)

                controller = self.app.controller
                controller.move_item(selected.id, target_column_id)

                item.focus()

        column = None

        for index, value in enumerate(self.board.columns):
            if value.id == selected.column_id:
                if index == 0:
                    return
                column = self.board.columns[index - 1]
                await move_item(column.id)
                return

    def move_focus_up(self) -> None:
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            # Try to focus first item if nothing is focused
            all_items = self.query(".item")
            focusable = [w for w in all_items if hasattr(
                w, 'can_focus') and w.can_focus]
            if focusable:
                focusable[0].focus()
                self._ensure_item_visible(focusable[0])
            return

        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if not focusable:
            return

        try:
            current_idx = focusable.index(focused)
            if current_idx > 0:
                next_item = focusable[current_idx - 1]
                next_item.focus()
                self._ensure_item_visible(next_item)
        except (ValueError, AttributeError):
            pass

    def move_focus_down(self) -> None:
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            all_items = self.query(".item")
            focusable = [w for w in all_items if hasattr(
                w, 'can_focus') and w.can_focus]
            if focusable:
                focusable[0].focus()
                self._ensure_item_visible(focusable[0])
            return

        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if not focusable:
            return

        try:
            current_idx = focusable.index(focused)
            if current_idx < len(focusable) - 1:
                next_item = focusable[current_idx + 1]
                next_item.focus()
                self._ensure_item_visible(next_item)
        except (ValueError, AttributeError):
            pass

    def move_focus_left(self) -> None:
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
            for i in range(current_idx - 1, -1, -1):
                item_column = self._get_column_for_item(focusable[i].item)
                if item_column != current_column:
                    focusable[i].focus()
                    self._ensure_item_visible(focusable[i])
                    break
        except (ValueError, AttributeError):
            pass

    def move_focus_right(self) -> None:
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
                    self._ensure_item_visible(focusable[i])
                    break
        except (ValueError, AttributeError):
            pass

    def move_focus_first(self) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if focusable:
            focusable[0].focus()
            self._ensure_item_visible(focusable[0])

    def move_focus_last(self) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]
        if focusable:
            focusable[-1].focus()
            self._ensure_item_visible(focusable[-1])

    def _ensure_item_visible(self, item_widget: ItemWidget) -> None:
        if not item_widget:
            return

        scroll_containers = []

        for value in item_widget.ancestors:
            for clss in value.classes:
                if clss == "items-scroll":
                    scroll_containers.append(value)

        if not scroll_containers:
            return

        scroll_view = scroll_containers[0]

        if not hasattr(scroll_view, 'scroll_to_widget'):
            return

        # Scroll to make the item visible
        try:
            scroll_view.scroll_to_widget(item_widget, animate=False)
        except Exception:
            try:
                item_region = item_widget.region
                scroll_view.scroll_to_region(item_region, animate=False)
            except Exception:
                pass

    def _get_column_for_item(self, item: Item) -> Optional[str]:
        return item.column_id if item else None

    def call_after_refresh(self, callback, *args) -> None:
        self.set_timer(0.01, lambda: callback(*args))

    def _restore_focus_to_item(self, item_id: str) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(
            w, 'can_focus') and w.can_focus]

        for widget in focusable:
            if hasattr(widget, 'item') and widget.item.id == item_id:
                widget.focus()
                self._ensure_item_visible(widget)
                break

    def show_help_dialog(self) -> None:
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
