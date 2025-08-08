from textual.widgets import Markdown
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.app import ComposeResult


class HelpDialog(ModalScreen):
    def __init__(
        self,
        help_text: str = """
# MKanban - Vim Keybindings

## Navigation
- j/Down    : Move down (navigate items)
- k/Up      : Move up (navigate items)
- h         : Move left (previous column)
- l         : Move right (next column)
- gg        : Go to first item
- G         : Go to last item

## Scrolling
- Shift+J   : Scroll column down
- Shift+K   : Scroll column up
- Ctrl+D    : Scroll down (page)
- Ctrl+U    : Scroll up (page)

## Item Operations
- o         : Create new item (inline markdown editor)
- i         : Edit item (inline markdown editor)
- dd        : Delete item
- m         : Move item to different column

## Text Editing (Vim Motions)
### Normal Mode
- i         : Insert mode at cursor
- I         : Insert mode at line start
- a         : Insert mode after cursor
- A         : Insert mode at line end
- o         : New line below and insert
- O         : New line above and insert
- h/j/k/l   : Navigate cursor
- w         : Next word
- b         : Previous word
- 0         : Beginning of line
- $         : End of line
- gg        : First line
- G         : Last line
- x         : Delete character
- X         : Delete char before cursor
- dd        : Delete line
- v         : Visual mode
- Escape    : Return to normal mode

### Insert Mode
- Escape    : Return to normal mode
- Normal typing works

### Visual Mode
- h/j/k/l   : Extend selection
- d/x       : Delete selection
- Escape    : Return to normal mode

## Dialog Navigation (Vim Style)
- j/k       : Navigate between fields
- i         : Enter insert mode for current field
- Enter     : Confirm action
- Escape    : Cancel/Exit

## Inline Editing
- Ctrl+S    : Save item while editing
- Escape    : Cancel editing (from normal mode)
- # Title   : First # line becomes item title

## View Operations
- p         : Toggle parent grouping
- w         : Save board
- r         : Refresh view

## Other
- g?        : Show this help
- q/Escape  : Quit
- Ctrl+C    : Force quit""",
    ):
        super().__init__()
        self.help_text = help_text

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog help-dialog"):
            with VerticalScroll(classes="vertical-scroll"):
                yield Markdown(self.help_text)

    def on_key(self, event) -> None:
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
