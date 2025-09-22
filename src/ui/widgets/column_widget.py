from typing import List
from textual.containers import Vertical, VerticalScroll
from src.core.exceptions import ValidationError
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.ui.widgets.item_widget import ItemWidget
from src.ui.widgets.editable_item_widget import EditableItemWidget
from controllers.column_controller import ColumnController
from controllers.item_controller import ItemController


class ColumnWidget(Vertical):
    def __init__(
        self, column: Column, items: List[Item], column_controller: ColumnController
    ):
        self.column = column
        self.items = items
        self.column_controller = column_controller
        self.editing_widget = None
        self._max_items_visible = None

        super().__init__(classes="column", id=f"column_{column.id.replace('-', '_')}")
        self.border_title = self._get_column_title(len(items))
        self.can_focus = True

    def _get_column_title(self, item_count: int) -> str:
        if self.column.limit is not None:
            return f"{self.column.name} ({item_count}/{self.column.limit})"
        return f"{self.column.name} ({item_count})"

    def update_title(self) -> None:
        current_count = len(self.column.get_all_items())
        self.border_title = self._get_column_title(current_count)

    def compose(self):
        with Vertical(classes="items-container"):
            with VerticalScroll(classes="items-scroll"):
                for item in self.items:
                    yield ItemWidget(
                        item,
                        item_controller=ItemController(
                            self.column_controller.board,
                            item,
                            self.column_controller.board_service,
                            self.column_controller.item_service,
                        ),
                    )

    def add_new_item_inline(self) -> None:
        if self.editing_widget:
            return

        def on_save(title: str, content: str):
            try:
                controller = self.column_controller
                controller.add_item(title, None, content)
                self.update_title()
                self._finish_editing()
            except ValidationError as e:
                # TODO: Show error message to user (needs notification system)
                self._finish_editing()

        def on_cancel():
            self._finish_editing()

        self.editing_widget = EditableItemWidget(
            is_new=True, on_save=on_save, on_cancel=on_cancel
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
