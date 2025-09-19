from pathlib import Path
from typing import List, Optional
from core.exceptions import StorageError, BoardNotFoundError
from core.types import BoardId
from core.constants import BOARD_FILENAME, COLUMN_METADATA_FILENAME
from domain.entities.board import Board
from domain.entities.column import Column
from domain.entities.item import Item
from domain.entities.parent import Parent
from domain.repositories.board_repository import BoardRepository
from domain.repositories.storage_repository import StorageRepository
from utils.file_utils import find_files_by_pattern, ensure_directory_exists
from utils.string_utils import generate_id_from_name, get_safe_filename
from utils.date_utils import now
from infrastructure.storage.board_persistence import BoardPersistence
from infrastructure.storage.markdown_parser import (
    parse_board_metadata,
    parse_item_metadata,
    parse_column_metadata,
    save_board_metadata,
)
from infrastructure.storage.file_operations import (
    get_board_directory_path,
    find_item_file_by_id,
)


class MarkdownStorageImpl(BoardRepository, StorageRepository):
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        ensure_directory_exists(self.data_dir)

        self.boards_dir = self.data_dir / "boards"
        ensure_directory_exists(self.boards_dir)

        self.persistence = BoardPersistence(data_dir)

    def load_all_boards(self) -> List[Board]:
        boards: List[Board] = []

        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / BOARD_FILENAME
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board:
                        boards.append(board)

        return boards

    def load_board_by_id(self, board_id: BoardId) -> Optional[Board]:
        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / BOARD_FILENAME
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board and board.id == board_id:
                        return board
        return None

    def load_board_by_name(self, board_name: str) -> Optional[Board]:
        boards = self.load_all_boards()
        for board in boards:
            if board.name.lower() == board_name.lower():
                return board
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
            return None

    def save_board(self, board: Board) -> None:
        kanban_file = self.persistence.get_board_file_path(board.name)
        ensure_directory_exists(kanban_file.parent)

        board_data = {
            "id": board.id,
            "kanban-plugin": "board",
            "created_at": board.created_at,
            "updated_at": board.updated_at,
            "parents": [
                {
                    "id": parent.id,
                    "name": parent.name,
                    "description": parent.description,
                    "color": parent.color,
                    "created_at": parent.created_at,
                    "updated_at": parent.updated_at,
                }
                for parent in board.parents
            ],
        }

        save_board_metadata(kanban_file, board.name, board_data)

        for column in sorted(board.columns, key=lambda c: (c.position, c.name)):
            self._save_column_with_items(board, column)

    def delete_board(self, board_id: BoardId) -> bool:
        board = self.load_board_by_id(board_id)
        if not board:
            return False

        try:
            board_dir = get_board_directory_path(self.boards_dir, board.name)
            if board_dir.exists():
                import shutil

                shutil.rmtree(board_dir)
                return True
        except Exception:
            return False

        return False

    def list_board_names(self) -> List[str]:
        boards = self.load_all_boards()
        return [board.name for board in boards]

    def create_sample_board(self, name: str = "Sample Board") -> Board:
        board = Board(name=name, description="Welcome to MKanban!")

        todo_col = board.add_column("To Do", 1)
        progress_col = board.add_column("In Progress", 2)
        review_col = board.add_column("Review", 3)
        done_col = board.add_column("Done", 4)

        return board

    def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
        return self.persistence.delete_item_from_column(
            board.name, column.name, item.id
        )

    def move_item_between_columns(
        self, board: Board, item: Item, old_column: Column, new_column: Column
    ) -> bool:
        item_data = item.to_dict()
        item_data["column_id"] = new_column.id

        return self.persistence.move_item_between_columns(
            board.name, old_column.name, new_column.name, item_data
        )

    def save_board_to_storage(self, board: Board) -> None:
        self.save_board(board)

    def _load_columns_for_board(self, board: Board, board_dir: Path) -> None:
        columns_data = []

        for folder_path in board_dir.iterdir():
            if folder_path.is_dir() and folder_path.name != "items":
                # Use folder name as column ID directly
                column_id = folder_path.name
                # Generate display name from folder name
                column_name = (
                    folder_path.name.replace("-", " ").replace("_", " ").title()
                )
                position = None

                # Try to get position and display name from column metadata (optional)
                column_md_path = folder_path / COLUMN_METADATA_FILENAME
                column_metadata = parse_column_metadata(column_md_path)
                if column_metadata:
                    # Override column name if specified in metadata
                    column_name = column_metadata.get("name", column_name)
                    position = column_metadata.get("position")

                columns_data.append(
                    {
                        "id": column_id,
                        "name": column_name,
                        "position": position,
                        "folder_path": folder_path,
                    }
                )

        columns_data.sort(
            key=lambda col: (
                1 if col["position"] is None else 0,
                col["position"] if col["position"] is not None else 0,
                col["name"],
            )
        )

        used_positions = {
            col["position"] for col in columns_data if col["position"] is not None
        }
        next_position = 0

        for col_data in columns_data:
            if col_data["position"] is None:
                while next_position in used_positions:
                    next_position += 1
                position = next_position
                used_positions.add(next_position)
                next_position += 1
            else:
                position = col_data["position"]

            column = Column(
                id=col_data["id"],
                name=col_data["name"],
                position=position,
                file_path=str(col_data["folder_path"]),
            )
            board.columns.append(column)
            self._load_items_for_column(board, column, col_data["folder_path"])

    def _load_items_for_column(
        self, board: Board, column: Column, column_dir: Path
    ) -> None:
        md_files = find_files_by_pattern(column_dir, "*.md")
        for item_file in md_files:
            if item_file.name != COLUMN_METADATA_FILENAME:
                item = self._load_item_from_file(item_file, column.id)
                if item:
                    column.items.append(item)

    def _load_item_from_file(self, item_file: Path, column_id: str) -> Optional[Item]:
        try:
            title, content, metadata = parse_item_metadata(item_file)

            # Column ID comes from the folder structure, not metadata
            # Create Item with optional git metadata
            item_data = {
                "id": metadata.get("id", item_file.stem),
                "column_id": column_id,  # Always use the folder-based column_id
                "title": title,
                "description": content,
                "parent_id": metadata.get("parent_id"),
                "created_at": metadata.get("created_at", now()),
                "updated_at": metadata.get("updated_at", now()),
                "file_path": str(item_file),
            }

            # Add git-specific fields if present
            if metadata.get("is_git_managed"):
                from domain.entities.item import GitMetadata

                item_data.update({
                    "is_git_managed": metadata.get("is_git_managed", False),
                    "auto_sync_enabled": metadata.get("auto_sync_enabled", True),
                })

                if metadata.get("git_metadata"):
                    item_data["git_metadata"] = GitMetadata(**metadata["git_metadata"])

            return Item(**item_data)
        except Exception:
            return None

    def _load_parents_for_board(self, board: Board, metadata: dict) -> None:
        for parent_data in metadata.get("parents", []):
            parent = Parent(
                id=parent_data["id"],
                name=parent_data["name"],
                description=parent_data.get("description", ""),
                color=parent_data.get("color", "blue"),
                created_at=parent_data.get("created_at", now()),
                updated_at=parent_data.get("updated_at", now()),
            )
            board.parents.append(parent)

    def _save_column_with_items(self, board: Board, column: Column) -> None:
        current_item_ids = {item.id for item in column.items}

        # Add debug logging
        import logging
        logger = logging.getLogger("mkanban-daemon")
        logger.debug(f"Saving column {board.name} '{column.name}' (ID: {column.id}) with {len(column.items)} items")
        for item in column.items:
            logger.debug(f"  Item: {item.title} (ID: {item.id})")

        for item in column.items:
            item_data = item.to_dict()
            self.persistence.save_item_to_column(board.name, column.name, item_data)

        self.persistence.save_column_metadata_if_needed(board.name, column.to_dict())
        self.persistence.cleanup_column(board.name, column.name, current_item_ids)

    def _get_board_directory(self, board: Board) -> Path:
        """Get the directory path for a board"""
        return get_board_directory_path(self.boards_dir, board.name)

    def _get_safe_name(self, name: str) -> str:
        """Get a safe filename for the given name"""
        return get_safe_filename(name)

    def _find_item_file_by_id(self, items_dir: Path, item_id: str) -> Optional[Path]:
        """Find an item file by its ID in the given directory"""
        return find_item_file_by_id(items_dir, item_id)

    def load_item_from_title_file(
        self, item_file: Path, column_id: str
    ) -> Optional[Item]:
        """Load an item from a file path"""
        return self._load_item_from_file(item_file, column_id)
