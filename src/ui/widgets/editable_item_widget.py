from typing import Optional
from textual.containers import Vertical


from ...models.item import Item
from .vim_widgets import VimTextArea


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
