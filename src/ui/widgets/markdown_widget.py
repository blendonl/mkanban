from typing import Optional
from textual.widgets import Markdown
from ...models.item import Item


class MarkDownWidget(Markdown):

    def __init__(self, item: Item, parent_name: Optional[str] = None):
        self.item = item
        self.parent_name = parent_name

        markdown_content = self.item.title

        if self.parent_name:
            markdown_content += f"\n\n*Parent: {self.parent_name}*"

        super().__init__(markdown_content, classes="item-content")
        self.can_focus = True

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")
