import frontmatter
from pathlib import Path
from typing import Optional
from src.core.exceptions import FileOperationError, ParseError
from src.core.types import Metadata


def read_frontmatter_file(file_path: Path) -> tuple[str, Metadata]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        return post.content, post.metadata
    except (IOError, OSError) as e:
        raise FileOperationError(f"Failed to read file {file_path}: {e}")
    except Exception as e:
        raise ParseError(f"Failed to parse frontmatter in {file_path}: {e}")


def _organize_metadata(metadata: Metadata) -> dict:
    """Organize metadata with a logical order, putting timestamps at the bottom.

    Order:
    1. id (required identifier)
    2. title (main field)
    3. parent_id (relationship)
    4. Other fields (alphabetically)
    5. Timestamps (moved_in_progress_at, moved_in_done_at, worked_on_for)
    6. created_at (always last)
    """
    ordered = {}

    # Define the preferred order
    priority_fields = ["id", "title", "parent_id"]
    timestamp_fields = ["moved_in_progress_at", "moved_in_done_at", "worked_on_for", "created_at"]

    # Add priority fields first (if they exist)
    for field in priority_fields:
        if field in metadata:
            ordered[field] = metadata[field]

    # Add other fields alphabetically (excluding timestamps and priority fields)
    other_fields = sorted([
        key for key in metadata.keys()
        if key not in priority_fields and key not in timestamp_fields
    ])
    for field in other_fields:
        ordered[field] = metadata[field]

    # Add timestamp fields at the end (except created_at)
    for field in timestamp_fields[:-1]:  # All except created_at
        if field in metadata:
            ordered[field] = metadata[field]

    # Add created_at last
    if "created_at" in metadata:
        ordered["created_at"] = metadata["created_at"]

    return ordered


def write_frontmatter_file(file_path: Path, content: str, metadata: Metadata) -> None:
    import logging
    logger = logging.getLogger("mkanban-daemon")

    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"About to create frontmatter post for {file_path}")

        # Organize metadata with created_at at the bottom
        ordered_metadata = _organize_metadata(metadata)

        post = frontmatter.Post(content, **ordered_metadata)
        logger.debug("Created frontmatter post, about to write file")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        logger.debug(f"Successfully wrote frontmatter file {file_path}")
    except Exception as e:
        logger.error(f"Exception in write_frontmatter_file: {e}", exc_info=True)
        raise FileOperationError(f"Failed to write file {file_path}: {e}")


def safe_rename_file(old_path: Path, new_path: Path) -> bool:
    try:
        old_path.rename(new_path)
        return True
    except (IOError, OSError):
        return False


def safe_delete_file(file_path: Path) -> bool:
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except (IOError, OSError):
        return False


def ensure_directory_exists(dir_path: Path) -> None:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except (IOError, OSError) as e:
        raise FileOperationError(f"Failed to create directory {dir_path}: {e}")


def find_files_by_pattern(directory: Path, pattern: str) -> list[Path]:
    try:
        return list(directory.glob(pattern))
    except (IOError, OSError) as e:
        raise FileOperationError(f"Failed to search files in {directory}: {e}")


def get_unique_filename(base_path: Path, item_id: str, max_retries: int = 100) -> str:
    base_name = base_path.stem
    suffix = base_path.suffix
    directory = base_path.parent

    if not (directory / base_path.name).exists():
        return base_name

    existing_item_id = _get_item_id_from_file(directory / base_path.name)
    if existing_item_id == item_id:
        return base_name

    for counter in range(1, max_retries + 1):
        test_name = f"{base_name}_{counter}"
        test_path = directory / f"{test_name}{suffix}"

        if not test_path.exists():
            return test_name

        existing_item_id = _get_item_id_from_file(test_path)
        if existing_item_id == item_id:
            return test_name

    return f"{base_name}_{item_id[:8]}"


def _get_item_id_from_file(file_path: Path) -> Optional[str]:
    try:
        _, metadata = read_frontmatter_file(file_path)
        return metadata.get("id", file_path.stem)
    except Exception:
        return file_path.stem
