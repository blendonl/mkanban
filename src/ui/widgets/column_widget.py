from typing import List
from textual.containers import Vertical, VerticalScroll
from ...models.column import Column
from ...models.item import Item
from .item_widget import ItemWidget
from .editable_item_widget import EditableItemWidget
from ...controllers.column_controller import ColumnController
from ...controllers.item_controller import ItemController


class ColumnWidget(Vertical):
    def __init__(
        self, column: Column, items: List[Item], column_controller: ColumnController
    ):
        self.column = column
        self.items = items
        self.column_controller = column_controller
        self.editing_widget = None

        super().__init__(classes="column", id=f"column_{column.id.replace('-', '_')}")
        self.border_title = f"{column.name} ({len(items)})"
        self.can_focus = True

    def compose(self):
        with Vertical(classes="items-container"):
            with VerticalScroll(classes="items-scroll"):
                for item in self.items:
                    yield ItemWidget(
                        item,
                        item_controller=ItemController(
                            self.column_controller.board,
                            item,
                            self.column_controller.storage,
                        ),
                    )

    def add_new_item_inline(self) -> None:
        if self.editing_widget:
            return

        def on_save(title: str, content: str):
            controller = self.column_controller
            controller.add_item(title, self.column.id, None, content)
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
