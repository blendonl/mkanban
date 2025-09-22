from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from src.domain.entities.board import Board
from src.ui.widgets.board_widget import BoardWidget
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.core.dependency_container import get_container, get_config_manager


class MKanbanApp(App):
    CSS_PATH = Path(__file__).parent / "ui" / "styles.css"
    TITLE = "MKanban"
    SUB_TITLE = "Terminal Kanban Board"

    terminal_width: reactive[int] = reactive(80)
    terminal_height: reactive[int] = reactive(24)

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
        Binding("H", action="move_left", description="Move Left"),
        ("L", "move_right", "Move Right"),
        Binding("o", "new_item", "New Item", show=False),
        Binding("a", "new_item_editor", "New Item (Editor)", show=False),
        Binding("d", "delete_item", "Delete", show=True),
        Binding("i", "edit_item", "Edit", show=False),
        Binding("p", "toggle_parents", "Toggle Parents", show=False),
        Binding("w", "save", "Save", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("c", "column_settings", "Column Settings", show=False),
        Binding("g,question_mark", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, boards_path: Path, initial_board: Optional[str] = None):
        super().__init__()
        self.container = get_container()
        self.config_manager = get_config_manager()

        # Update configuration with provided boards path
        self.config_manager.update_configuration(boards_path=str(boards_path))

        self.boards_path = self.config_manager.get_boards_path()
        self._setup_services()

        self.initial_board = initial_board
        self.current_board: Optional[Board] = None
        self.board_view: Optional[BoardWidget] = None
        self.auto_save_timer = None

    def _setup_services(self):
        self._board_service = self.container.get(BoardService)
        self._item_service = self.container.get(ItemService)

    @property
    def board_service(self):
        return self._board_service

    @property
    def item_service(self):
        return self._item_service

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-container"):
            with Horizontal(classes="board-container"):
                self.board_view = BoardWidget()
                yield self.board_view

    def on_mount(self) -> None:
        self.update_terminal_dimensions()
        self.load_initial_board()
        self.start_auto_save_timer()

    def on_resize(self, event) -> None:
        self.update_terminal_dimensions()
        if self.board_view:
            self.board_view.update_responsive_layout()

    def update_terminal_dimensions(self) -> None:
        size = self.console.size
        self.terminal_width = size.width
        self.terminal_height = size.height

    def load_initial_board(self) -> None:
        if self.initial_board:
            try:
                self.current_board = self._board_service.get_board_by_name(
                    self.initial_board
                )
            except Exception:
                self.current_board = self._board_service.get_or_create_sample_board(
                    self.initial_board
                )
        else:
            boards = self._board_service.get_all_boards()
            if boards:
                self.current_board = boards[0]
            else:
                self.current_board = self._board_service.get_or_create_sample_board(
                    "default"
                )

        if self.current_board:
            if self.board_view:
                self.board_view.set_board(self.current_board)

    def action_new_item(self) -> None:
        if self.board_view:
            self.board_view.show_new_item_dialog()

    def action_new_item_editor(self) -> None:
        if self.board_view:
            self.board_view.create_new_item_with_editor()

    def action_delete_item(self) -> None:
        if self.board_view:
            self.board_view.delete_selected_item()

    def action_edit_item(self) -> None:
        if self.board_view:
            self.board_view.edit_selected_item()

    async def action_move_left(self) -> None:
        if self.board_view:
            await self.board_view.move_left()

    async def action_move_right(self) -> None:
        if self.board_view:
            await self.board_view.move_right()

    def action_toggle_parents(self) -> None:
        if self.board_view:
            self.board_view.toggle_parent_grouping()

    def action_save(self) -> None:
        if self.current_board:
            try:
                self._board_service.save_board(self.current_board)
                self.notify("Board saved successfully")
            except Exception as e:
                self.notify(f"Error saving board: {e}", severity="error")

    def action_refresh(self) -> None:
        if self.board_view and self.current_board:
            from src.core.types import RefreshType

            self.board_view.refresh_board(refresh_type=RefreshType.FULL)

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

    def action_column_settings(self) -> None:
        if self.board_view:
            self.board_view.show_column_settings_dialog()

    def start_auto_save_timer(self) -> None:
        if self.config_manager.config.auto_save and self.config_manager.config.auto_save_interval > 0:
            self.auto_save_timer = self.set_interval(
                self.config_manager.config.auto_save_interval, self.auto_save_callback
            )

    def auto_save_callback(self) -> None:
        if self.current_board:
            try:
                self._board_service.save_board(self.current_board)
            except Exception:
                pass

    def on_unmount(self) -> None:
        if self.current_board:
            try:
                self._board_service.save_board(self.current_board)
            except Exception:
                pass

        if self.auto_save_timer:
            self.auto_save_timer.stop()

    def action_quit(self) -> None:
        if self.current_board:
            try:
                self._board_service.save_board(self.current_board)
            except Exception:
                pass
        self.exit()
