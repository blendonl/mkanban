from typing import Optional
from pathlib import Path
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from ...models.board import Board
from ...models.item import Item
from ..refresh_type import RefreshType
from .markdown_widget import MarkDownWidget
from .item_widget import ItemWidget
from .column_widget import ColumnWidget
from .editable_item_widget import EditableItemWidget
from ...controllers.column_controller import ColumnController

from ..dialogs.help_dialog import HelpDialog


class BoardWidget(Widget):
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
            for column in self.board.columns:
                for item in column.items:
                    if item.id == item_widget.item.id:
                        updated_item = item
                        break
                if updated_item:
                    break

            if updated_item:
                item_widget.item = updated_item
                markdown_widget = item_widget.query_one(MarkDownWidget)
                if markdown_widget:
                    parent_name = None
                    if updated_item.parent_id:
                        parent = next(
                            (p for p in self.board.columns[0].parents if p.id == updated_item.parent_id), None)
                        if parent:
                            parent_name = parent.name

                    markdown_content = updated_item.title
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
            columns_container.mount(ColumnWidget(
                column, items, ColumnController(
                    self.board,
                    column,
                    self.app.storage
                )
            ))

    def _render_parent_grouped_view(self) -> None:
        if not self.board:
            return

        container = Vertical()
        self.mount(container)

        parent_groups = {}
        orphaned_items = []

        for column in self.board.columns:
            for item in column.items:
                if item.parent_id:
                    if item.parent_id not in parent_groups:
                        parent_groups[item.parent_id] = []
                    parent_groups[item.parent_id].append(item)
                else:
                    orphaned_items.append(item)

    def toggle_parent_grouping(self) -> None:
        self.show_parents = not self.show_parents
        self.refresh_board(refresh_type=RefreshType.FULL)

    def get_selected_item(self) -> Optional[Item]:
        focused = self.app.focused
        if isinstance(focused, ItemWidget):
            return focused.item
        return None

    def show_new_item_dialog(self) -> None:
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

        column = self.board.get_column_by_id(selected.column_id)
        column_controller = ColumnController(
            self.board, column, self.app.storage)
        if column_controller.delete_item(selected):
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

        # Get the item file path
        item_file_path = self._get_item_file_path(selected)
        if not item_file_path or not item_file_path.exists():
            self.app.notify("Item file not found", severity="error")
            return

        # Suspend the app and open Neovim
        import subprocess
        import os
        
        try:
            with self.app.suspend():
                result = subprocess.run(['nvim', str(item_file_path)], 
                                      check=True, 
                                      env=os.environ.copy())
            
            # App automatically resumes here
            # Refresh the board after editing
            self.refresh_board()
            
        except subprocess.CalledProcessError:
            self.app.notify("Error opening Neovim", severity="error")
        except FileNotFoundError:
            self.app.notify("Neovim not found. Please install nvim", severity="error")

    async def move_right(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        async def move_item(target_column_id: str) -> None:
            items_container = self.query_one(
                f"#column_{target_column_id.replace("-", "_")}", Vertical)

            item = self.query_one(f"#item_{selected.id.replace("-", "_")}")

            await item.remove()
            items_container.children[0].children[0].mount(item)
            items_container.items.append(item)
            item.focus()

            controller = items_container.column_controller
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
            items_container = self.query_one(
                f"#column_{target_column_id.replace("-", "_")}", Vertical)

            item = self.query_one(f"#item_{selected.id.replace("-", "_")}")
            await item.remove()
            items_container.children[0].children[0].mount(item)

            controller = items_container.column_controller
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

    def _get_item_file_path(self, item: Item) -> Optional[Path]:
        """Get the file path for an item"""
        if not item or not self.board:
            return None
        
        # Find the column containing this item
        column = None
        for col in self.board.columns:
            if col.id == item.column_id:
                column = col
                break
        
        if not column:
            return None
        
        # Get the storage instance to access paths
        storage = self.app.storage
        board_dir = storage._get_board_directory(self.board)
        column_safe_name = storage._get_safe_name(column.name)
        
        item_file_path = board_dir / column_safe_name / "items" / f"{item.id}.md"
        return item_file_path

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
        dialog = HelpDialog()
        self.app.push_screen(dialog)
