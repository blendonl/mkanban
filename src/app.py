"""Main MKanban application."""

from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Static
from textual.binding import Binding

from .storage import MarkdownStorage
from .models import Board
from .ui import BoardView
from .controllers import BoardController
from .utils import Config


class MKanbanApp(App):
    """Main MKanban TUI application."""

    CSS_PATH = "ui/styles.css"
    TITLE = "MKanban"
    SUB_TITLE = "Terminal Kanban Board"

    BINDINGS = [
        # Vim-style navigation and actions
        Binding("j", "focus_next", "Next", show=False),
        Binding("k", "focus_previous", "Previous", show=False),
        Binding("h", "focus_left", "Left", show=False),
        Binding("l", "focus_right", "Right", show=False),
        Binding("g,g", "focus_first", "First", show=False),
        Binding("G", "focus_last", "Last", show=False),

        # Scrolling bindings
        Binding("ctrl+d", "scroll_down", "Scroll Down", show=False),
        Binding("ctrl+u", "scroll_up", "Scroll Up", show=False),
        Binding("shift+j", "column_scroll_down",
                "Column Scroll Down", show=False),
        Binding("shift+k", "column_scroll_up", "Column Scroll Up", show=False),

        # Item operations (vim-style)
        Binding("o", "new_item", "New Item", show=False),
        Binding("dd", "delete_item", "Delete", show=False),
        Binding("i", "edit_item", "Edit", show=False),
        Binding("m", "move_item", "Move", show=False),

        # View operations
        Binding("p", "toggle_parents", "Toggle Parents", show=False),
        Binding("w", "save", "Save", show=False),
        Binding("r", "refresh", "Refresh", show=False),

        # Help and quit
        Binding("g,question_mark", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, initial_board: Optional[str] = None):
        """Initialize the application."""
        super().__init__()
        self.config = Config.load()

        # Override data_dir if provided
        if data_dir != Path("./data"):
            self.config.data_dir = str(data_dir)

        self.data_dir = Path(self.config.data_dir).expanduser().resolve()
        self.storage = MarkdownStorage(self.data_dir)
        self.initial_board = initial_board
        self.current_board: Optional[Board] = None
        self.controller: Optional[BoardController] = None
        self.board_view: Optional[BoardView] = None

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()

        with Vertical(classes="main-container"):
            with Horizontal(classes="board-container"):
                self.board_view = BoardView()
                yield self.board_view

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.load_initial_board()

    def load_initial_board(self) -> None:
        """Load the initial board."""
        try:
            if self.initial_board:
                # Load specific board by name
                boards = self.storage.load_boards()
                board_found = None
                for board in boards:
                    if board.name.lower() == self.initial_board.lower():
                        board_found = board
                        break

                if board_found:
                    self.current_board = board_found
                else:
                    self.notify(
                        f"Board '{self.initial_board}' not found", severity="error")
                    self.create_sample_board()
            else:
                # Load first available board or create sample
                boards = self.storage.load_boards()
                if boards:
                    self.current_board = boards[0]
                else:
                    self.create_sample_board()

            if self.current_board:
                self.controller = BoardController(
                    self.current_board, self.storage)
                if self.board_view:
                    self.board_view.set_board(self.current_board)

        except Exception as e:
            self.notify(f"Error loading board: {e}", severity="error")
            self.create_sample_board()

    def create_sample_board(self) -> None:
        """Create and load a sample board."""
        self.current_board = self.storage.create_sample_board("My Board")
        self.controller = BoardController(self.current_board, self.storage)
        if self.board_view:
            self.board_view.set_board(self.current_board)

    def action_new_item(self) -> None:
        """Create a new item."""
        if self.controller and self.board_view:
            self.board_view.show_new_item_dialog()

    def action_delete_item(self) -> None:
        """Delete the selected item."""
        if self.controller and self.board_view:
            self.board_view.delete_selected_item()

    def action_edit_item(self) -> None:
        """Edit the selected item."""
        if self.controller and self.board_view:
            self.board_view.edit_selected_item()

    def action_move_item(self) -> None:
        """Move the selected item."""
        if self.controller and self.board_view:
            self.board_view.show_move_item_dialog()

    def action_toggle_parents(self) -> None:
        """Toggle parent grouping view."""
        if self.board_view:
            self.board_view.toggle_parent_grouping()

    def action_save(self) -> None:
        """Save the current board."""
        if self.controller:
            try:
                self.controller.save()
                self.notify("Board saved successfully")
            except Exception as e:
                self.notify(f"Error saving board: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the board view."""
        if self.board_view and self.current_board:
            self.board_view.refresh_board()

    # Vim-style navigation actions
    def action_focus_next(self) -> None:
        """Focus next widget (vim j)."""
        self.screen.focus_next()

    def action_focus_previous(self) -> None:
        """Focus previous widget (vim k)."""
        self.screen.focus_previous()

    def action_focus_left(self) -> None:
        """Focus left widget (vim h)."""
        if self.board_view:
            self.board_view.move_focus_left()

    def action_focus_right(self) -> None:
        """Focus right widget (vim l)."""
        if self.board_view:
            self.board_view.move_focus_right()

    def action_focus_first(self) -> None:
        """Focus first widget (vim gg)."""
        if self.board_view:
            self.board_view.move_focus_first()

    def action_focus_last(self) -> None:
        """Focus last widget (vim G)."""
        if self.board_view:
            self.board_view.move_focus_last()

    def action_show_help(self) -> None:
        """Show help dialog (vim g?)."""
        if self.board_view:
            self.board_view.show_help_dialog()

    def action_scroll_down(self) -> None:
        """Scroll down (ctrl+d)."""
        if self.board_view:
            self.board_view.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll up (ctrl+u)."""
        if self.board_view:
            self.board_view.scroll_up()

    def action_column_scroll_down(self) -> None:
        """Scroll column down (shift+j)."""
        if self.board_view:
            self.board_view.column_scroll_down()

    def action_column_scroll_up(self) -> None:
        """Scroll column up (shift+k)."""
        if self.board_view:
            self.board_view.column_scroll_up()
