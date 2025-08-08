from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from .storage.markdown_storage import MarkdownStorage
from .models.board import Board
from .ui.widgets.board_widget import BoardWidget
from .controllers.board_controller import BoardController
from .utils.config import Config


class MKanbanApp(App):
    CSS_PATH = "ui/styles.css"
    TITLE = "MKanban"
    SUB_TITLE = "Terminal Kanban Board"

    BINDINGS = [
        Binding("j", "focus_next", "Next", show=False),
        Binding("k", "focus_previous", "Previous", show=False),
        Binding("h", "focus_left", "Left", show=False),
        Binding("l", "focus_right", "Right", show=False),
        Binding("g,g", "focus_first", "First", show=False),
        Binding("G", "focus_last", "Last", show=False),
        Binding("ctrl+d", "scroll_down", "Scroll Down", show=False),
        Binding("ctrl+u", "scroll_up", "Scroll Up", show=False),
        Binding("shift+j", "column_scroll_down", "Column Scroll Down", show=False),
        Binding("H", action="move_left", description="Column Scroll Down"),
        ("L", "move_right", "Move Left"),
        Binding("o", "new_item", "New Item", show=False),
        Binding("d", "delete_item", "Delete", show=True),
        Binding("i", "edit_item", "Edit", show=False),
        Binding("p", "toggle_parents", "Toggle Parents", show=False),
        Binding("w", "save", "Save", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("g,question_mark", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, initial_board: Optional[str] = None):
        super().__init__()
        self.config = Config.load()

        if data_dir != Path("./data"):
            self.config.data_dir = str(data_dir)

        self.data_dir = Path(self.config.data_dir).expanduser().resolve()
        self.storage = MarkdownStorage(self.data_dir)
        self.initial_board = initial_board
        self.current_board: Optional[Board] = None
        self.board_view: Optional[BoardWidget] = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-container"):
            with Horizontal(classes="board-container"):
                self.board_view = BoardWidget()
                yield self.board_view

    def on_mount(self) -> None:
        self.load_initial_board()

    def load_initial_board(self) -> None:
        if self.initial_board:
            boards = self.storage.load_boards()
            board_found = None
            for board in boards:
                if board.name.lower() == self.initial_board.lower():
                    board_found = board
                    break

            if board_found:
                self.current_board = board_found
            else:
                sample_board = self.storage.create_sample_board(self.initial_board)
                self.storage.save_board(sample_board)
                self.current_board = sample_board
        else:
            boards = self.storage.load_boards()
            if boards:
                self.current_board = boards[0]
            else:
                sample_board = self.storage.create_sample_board("Welcome Board 1")
                self.storage.save_board(sample_board)
                self.current_board = sample_board

        if self.current_board:
            self.controller = BoardController(self.current_board, self.storage)
            if self.board_view:
                self.board_view.set_board(self.current_board)

    def action_new_item(self) -> None:
        if self.controller and self.board_view:
            self.board_view.show_new_item_dialog()

    def action_delete_item(self) -> None:
        if self.controller and self.board_view:
            self.board_view.delete_selected_item()

    def action_edit_item(self) -> None:
        if self.controller and self.board_view:
            self.board_view.edit_selected_item()

    async def action_move_left(self) -> None:
        if self.controller and self.board_view:
            await self.board_view.move_left()

    async def action_move_right(self) -> None:
        if self.controller and self.board_view:
            await self.board_view.move_right()

    def action_toggle_parents(self) -> None:
        if self.board_view:
            self.board_view.toggle_parent_grouping()

    def action_save(self) -> None:
        if self.controller:
            try:
                self.controller.save()
                self.notify("Board saved successfully")
            except Exception as e:
                self.notify(f"Error saving board: {e}", severity="error")

    def action_refresh(self) -> None:
        if self.board_view and self.current_board:
            from .ui.board_view import RefreshType

            self.board_view.refresh_board(refresh_type=RefreshType.FULL)

    # Vim-style navigation actions
    def action_focus_next(self) -> None:
        if self.board_view:
            self.board_view.move_focus_down()
        else:
            self.screen.focus_next()

    def action_focus_previous(self) -> None:
        if self.board_view:
            self.board_view.move_focus_up()
        else:
            self.screen.focus_previous()

    def action_focus_left(self) -> None:
        if self.board_view:
            self.board_view.move_focus_left()

    def action_focus_right(self) -> None:
        if self.board_view:
            self.board_view.move_focus_right()

    def action_focus_first(self) -> None:
        if self.board_view:
            self.board_view.move_focus_first()

    def action_focus_last(self) -> None:
        if self.board_view:
            self.board_view.move_focus_last()

    def action_show_help(self) -> None:
        if self.board_view:
            self.board_view.show_help_dialog()
