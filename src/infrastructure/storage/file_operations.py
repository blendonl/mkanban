from pathlib import Path
from typing import Optional
from ...core.exceptions import FileOperationError
from ...core.types import ItemId, Metadata
from ...utils.file_utils import read_frontmatter_file, find_files_by_pattern


def find_item_file_by_id(column_dir: Path, item_id: ItemId) -> Optional[Path]:
    if not column_dir.exists():
        return None
    
    try:
        md_files = find_files_by_pattern(column_dir, "*.md")
        for item_file in md_files:
            if item_file.name == "column.md":
                continue
            
            try:
                _, metadata = read_frontmatter_file(item_file)
                if metadata.get("id") == item_id:
                    return item_file
            except Exception:
                continue
        
        return None
    except Exception as e:
        raise FileOperationError(f"Failed to search for item {item_id} in {column_dir}: {e}")


def get_board_directory_path(boards_dir: Path, board_name: str) -> Path:
    from ...utils.string_utils import get_safe_filename
    safe_name = get_safe_filename(board_name)
    return boards_dir / safe_name


def get_column_directory_path(board_dir: Path, column_name: str) -> Path:
    from ...utils.string_utils import get_safe_filename
    safe_name = get_safe_filename(column_name)
    return board_dir / safe_name


def cleanup_column_files(column_dir: Path, current_item_ids: set[ItemId]) -> None:
    if not column_dir.exists():
        return
    
    md_files = find_files_by_pattern(column_dir, "*.md")
    item_id_to_files = {}
    
    for item_file in md_files:
        if item_file.name == "column.md":
            continue
        
        try:
            _, metadata = read_frontmatter_file(item_file)
            file_item_id = metadata.get("id")
            
            if file_item_id:
                if file_item_id not in current_item_ids:
                    item_file.unlink()
                else:
                    if file_item_id not in item_id_to_files:
                        item_id_to_files[file_item_id] = []
                    item_id_to_files[file_item_id].append(item_file)
        except Exception:
            continue
    
    for item_id, files in item_id_to_files.items():
        if len(files) > 1:
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            for old_file in files[1:]:
                old_file.unlink()