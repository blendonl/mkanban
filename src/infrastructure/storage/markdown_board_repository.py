from pathlib import Path
from typing import List, Optional
from src.core.types import BoardId
from src.core.constants import BOARD_FILENAME, COLUMN_METADATA_FILENAME
from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.domain.entities.parent import Parent
from src.domain.repositories.board_repository import BoardRepository
from src.utils.file_utils import find_files_by_pattern
from src.utils.string_utils import generate_id_from_name, get_safe_filename
from src.utils.date_utils import now
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import ContextAwareLogger
from src.infrastructure.storage.board_persistence import BoardPersistence
from src.infrastructure.storage.markdown_parser import (
    parse_board_metadata,
    parse_item_metadata,
    parse_column_metadata,
    save_board_metadata,
)


class MarkdownBoardRepository(BoardRepository):
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger
        self.boards_dir = path_resolver.get_boards_directory()
        self.persistence = BoardPersistence(path_resolver.get_data_dir())

    def load_all_boards(self) -> List[Board]:
        self.logger.debug("Loading all boards")
        boards: List[Board] = []

        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / BOARD_FILENAME
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board:
                        boards.append(board)

        self.logger.info(f"Loaded {len(boards)} boards")
        return boards

    def load_board_by_id(self, board_id: BoardId) -> Optional[Board]:
        self.logger.debug("Loading board by ID", board=board_id)

        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / BOARD_FILENAME
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board and board.id == board_id:
                        self.logger.info("Found board by ID", board=board.name)
                        return board

        self.logger.warning("Board not found by ID", board=board_id)
        return None

    def load_board_by_name(self, board_name: str) -> Optional[Board]:
        self.logger.debug("Loading board by name", board=board_name)
        boards = self.load_all_boards()

        for board in boards:
            if board.name.lower() == board_name.lower():
                self.logger.info("Found board by name", board=board_name)
                return board

        self.logger.warning("Board not found by name", board=board_name)
        return None

    def load_board_from_file(self, kanban_file: Path) -> Optional[Board]:
        try:
            board_name, metadata = parse_board_metadata(kanban_file)

            board = Board(
                id=metadata.get("id", kanban_file.parent.name),
                name=board_name,
                description=metadata.get("description", ""),
                created_at=metadata.get("created_at", now()),
                updated_at=metadata.get("updated_at", now()),
                file_path=kanban_file,
            )

            self._load_columns_for_board(board, kanban_file.parent)
            self._load_parents_for_board(board, metadata)

            return board
        except Exception:
            self.logger.error(
                f"Failed to load board from file: {kanban_file}",
                board=kanban_file.parent.name,
            )
            return None

    def save_board(self, board: Board) -> None:
        self.logger.debug("Saving board", board=board.name)

        kanban_file = self.persistence.get_board_file_path(board.name)
        self.path_resolver.ensure_directory_exists(kanban_file.parent)

        board_data = {
            "id": board.id,
            "name": board.name,
            "description": board.description,
            "created_at": board.created_at,
            "updated_at": board.updated_at,
            "parents": [
                {
                    "id": parent.id,
                    "name": parent.name,
                    "color": parent.color,
                    "created_at": parent.created_at,
                }
                for parent in board.parents
            ],
        }

        save_board_metadata(kanban_file, board.name, board_data)
        self._save_columns_for_board(board, kanban_file.parent)

        self.logger.info("Successfully saved board", board=board.name)

    def delete_board(self, board_id: BoardId) -> bool:
        self.logger.info("Deleting board", board=board_id)

        board = self.load_board_by_id(board_id)
        if not board:
            self.logger.warning("Cannot delete non-existent board", board=board_id)
            return False

        board_dir = self.path_resolver.get_board_directory(board.name)

        try:
            import shutil

            shutil.rmtree(board_dir)
            self.logger.info("Successfully deleted board", board=board.name)
            return True
        except Exception:
            self.logger.error("Failed to delete board directory", board=board.name)
            return False

    def list_board_names(self) -> List[str]:
        self.logger.debug("Listing board names")
        boards = self.load_all_boards()
        names = [board.name for board in boards]
        self.logger.debug(f"Found {len(names)} board names")
        return names

    def create_sample_board(self, name: str) -> Board:
        self.logger.info("Creating sample board", board=name)

        board = Board(name=name, description="Sample board for getting started")

        # Add default columns
        board.add_column("To Do", 0)
        board.add_column("In Progress", 1)
        board.add_column("Done", 2)

        # Add sample parent
        board.add_parent("Sample Project", "blue")

        self.logger.info("Created sample board", board=name)
        return board

    def _load_columns_for_board(self, board: Board, board_dir: Path) -> None:
        column_dirs = [d for d in board_dir.iterdir() if d.is_dir()]
        column_dirs.sort(key=lambda d: d.name)

        for idx, column_dir in enumerate(column_dirs):
            column_metadata_file = column_dir / COLUMN_METADATA_FILENAME

            if column_metadata_file.exists():
                try:
                    metadata = parse_column_metadata(column_metadata_file)
                    column = Column(
                        id=metadata.get("id", column_dir.name),
                        name=metadata.get(
                            "name", column_dir.name.replace("-", " ").title()
                        ),
                        position=metadata.get("position", idx),
                        limit=metadata.get("limit"),
                        created_at=metadata.get("created_at", now()),
                        updated_at=metadata.get("updated_at", now()),
                        file_path=column_metadata_file,
                    )
                except Exception:
                    column = Column(
                        id=column_dir.name,
                        name=column_dir.name.replace("-", " ").title(),
                        position=idx,
                        file_path=column_dir,
                    )
            else:
                column = Column(
                    id=column_dir.name,
                    name=column_dir.name.replace("-", " ").title(),
                    position=idx,
                    file_path=column_dir,
                )

            self._load_items_for_column(column, column_dir)
            board.columns.append(column)

        board.columns.sort(key=lambda c: (c.position, c.name))

    def _load_items_for_column(self, column: Column, column_dir: Path) -> None:
        item_files = find_files_by_pattern(column_dir, "*.md")

        for item_file in item_files:
            if item_file.name == COLUMN_METADATA_FILENAME:
                continue

            try:
                item_data = parse_item_metadata(item_file)
                item = Item(
                    id=item_data.get("id", generate_id_from_name(item_file.stem)),
                    title=item_data.get("title", item_file.stem),
                    description=item_data.get("description", ""),
                    column_id=column.id,
                    parent_id=item_data.get("parent_id"),
                    created_at=item_data.get("created_at", now()),
                    updated_at=item_data.get("updated_at", now()),
                    file_path=item_file,
                )
                column.items.append(item)
            except Exception:
                # Skip corrupted item files
                continue

    def _load_parents_for_board(self, board: Board, metadata: dict) -> None:
        parents_data = metadata.get("parents", [])

        for parent_data in parents_data:
            parent = Parent(
                id=parent_data.get(
                    "id", generate_id_from_name(parent_data.get("name", ""))
                ),
                name=parent_data.get("name", ""),
                color=parent_data.get("color", "blue"),
                created_at=parent_data.get("created_at", now()),
            )
            board.parents.append(parent)

    def _save_columns_for_board(self, board: Board, board_dir: Path) -> None:
        existing_column_dirs = {d.name for d in board_dir.iterdir() if d.is_dir()}
        board_column_dirs = {get_safe_filename(col.name) for col in board.columns}

        # Remove columns that no longer exist
        for dir_name in existing_column_dirs - board_column_dirs:
            column_dir = board_dir / dir_name
            if column_dir.exists():
                import shutil

                shutil.rmtree(column_dir)

        # Save each column
        for column in board.columns:
            column_dir = self.path_resolver.get_column_directory(
                board.name, column.name
            )
            self.persistence.save_column_metadata(
                board.name,
                column.name,
                {
                    "id": column.id,
                    "name": column.name,
                    "position": column.position,
                    "limit": column.limit,
                    "created_at": column.created_at,
                    "updated_at": column.updated_at,
                },
            )

            # Save items in this column
            for item in column.items:
                self.persistence.save_item_to_column(
                    board.name,
                    column.name,
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "parent_id": item.parent_id,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    },
                )

