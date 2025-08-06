from typing import Optional
from textual.containers import Vertical
from ...models.item import Item
from .markdown_widget import MarkDownWidget
from ...controllers.item_controller import ItemController


class ItemWidget(Vertical):

    def __init__(self,
                 item: Item,
                 item_controller: ItemController,
                 parent_name: Optional[str] = None):
        self.item = item
        self.parent_name = parent_name
        self.item_controller = item_controller
        super().__init__(classes="item", id=f"item_{
            item.id.replace("-", "_")}")
        self.can_focus = True

    def compose(self):
        yield MarkDownWidget(self.item)

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")
