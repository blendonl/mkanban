from typing import Optional
from pathlib import Path
import subprocess
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from src.core.exceptions import ValidationError
from src.domain.entities.board import Board
from src.domain.entities.item import Item
from src.core.types import RefreshType
from src.core.constants import (
    BOARD_WIDGET_DEFAULT_COLUMN_WIDTH,
    BOARD_WIDGET_MIN_COLUMN_WIDTH,
    BOARD_WIDGET_MAX_COLUMN_WIDTH,
    BOARD_WIDGET_COMPACT_MIN_WIDTH,
)
from src.ui.widgets.markdown_widget import MarkDownWidget
from src.ui.widgets.item_widget import ItemWidget
from src.ui.widgets.column_widget import ColumnWidget
from src.core.dependency_container import create_column_controller
from src.utils.editor_utils import open_editor_for_app

from src.ui.dialogs.help_dialog import HelpDialog
from src.ui.dialogs.column_settings_dialog import ColumnSettingsDialog


class BoardWidget(Widget):
    show_parents: reactive[bool] = reactive(False)

    def __init__(self):
        super().__init__(classes="board-view")
        self.board: Optional[Board] = None
        self.selected_item: Optional[Item] = None
        self._current_column_width = BOARD_WIDGET_DEFAULT_COLUMN_WIDTH

    def set_board(self, board: Board) -> None:
        self.board = board
        self.refresh_board()

    def refresh_board(
        self,
        focus_item_id: Optional[str] = None,
        refresh_type: RefreshType = RefreshType.FULL,
    ) -> None:
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
                            (
                                p
                                for p in self.board.columns[0].parents
                                if p.id == updated_item.parent_id
                            ),
                            None,
                        )
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
                items = self.board.get_column_by_id(updated_column.id).get_all_items()
                column_widget.items = items
                column_widget.update_title()

    def _refresh_layout_only(self) -> None:
        pass

    def _render_column_view(self) -> None:
        if not self.board:
            return

        columns_container = Horizontal()
        self.mount(columns_container)

        for column in sorted(self.board.columns, key=lambda c: (c.position, c.name)):
            items = self.board.get_column_by_id(column.id).get_all_items()
            column_widget = ColumnWidget(
                column,
                items,
                create_column_controller(self.board, column),
            )
            columns_container.mount(column_widget)

        # Apply responsive layout after mounting
        self.call_after_refresh(self.update_responsive_layout)

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
            # Use the first column by position (lowest position number)
            first_column = self.board.get_first_column()
            if first_column:
                columns = list(self.query(ColumnWidget))
                target_column = next(
                    (col for col in columns if col.column.id == first_column.id),
                    columns[0] if columns else None,
                )

        if target_column:
            target_column.add_new_item_inline()
        else:
            self.app.notify("No column available for new item", severity="error")

    def _find_column_for_item(self, item: Item) -> Optional[ColumnWidget]:
        for column_widget in self.query(ColumnWidget):
            if item in column_widget.column.items:
                return column_widget
        return None

    def delete_selected_item(self) -> None:
        selected = self.get_selected_item()
        if not selected:
            return

        column_widget = self._find_column_for_item(selected)
        column = column_widget.column if column_widget else None
        column_controller = create_column_controller(self.board, column)
        if column_controller.delete_item(selected):
            self.refresh_board()

    def create_new_item_with_editor(self) -> None:
        if not self.board:
            return

        focused = self.app.focused
        target_column = None

        if isinstance(focused, ItemWidget):
            target_column = self._find_column_for_item(focused.item)
        elif isinstance(focused, ColumnWidget):
            target_column = focused
        else:
            # Use the first column by position (lowest position number)
            first_column = self.board.get_first_column()
            if first_column:
                columns = list(self.query(ColumnWidget))
                target_column = next(
                    (col for col in columns if col.column.id == first_column.id),
                    columns[0] if columns else None,
                )

        if not target_column:
            self.app.notify("No column available for new item", severity="error")
            return

        from ...domain.entities.item import Item
        import tempfile

        # Create a new item template
        item = Item(title="New Task", column_id=target_column.column.id)
        template_content = f"""--- 
id: {item.id}
parent_id: null
title: {item.id} 
created_at: {item.created_at}
updated_at: {item.updated_at}
---

# 
"""

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as temp_file:
                temp_file.write(template_content)
                temp_file_path = temp_file.name

            open_editor_for_app(temp_file_path, self.app)

            # Read the edited content
            with open(temp_file_path, "r") as f:
                edited_content = f.read()

            # Extract title from the content
            title_line = next(
                (
                    line
                    for line in edited_content.split("\n")
                    if line.strip().startswith("# ")
                ),
                None,
            )
            title = title_line.replace("# ", "").strip() if title_line else "New Item"

            if not title or title == "New Item":
                self.app.notify(
                    "No title specified. Item creation cancelled.", severity="warning"
                )
                return

            try:
                # Create the new item
                new_item = target_column.column.add_item(title)
                new_item.description = edited_content.strip()

                # Save the board
                self.app.board_service.save_board(self.board)

                # Refresh the board and focus the new item
                self.refresh_board(focus_item_id=new_item.id)
            except ValidationError as e:
                self.app.notify(str(e), severity="error")
                return

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Error messages already handled in open_editor_for_app
        except Exception as e:
            self.app.notify(f"Error creating item: {e}", severity="error")
        finally:
            try:
                Path(temp_file_path).unlink()
            except Exception:
                pass

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

        item_file_path = self._get_item_file_path(selected)
        if not item_file_path or not item_file_path.exists():
            self.app.notify("Item file not found", severity="error")
            return

        try:
            # Store the original item ID for focus restoration
            original_item_id = selected.id

            open_editor_for_app(str(item_file_path), self.app)

            # After editing, reload the item from file to get updated title
            self._update_item_from_file(selected, item_file_path)

            # Save the board to trigger filename update and persist changes
            self.app.board_service.save_board(self.board)

            # Refresh the board to reflect all changes
            self.refresh_board(focus_item_id=original_item_id)

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Error messages already handled in open_editor_for_app

    async def move_right(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        for index, value in enumerate(self.board.columns):
            if value.id == selected.column_id:
                if index == len(self.board.columns) - 1:
                    return
                target_column = self.board.columns[index + 1]

                column_widget = self._find_column_for_item(selected)
                column_controller = create_column_controller(
                    self.board, column_widget.column
                )

                try:
                    if column_controller.move_item(selected.id, target_column.id):
                        self.refresh_board(focus_item_id=selected.id)
                except ValidationError as e:
                    self.app.notify(str(e), severity="error")
                return

    async def move_left(self) -> None:
        selected = self.get_selected_item()
        if not selected or not self.board:
            return

        for index, value in enumerate(self.board.columns):
            if value.id == selected.column_id:
                if index == 0:
                    return
                target_column = self.board.columns[index - 1]

                column_widget = self._find_column_for_item(selected)
                column_controller = create_column_controller(
                    self.board, column_widget.column
                )

                try:
                    if column_controller.move_item(selected.id, target_column.id):
                        self.refresh_board(focus_item_id=selected.id)
                except ValidationError as e:
                    self.app.notify(str(e), severity="error")
                return

    def move_focus_up(self) -> None:
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            all_items = self.query(".item")
            focusable = [
                w for w in all_items if hasattr(w, "can_focus") and w.can_focus
            ]
            if focusable:
                focusable[0].focus()
                self._ensure_item_visible(focusable[0])
            return

        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(w, "can_focus") and w.can_focus]
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
            focusable = [
                w for w in all_items if hasattr(w, "can_focus") and w.can_focus
            ]
            if focusable:
                focusable[0].focus()
                self._ensure_item_visible(focusable[0])
            return

        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(w, "can_focus") and w.can_focus]
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

        current_column = self._get_column_for_item(focused.item)
        if not current_column:
            return

        # Get the current item's position within its column
        current_position = self._get_item_position_in_column(focused.item)
        if current_position is None:
            return

        # Find the target column (previous non-empty column)
        target_column_id = self._get_previous_non_empty_column_id(current_column)
        if not target_column_id:
            return

        # Get items in the target column and try to focus the item at the same position
        target_item = self._get_item_at_position_in_column(
            target_column_id, current_position
        )
        if target_item:
            target_item.focus()
            self._ensure_item_visible(target_item)

    def move_focus_right(self) -> None:
        focused = self.app.focused
        if not isinstance(focused, ItemWidget):
            return

        current_column = self._get_column_for_item(focused.item)
        if not current_column:
            return

        # Get the current item's position within its column
        current_position = self._get_item_position_in_column(focused.item)
        if current_position is None:
            return

        # Find the target column (next non-empty column)
        target_column_id = self._get_next_non_empty_column_id(current_column)
        if not target_column_id:
            return

        # Get items in the target column and try to focus the item at the same position
        target_item = self._get_item_at_position_in_column(
            target_column_id, current_position
        )
        if target_item:
            target_item.focus()
            self._ensure_item_visible(target_item)

    def move_focus_first(self) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(w, "can_focus") and w.can_focus]
        if focusable:
            focusable[0].focus()
            self._ensure_item_visible(focusable[0])

    def move_focus_last(self) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(w, "can_focus") and w.can_focus]
        if focusable:
            focusable[-1].focus()
            self._ensure_item_visible(focusable[-1])

    def _get_item_position_in_column(self, item: Item) -> Optional[int]:
        """Get the position (index) of an item within its column"""
        if not item or not self.board:
            return None

        column_widget = self._find_column_for_item(item)
        if column_widget:
            item_widgets = column_widget.query(ItemWidget)
            for i, item_widget in enumerate(item_widgets):
                if item_widget.item.id == item.id:
                    return i
        return None

    def _get_previous_column_id(self, current_column_id: str) -> Optional[str]:
        """Get the ID of the column to the left of the current column"""
        if not self.board:
            return None

        sorted_columns = sorted(self.board.columns, key=lambda c: (c.position, c.name))
        for i, column in enumerate(sorted_columns):
            if column.id == current_column_id and i > 0:
                return sorted_columns[i - 1].id
        return None

    def _get_next_column_id(self, current_column_id: str) -> Optional[str]:
        """Get the ID of the column to the right of the current column"""
        if not self.board:
            return None

        sorted_columns = sorted(self.board.columns, key=lambda c: (c.position, c.name))
        for i, column in enumerate(sorted_columns):
            if column.id == current_column_id and i < len(sorted_columns) - 1:
                return sorted_columns[i + 1].id
        return None

    def _get_item_at_position_in_column(
        self, column_id: str, position: int
    ) -> Optional[ItemWidget]:
        """Get the item widget at a specific position in a column"""
        column_widgets = self.query(ColumnWidget)
        for column_widget in column_widgets:
            if column_widget.column.id == column_id:
                item_widgets = list(column_widget.query(ItemWidget))
                # If the position exists in the target column, use it
                if position < len(item_widgets):
                    return item_widgets[position]
                # If the target column has fewer items, focus the last item
                elif item_widgets:
                    return item_widgets[-1]
        return None

    def _get_previous_non_empty_column_id(
        self, current_column_id: str
    ) -> Optional[str]:
        """Get the ID of the previous column that has items, skipping empty columns"""
        if not self.board:
            return None

        sorted_columns = sorted(self.board.columns, key=lambda c: (c.position, c.name))
        current_index = None

        # Find current column index
        for i, column in enumerate(sorted_columns):
            if column.id == current_column_id:
                current_index = i
                break

        if current_index is None:
            return None

        # Look backwards for a non-empty column
        for i in range(current_index - 1, -1, -1):
            column = sorted_columns[i]
            if self._column_has_items(column.id):
                return column.id

        return None

    def _get_next_non_empty_column_id(self, current_column_id: str) -> Optional[str]:
        """Get the ID of the next column that has items, skipping empty columns"""
        if not self.board:
            return None

        sorted_columns = sorted(self.board.columns, key=lambda c: (c.position, c.name))
        current_index = None

        # Find current column index
        for i, column in enumerate(sorted_columns):
            if column.id == current_column_id:
                current_index = i
                break

        if current_index is None:
            return None

        # Look forwards for a non-empty column
        for i in range(current_index + 1, len(sorted_columns)):
            column = sorted_columns[i]
            if self._column_has_items(column.id):
                return column.id

        return None

    def _column_has_items(self, column_id: str) -> bool:
        """Check if a column has any items"""
        column_widgets = self.query(ColumnWidget)
        for column_widget in column_widgets:
            if column_widget.column.id == column_id:
                item_widgets = list(column_widget.query(ItemWidget))
                return len(item_widgets) > 0
        return False

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

        if not hasattr(scroll_view, "scroll_to_widget"):
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
        column_widget = self._find_column_for_item(item)
        return column_widget.column.id if column_widget else None

    def _get_item_file_path(self, item: Item) -> Optional[Path]:
        """Get the file path for an item"""
        if not item or not self.board:
            return None

        # Find the column containing this item
        column_widget = self._find_column_for_item(item)
        if not column_widget:
            return None

        column = column_widget.column

        # Get the item file path using file operations
        from src.infrastructure.storage.file_operations import (
            find_item_file_by_id
        )
        from src.core.dependency_container import get_container

        from src.utils.path_resolver import PathResolver

        container = get_container()
        path_resolver = container.get(PathResolver)
        column_dir = path_resolver.get_column_directory(
            self.board.name, column.name
        )
        item_file_path = find_item_file_by_id(column_dir, item.id)
        return item_file_path

    def _update_item_from_file(self, item: Item, item_file_path: Path) -> None:
        """Update an item's properties by re-reading from its file"""
        if not item_file_path.exists():
            return

        # Load the updated item from the file
        from src.infrastructure.storage.markdown_parser import (
            parse_item_metadata
        )

        try:
            content_title, content, metadata = parse_item_metadata(
                item_file_path
            )
            # Update the existing item's properties
            item.title = content_title
            item.description = content
            item.updated_at = metadata.get(
                'updated_at', item.updated_at
            )
            item.parent_id = metadata.get(
                'parent_id', item.parent_id
            )
        except Exception:
            # If parsing fails, keep existing item data
            pass

    def call_after_refresh(self, callback, *args) -> None:
        self.set_timer(0.01, lambda: callback(*args))

    def _restore_focus_to_item(self, item_id: str) -> None:
        all_items = self.query(".item")
        focusable = [w for w in all_items if hasattr(w, "can_focus") and w.can_focus]

        for widget in focusable:
            if hasattr(widget, "item") and widget.item.id == item_id:
                widget.focus()
                self._ensure_item_visible(widget)
                break

    def show_help_dialog(self) -> None:
        dialog = HelpDialog()
        self.app.push_screen(dialog)

    def show_column_settings_dialog(self) -> None:
        if not self.board:
            return

        focused = self.app.focused
        target_column = None

        # Determine which column to configure
        if isinstance(focused, ItemWidget):
            target_column = self._find_column_for_item(focused.item)
        elif isinstance(focused, ColumnWidget):
            target_column = focused
        else:
            # Use the first column as default
            columns = list(self.query(ColumnWidget))
            target_column = columns[0] if columns else None

        if not target_column:
            self.app.notify("No column selected", severity="error")
            return

        def on_save(limit: Optional[int]):
            target_column.column.limit = limit
            target_column.column.update()
            target_column.update_title()
            self.app.board_service.save_board(self.board)
            self.app.notify(f"Column limit updated for '{target_column.column.name}'")

        dialog = ColumnSettingsDialog(target_column.column, on_save)
        self.app.push_screen(dialog)

    def update_responsive_layout(self) -> None:
        if not self.board:
            return

        terminal_width = getattr(self.app, "terminal_width", 80)
        terminal_height = getattr(self.app, "terminal_height", 24)

        num_columns = len(self.board.columns)
        if num_columns == 0:
            return

        # Handle very small terminals by switching to vertical layout
        if terminal_width < 60 and num_columns > 2:
            self._switch_to_compact_layout()
            return

        # Calculate responsive column width
        available_width = terminal_width - 6  # Account for padding and margins
        column_width = max(BOARD_WIDGET_MIN_COLUMN_WIDTH, min(BOARD_WIDGET_MAX_COLUMN_WIDTH, available_width // num_columns))

        # Ensure minimum usable width
        if column_width < BOARD_WIDGET_MIN_COLUMN_WIDTH and num_columns > 1:
            column_width = max(BOARD_WIDGET_COMPACT_MIN_WIDTH, available_width // min(num_columns, 3))

        # Update column widths if changed
        if column_width != self._current_column_width:
            self._current_column_width = column_width
            self._update_column_styles(column_width)

        # Calculate responsive item heights based on terminal height
        available_height = terminal_height - 8  # Account for headers, borders, footer
        max_items_per_column = max(1, available_height // 4)  # 4 lines per item minimum
        item_height = max(3, min(12, available_height // max(max_items_per_column, 3)))

        self._update_item_styles(item_height)

    def _switch_to_compact_layout(self) -> None:
        # For very narrow terminals, make columns stack or show fewer at once
        for i, column_widget in enumerate(self.query(ColumnWidget)):
            if i < 2:  # Show only first 2 columns
                column_widget.display = True
                column_widget.styles.min_width = 15
                column_widget.styles.max_width = 25
            else:
                column_widget.display = False

    def _update_column_styles(self, width: int) -> None:
        for column_widget in self.query(ColumnWidget):
            column_widget.styles.min_width = width
            column_widget.styles.max_width = width + 10

    def _update_item_styles(self, height: int) -> None:
        for item_widget in self.query(ItemWidget):
            item_widget.styles.max_height = height
