import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.core.exceptions import ParseError
from src.core.types import Metadata
from src.utils.file_utils import read_frontmatter_file, write_frontmatter_file
from src.utils.string_utils import extract_title_from_content, ensure_title_header
from src.utils.date_utils import ensure_datetime


def parse_board_metadata(kanban_file: Path) -> tuple[str, Metadata]:
    try:
        content, metadata = read_frontmatter_file(kanban_file)
        board_name = metadata.get("name", kanban_file.parent.name)
        content_title = extract_title_from_content(content, board_name)
        return content_title, metadata
    except Exception as e:
        raise ParseError(f"Failed to parse board metadata from {kanban_file}: {e}")


def parse_item_metadata(item_file: Path) -> tuple[str, str, Metadata]:
    try:
        content, metadata = read_frontmatter_file(item_file)
        title = metadata.get("title", item_file.stem)
        content_title = extract_title_from_content(content, title)
        return content_title, content, metadata
    except Exception as e:
        raise ParseError(f"Failed to parse item metadata from {item_file}: {e}")


def parse_column_metadata(column_file: Path) -> Optional[Metadata]:
    try:
        if not column_file.exists():
            return None
        _, metadata = read_frontmatter_file(column_file)
        return metadata
    except Exception:
        return None


def save_board_metadata(kanban_file: Path, board_name: str, metadata: Metadata) -> None:
    try:
        content_lines = [f"# {board_name}", ""]
        yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        full_content = f"---\n{yaml_str}---\n\n{'\n'.join(content_lines)}"

        with open(kanban_file, "w", encoding="utf-8") as f:
            f.write(full_content)
    except Exception as e:
        raise ParseError(f"Failed to save board metadata to {kanban_file}: {e}")


def save_item_with_metadata(
    item_file: Path, title: str, content: str, metadata: Metadata
) -> None:
    try:
        updated_content = ensure_title_header(content, title)
        write_frontmatter_file(item_file, updated_content, metadata)
    except Exception as e:
        raise ParseError(f"Failed to save item to {item_file}: {e}")


def save_column_metadata(
    column_file: Path, column_name: str, metadata: Metadata
) -> None:
    try:
        content = f"# {column_name}\n\nColumn metadata and configuration."
        write_frontmatter_file(column_file, content, metadata)
    except Exception as e:
        raise ParseError(f"Failed to save column metadata to {column_file}: {e}")
