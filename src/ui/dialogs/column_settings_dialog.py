from textual.widgets import Input, Button, Static, Label
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.validation import Integer
from typing import Optional, Callable
from domain.entities.column import Column


class ColumnSettingsDialog(ModalScreen):
    def __init__(
        self,
        column: Column,
        on_save: Callable[[Optional[int]], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.column = column
        self.on_save = on_save
        self.on_cancel = on_cancel

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog column-settings-dialog"):
            yield Label(f"Column Settings: {self.column.name}", classes="dialog-title")

            with Vertical(classes="form-container"):
                yield Label("Item Limit:", classes="field-label")
                yield Static(
                    "Set the maximum number of items for this column (leave empty for unlimited)",
                    classes="help-text",
                )

                current_limit = (
                    str(self.column.limit) if self.column.limit is not None else ""
                )
                yield Input(
                    value=current_limit,
                    placeholder="Enter number or leave empty for unlimited",
                    validators=[Integer(minimum=1)],
                    id="limit-input",
                )

            with Horizontal(classes="button-container"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            limit_input = self.query_one("#limit-input", Input)

            if limit_input.value.strip():
                try:
                    limit_value = int(limit_input.value.strip())
                    if limit_value < 1:
                        self.app.notify("Limit must be at least 1", severity="error")
                        return
                    self.on_save(limit_value)
                except ValueError:
                    self.app.notify("Please enter a valid number", severity="error")
                    return
            else:
                self.on_save(None)  # No limit

            self.dismiss()
        elif event.button.id == "cancel-btn":
            if self.on_cancel:
                self.on_cancel()
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key == "escape":
            if self.on_cancel:
                self.on_cancel()
            self.dismiss()
        elif event.key == "enter":
            # Simulate save button press
            save_btn = self.query_one("#save-btn", Button)
            save_btn.press()
