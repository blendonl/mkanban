import frontmatter
from pathlib import Path
from typing import Optional, Dict, Any
from core.exceptions import FileOperationError, ParseError
from core.types import Metadata


def read_frontmatter_file(file_path: Path) -> tuple[str, Metadata]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        return post.content, post.metadata
    except (IOError, OSError) as e:
        raise FileOperationError(f"Failed to read file {file_path}: {e}")
    except Exception as e:
        raise ParseError(f"Failed to parse frontmatter in {file_path}: {e}")


def write_frontmatter_file(file_path: Path, content: str, metadata: Metadata) -> None:
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        post = frontmatter.Post(content, **metadata)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
    except (IOError, OSError) as e:
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
