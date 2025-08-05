"""Dialog widgets for MKanban."""

from typing import Optional, List, Callable
from textual.widgets import Button, Input, Label, Select, Static, Markdown
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.app import ComposeResult

from ..models import Board, Column, Parent
from .vim_widgets import VimInput, VimMode


class EditItemDialog(ModalScreen):
    """Dialog for editing an existing item."""

    def __init__(self, board: Board, item_title: str, item_description: str,
                 item_column_id: str, item_parent_id: Optional[str],
                 on_update: Callable[[str, str, str, Optional[str]], None]):
        """Initialize dialog."""
        super().__init__()
        self.board = board
        self.item_title = item_title
        self.item_description = item_description
        self.item_column_id = item_column_id
        self.item_parent_id = item_parent_id
        self.on_update = on_update

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Vertical(classes="dialog"):
            yield Label("Edit Item", classes="dialog-title")

            yield Label("Title:")
            yield VimInput(value=self.item_title, id="title_input")

            yield Label("Description:")
            yield VimInput(value=self.item_description, placeholder="Enter description", id="description_input")

            yield Label("Column:")
            column_options = [(col.name, col.id) for col in sorted(
                self.board.columns, key=lambda c: c.position)]
            yield Select(column_options, value=self.item_column_id, id="column_select")

            yield Label("Parent (optional):")
            parent_options = [("None", None)] + [(parent.name, parent.id)
                                                 for parent in self.board.parents]
            current_parent = self.item_parent_id if self.item_parent_id else None
            yield Select(parent_options, value=current_parent, id="parent_select")

            with Horizontal():
                yield Button("Update", variant="primary", id="update_btn")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "update_btn":
            title_input = self.query_one("#title_input", VimInput)
            description_input = self.query_one("#description_input", VimInput)
            column_select = self.query_one("#column_select", Select)
            parent_select = self.query_one("#parent_select", Select)

            title = title_input.value.strip()
            if not title:
                self.app.notify("Title is required", severity="error")
                return

            description = description_input.value.strip()
            column_id = column_select.value
            parent_id = parent_select.value if parent_select.value != "None" else None

            self.on_update(title, description, column_id, parent_id)
            self.dismiss()

        elif event.button.id == "cancel_btn":
            self.dismiss()


class MoveItemDialog(ModalScreen):
    """Dialog for moving an item to a different column."""

    def __init__(self, board: Board, current_column_id: str,
                 on_move: Callable[[str], None]):
        """Initialize dialog."""
        super().__init__()
        self.board = board
        self.current_column_id = current_column_id
        self.on_move = on_move

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Vertical(classes="dialog"):
            yield Label("Move Item", classes="dialog-title")

            yield Label("Select target column:")
            column_options = [(col.name, col.id) for col in sorted(
                self.board.columns, key=lambda c: c.position)]
            yield Select(column_options, value=self.current_column_id, id="column_select")

            with Horizontal():
                yield Button("Move", variant="primary", id="move_btn")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "move_btn":
            column_select = self.query_one("#column_select", Select)
            target_column_id = column_select.value

            if target_column_id == self.current_column_id:
                self.app.notify("Item is already in that column")
                self.dismiss()
                return

            self.on_move(target_column_id)
            self.dismiss()

        elif event.button.id == "cancel_btn":
            self.dismiss()


class ConfirmDialog(ModalScreen):
    """Generic confirmation dialog."""

    def __init__(self, title: str, message: str, on_confirm: Callable[[], None]):
        """Initialize dialog."""
        super().__init__()
        self.title = title
        self.message = message
        self.on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Vertical(classes="dialog"):
            yield Label(self.title, classes="dialog-title")
            yield Label(self.message)

            with Horizontal():
                yield Button("Yes", variant="primary", id="yes_btn")
                yield Button("No", id="no_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "yes_btn":
            self.on_confirm()
            self.dismiss()
        elif event.button.id == "no_btn":
            self.dismiss()


class HelpDialog(ModalScreen):
    """Help dialog showing keybindings and usage."""

    def __init__(self, help_text: str):
        """Initialize dialog."""
        super().__init__()
        self.help_text = help_text

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Vertical(classes="dialog help-dialog"):
            with VerticalScroll(classes="vertical-scroll"):
                yield Markdown(self.help_text)

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
        elif event.key in ("escape", "q", "enter"):
            self.dismiss()
