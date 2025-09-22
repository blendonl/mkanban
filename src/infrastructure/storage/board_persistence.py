from pathlib import Path
from src.core.types import ItemId
from src.core.constants import BOARD_FILENAME, COLUMN_METADATA_FILENAME
from src.utils.file_utils import (
    ensure_directory_exists,
    safe_delete_file,
    safe_rename_file,
    get_unique_filename,
)
from src.utils.string_utils import get_title_filename
from src.utils.date_utils import now
from src.infrastructure.storage.file_operations import (
    find_item_file_by_id,
    get_board_directory_path,
    get_column_directory_path,
    cleanup_column_files,
)
from src.infrastructure.storage.markdown_parser import (
    save_item_with_metadata,
    save_column_metadata,
)


class BoardPersistence:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        ensure_directory_exists(self.data_dir)

        self.boards_dir = self.data_dir / "boards"
        ensure_directory_exists(self.boards_dir)

    def save_item_to_column(
        self, board_name: str, column_name: str, item_data: dict
    ) -> None:
        # Add debug logging
        import logging
        logger = logging.getLogger("mkanban-daemon")
        logger.debug(f"save_item_to_column: board='{board_name}', column='{column_name}', item='{item_data.get('title', 'unknown')}'")

        board_dir = get_board_directory_path(self.boards_dir, board_name)
        column_dir = get_column_directory_path(board_dir, column_name)
        logger.debug(f"Column directory: {column_dir}")
        ensure_directory_exists(column_dir)

        item_id = item_data["id"]
        title = item_data["title"]
        content = item_data.get("description", "")

        new_filename = get_title_filename(title)
        old_item_file = find_item_file_by_id(column_dir, item_id)
        new_item_file = column_dir / f"{new_filename}.md"

        if old_item_file and old_item_file.exists():
            current_filename = old_item_file.stem
            if current_filename != new_filename:
                if new_item_file.exists() and new_item_file != old_item_file:
                    unique_filename = get_unique_filename(new_item_file, item_id)
                    new_item_file = column_dir / f"{unique_filename}.md"
                    new_filename = unique_filename

                if not safe_rename_file(old_item_file, new_item_file):
                    new_item_file = old_item_file

        # Extract all metadata from item_data, excluding content and title which are handled separately
        item_metadata = {
            key: value for key, value in item_data.items()
            if key not in ["title", "description"]  # title is passed separately, description becomes content
        }

        # Ensure required fields have defaults
        item_metadata.setdefault("created_at", now())
        item_metadata.setdefault("updated_at", now())

        try:
            save_item_with_metadata(new_item_file, title, content, item_metadata)
            logger.debug(f"Successfully saved item file: {new_item_file}")
        except Exception as e:
            logger.error(f"Failed to save item file {new_item_file}: {e}", exc_info=True)
            raise

    def delete_item_from_column(
        self, board_name: str, column_name: str, item_id: ItemId
    ) -> bool:
        board_dir = get_board_directory_path(self.boards_dir, board_name)
        column_dir = get_column_directory_path(board_dir, column_name)

        item_file = find_item_file_by_id(column_dir, item_id)
        if item_file and item_file.exists():
            return safe_delete_file(item_file)
        return False

    def move_item_between_columns(
        self,
        board_name: str,
        old_column_name: str,
        new_column_name: str,
        item_data: dict,
    ) -> bool:
        board_dir = get_board_directory_path(self.boards_dir, board_name)
        old_column_dir = get_column_directory_path(board_dir, old_column_name)
        new_column_dir = get_column_directory_path(board_dir, new_column_name)

        ensure_directory_exists(new_column_dir)

        item_id = item_data["id"]
        old_item_file = find_item_file_by_id(old_column_dir, item_id)

        if old_item_file and old_item_file.exists():
            item_data["updated_at"] = now()
            self.save_item_to_column(board_name, new_column_name, item_data)
            safe_delete_file(old_item_file)
            return True

        return False

    def save_column_metadata(
        self, board_name: str, column_name: str, column_data: dict
    ) -> None:
        board_dir = get_board_directory_path(self.boards_dir, board_name)
        column_dir = get_column_directory_path(board_dir, column_name)
        ensure_directory_exists(column_dir)
        column_metadata_file = column_dir / COLUMN_METADATA_FILENAME

        metadata = {
            "position": column_data.get("position"),
            "created_at": column_data.get("created_at", now()),
            "updated_at": column_data.get("updated_at", now()),
        }

        if column_data.get("limit") is not None:
            metadata["limit"] = column_data["limit"]

        save_column_metadata(column_metadata_file, column_name, metadata)

    def save_column_metadata_if_needed(
        self, board_name: str, column_data: dict
    ) -> None:
        needs_metadata = (
            column_data.get("position", 0) != 0 or column_data.get("limit") is not None
        )

        if needs_metadata:
            self.save_column_metadata(board_name, column_data["name"], column_data)

    def cleanup_column(
        self, board_name: str, column_name: str, current_item_ids: set[ItemId]
    ) -> None:
        board_dir = get_board_directory_path(self.boards_dir, board_name)
        column_dir = get_column_directory_path(board_dir, column_name)
        cleanup_column_files(column_dir, current_item_ids)

    def get_board_file_path(self, board_name: str) -> Path:
        board_dir = get_board_directory_path(self.boards_dir, board_name)
        return board_dir / BOARD_FILENAME

    def list_board_directories(self) -> list[Path]:
        if not self.boards_dir.exists():
            return []
        return [d for d in self.boards_dir.iterdir() if d.is_dir()]
