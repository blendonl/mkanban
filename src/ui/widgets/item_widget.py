from typing import Optional
from textual.widgets import Markdown
from ...models.item import Item
from ...controllers.item_controller import ItemController


class ItemWidget(Markdown):
    def __init__(
        self,
        item: Item,
        item_controller: ItemController,
        parent_name: Optional[str] = None,
    ):
        self.item = item
        self.parent_name = parent_name
        self.item_controller = item_controller

        markdown_content = self.item.title

        if self.parent_name:
            markdown_content += f"\n\n*Parent: {self.parent_name}*"

        super().__init__(
            markdown_content, classes="item", id=f"item_{item.id.replace('-', '_')}"
        )
        self.can_focus = True

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")
