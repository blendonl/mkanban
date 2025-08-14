from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from .infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from .domain.entities.board import Board
from .ui.widgets.board_widget import BoardWidget
from .controllers.board_controller import BoardController
from .services.board_service import BoardService
from .services.item_service import ItemService
from .services.validation_service import ValidationService
from .config.settings import Settings


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
        Binding("g,question_mark", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, initial_board: Optional[str] = None):
        super().__init__()
        self.settings = Settings.load()

        if data_dir != Path("./data"):
            self.settings.data_dir = str(data_dir)

        self.data_dir = Path(self.settings.data_dir).expanduser().resolve()
        
        self._setup_services()
        
        self.initial_board = initial_board
        self.current_board: Optional[Board] = None
        self.board_view: Optional[BoardWidget] = None
        self.controller: Optional[BoardController] = None
        self.auto_save_timer = None

    def _setup_services(self):
        self._storage = MarkdownStorageImpl(self.data_dir)
        self._validator = ValidationService()
        self._board_service = BoardService(self._storage, self._validator)
        self._item_service = ItemService(self._storage, self._validator)

    @property
    def storage(self):
        return self._storage

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
                self.current_board = self._board_service.get_board_by_name(self.initial_board)
            except Exception:
                self.current_board = self._board_service.get_or_create_sample_board(self.initial_board)
        else:
            boards = self._board_service.get_all_boards()
            if boards:
                self.current_board = boards[0]
            else:
                self.current_board = self._board_service.get_or_create_sample_board("default")

        if self.current_board:
            self.controller = BoardController(self.current_board, self._board_service)
            if self.board_view:
                self.board_view.set_board(self.current_board)

    def action_new_item(self) -> None:
        if self.controller and self.board_view:
            self.board_view.show_new_item_dialog()

    def action_new_item_editor(self) -> None:
        if self.controller and self.board_view:
            self.board_view.create_new_item_with_editor()

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
            from .core.types import RefreshType
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

    def start_auto_save_timer(self) -> None:
        if self.settings.auto_save and self.settings.auto_save_interval > 0:
            self.auto_save_timer = self.set_interval(
                self.settings.auto_save_interval, self.auto_save_callback
            )

    def auto_save_callback(self) -> None:
        if self.controller and self.current_board:
            try:
                self.controller.save()
            except Exception:
                pass

    def on_unmount(self) -> None:
        if self.controller and self.current_board:
            try:
                self.controller.save()
            except Exception:
                pass
        
        if self.auto_save_timer:
            self.auto_save_timer.stop()

    def action_quit(self) -> None:
        if self.controller and self.current_board:
            try:
                self.controller.save()
            except Exception:
                pass
        self.exit()