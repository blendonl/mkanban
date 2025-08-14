import click
import frontmatter
import yaml
from pathlib import Path
from datetime import datetime
import re

from ..models.board import Board
from ..models.column import Column
from ..models.item import Item
from ..models.parent import Parent


class MarkdownStorage:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.boards_dir = self.data_dir / "boards"
        self.boards_dir.mkdir(exist_ok=True)

    def load_boards(self) -> list[Board]:
        boards: list[Board] = []

        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / "kanban.md"
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board:
                        boards.append(board)

        return boards

    def load_board_from_file(self, kanban_file: Path) -> Board | None:
        if not kanban_file.exists():
            return None

        with open(kanban_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        metadata = post.metadata

        # Extract name from content (# heading) or fallback to metadata or folder name
        board_name = metadata.get("name", kanban_file.parent.name)
        content_lines = post.content.strip().split("\n")
        for line in content_lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                board_name = stripped[2:].strip()
                break
        
        board = Board(
            id=metadata.get("id", kanban_file.parent.name),
            name=board_name,
            description=metadata.get("description") or "",
            created_at=metadata.get("created_at", datetime.now()),
            updated_at=metadata.get("updated_at", datetime.now()),
            file_path=kanban_file,
        )

        self._parse_columns_from_content(board, post.content, kanban_file.parent)

        for parent_data in metadata.get("parents") or []:
            parent = Parent(
                id=parent_data["id"],
                name=parent_data["name"],
                description=parent_data.get("description", ""),
                color=parent_data.get("color", "blue"),
                created_at=parent_data.get("created_at", datetime.now()),
                updated_at=parent_data.get("updated_at", datetime.now()),
            )
            board.parents.append(parent)

        return board

    def _parse_columns_from_content(
        self, board: Board, content: str, board_dir: Path
    ) -> None:
        # Load columns directly from folders in the board directory
        position = 0
        for folder_path in sorted(board_dir.iterdir()):
            if folder_path.is_dir() and folder_path.name != "items":
                column_name = folder_path.name.replace("-", " ").replace("_", " ").title()
                column_id = self._generate_id_from_name(column_name)
                
                column = Column(
                    id=column_id,
                    name=column_name,
                    position=position,
                    file_path=str(folder_path)
                )
                board.columns.append(column)
                self._load_items_for_column(board, column, folder_path)
                position += 1

    def load_board(self, board_id: str) -> Board | None:
        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / "kanban.md"
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board and board.id == board_id:
                        return board

        return None

    def load_board_by_name(self, board_name: str) -> Board | None:
        boards = self.load_boards()
        for board in boards:
            if board.name.lower() == board_name.lower():
                return board

        return None


    def _load_items_for_column(
        self, board: Board, column: Column, column_dir: Path
    ) -> None:
        # Load all .md files directly from the column folder
        for item_file in column_dir.glob("*.md"):
            if item_file.name != "column.md":  # Skip column.md if it exists
                item = self.load_item_from_title_file(item_file, column.id)
                if item:
                    column.items.append(item)

    def load_item_from_title_file(self, item_file: Path, column_id: str) -> Item | None:
        if not item_file.exists():
            return None

        with open(item_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        item_metadata = post.metadata

        item_id = item_metadata.get("id")
        if not item_id:
            item_id = item_file.stem

        # Check if the item's metadata column_id matches the expected column
        # If not, this item is in the wrong directory and should be skipped
        item_metadata_column_id = item_metadata.get("column_id")
        if item_metadata_column_id and item_metadata_column_id != column_id:
            # Item is in wrong directory, skip loading it here
            return None

        # Extract title from first # heading in content, fallback to metadata or filename
        title = item_metadata.get("title", item_file.stem)
        content_lines = post.content.strip().split("\n")
        for line in content_lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()  # Remove "# " prefix
                break

        # Use the actual column_id from metadata if available, otherwise use the passed column_id
        actual_column_id = item_metadata_column_id or column_id

        return Item(
            id=item_id,
            column_id=actual_column_id,
            title=title,
            description=post.content.strip(),
            parent_id=item_metadata.get("parent_id"),
            created_at=item_metadata.get("created_at", datetime.now()),
            updated_at=item_metadata.get("updated_at", datetime.now()),
            file_path=str(item_file),
        )

    def save_boards(self, boards: list[Board]) -> None:
        for board in boards:
            self.save_board(board)

    def save_board(self, board: Board) -> None:
        board_dir = self._get_board_directory(board)
        board_dir.mkdir(exist_ok=True)

        kanban_file = board_dir / "kanban.md"

        board_data = {
            "id": board.id,
            "kanban-plugin": "board",
            "created_at": board.created_at,
            "updated_at": board.updated_at,
            "parents": [],
        }

        for parent in board.parents:
            parent_data = {
                "id": parent.id,
                "name": parent.name,
                "description": parent.description,
                "color": parent.color,
                "created_at": parent.created_at,
                "updated_at": parent.updated_at,
            }
            board_data["parents"].append(parent_data)

        content_lines = [f"# {board.name}", ""]

        for column in sorted(board.columns, key=lambda c: c.position):
            self.save_column_with_items(board, column)

        yaml_str = yaml.dump(board_data, default_flow_style=False, sort_keys=False)
        full_content = f"---\n{yaml_str}---\n\n{'\n'.join(content_lines)}"

        with open(kanban_file, "w", encoding="utf-8") as f:
            f.write(full_content)

    def save_column_with_items(self, board: Board, column: Column) -> None:
        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name
        column_dir.mkdir(exist_ok=True)

        # Get current item IDs that should be in this column
        current_item_ids = {item.id for item in column.items}

        # Save items directly in the column folder
        for item in column.items:
            item_filename = self._get_unique_filename(column_dir, item)
            self.save_item_with_title(column_dir, item, item_filename)

        # Remove any .md files that don't belong to current column items
        # Also remove duplicate files for the same item ID
        item_id_to_files = {}
        for item_file in column_dir.glob("*.md"):
            if item_file.name != "column.md":  # Skip column.md if it exists
                try:
                    with open(item_file, "r", encoding="utf-8") as f:
                        post = frontmatter.load(f)
                    
                    item_metadata = post.metadata
                    file_item_id = item_metadata.get("id")
                    
                    if file_item_id:
                        # If this file's item ID is not in current column items, delete it
                        if file_item_id not in current_item_ids:
                            item_file.unlink()
                        else:
                            # Track files by item ID to handle duplicates
                            if file_item_id not in item_id_to_files:
                                item_id_to_files[file_item_id] = []
                            item_id_to_files[file_item_id].append(item_file)
                except Exception:
                    # Skip files that can't be read or processed
                    continue
        
        # Remove duplicate files for the same item ID (keep the most recently modified)
        for item_id, files in item_id_to_files.items():
            if len(files) > 1:
                # Sort by modification time, keep the newest
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                # Delete all but the newest file
                for old_file in files[1:]:
                    old_file.unlink()

    def save_item_with_title(
        self, column_dir: Path, item: Item, item_filename: str
    ) -> None:
        # Generate filename from current title
        new_filename = self._get_title_filename(item.title)
        old_item_file = column_dir / f"{item_filename}.md"
        new_item_file = column_dir / f"{new_filename}.md"

        # Check if we need to rename the file
        if old_item_file.exists() and item_filename != new_filename:
            # Make sure the new filename doesn't conflict with an existing file
            if new_item_file.exists() and new_item_file != old_item_file:
                # If conflict exists, find a unique name
                counter = 1
                while new_item_file.exists():
                    test_filename = f"{new_filename}_{counter}"
                    new_item_file = column_dir / f"{test_filename}.md"
                    counter += 1
                    if counter > 100:  # Safety valve
                        new_filename = f"{new_filename}_{item.id[:8]}"
                        new_item_file = column_dir / f"{new_filename}.md"
                        break
                new_filename = new_item_file.stem

            # Rename the file
            try:
                old_item_file.rename(new_item_file)
            except Exception:
                # If rename fails, use the new file path anyway
                pass

        # Use the determined filename
        item_file = column_dir / f"{new_filename}.md"

        # New metadata to be written
        item_metadata = {
            "id": item.id,
            "title": item.title,
            "column_id": item.column_id,
            "parent_id": item.parent_id,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

        # Check if file already exists and has content
        existing_content = ""
        if item_file.exists():
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
                existing_content = post.content

                # Create new post with updated metadata and existing content
                new_post = frontmatter.Post(existing_content, **item_metadata)

                # Handle title header in content
                description_lines = existing_content.split("\n")
                has_title_header = False

                # Check if description already has a title header
                for line in description_lines:
                    stripped = line.strip()
                    if stripped.startswith("# "):
                        has_title_header = True
                        break

                if has_title_header:
                    # Update the existing title header to match current title
                    updated_lines = []
                    title_updated = False
                    for line in description_lines:
                        stripped = line.strip()
                        if stripped.startswith("# ") and not title_updated:
                            updated_lines.append(f"# {item.title}")
                            title_updated = True
                        else:
                            updated_lines.append(line)
                    new_post.content = "\n".join(updated_lines)
                else:
                    if existing_content:
                        new_post.content = f"# {item.title}\n\n{existing_content}"
                    else:
                        new_post.content = f"# {item.title}"

                # Write the post with frontmatter handling the metadata replacement
                with open(item_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(new_post))
                return

            except Exception:
                # If we can't read the existing file, fall back to description
                existing_content = item.description or ""
        else:
            existing_content = item.description or ""

        # Fallback for new files or when frontmatter reading fails
        description_lines = existing_content.split("\n")
        has_title_header = False

        # Check if description already has a title header
        for line in description_lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                has_title_header = True
                break

        if has_title_header:
            # Update the existing title header to match current title
            updated_lines = []
            title_updated = False
            for line in description_lines:
                stripped = line.strip()
                if stripped.startswith("# ") and not title_updated:
                    updated_lines.append(f"# {item.title}")
                    title_updated = True
                else:
                    updated_lines.append(line)
            content_lines = updated_lines
        else:
            content_lines = (
                [f"# {item.title}", "", existing_content]
                if existing_content
                else [f"# {item.title}"]
            )

        yaml_str = yaml.dump(item_metadata, default_flow_style=False, sort_keys=False)

        content_to_write = content_lines
        if content_lines and content_lines[0].strip().startswith("---"):
            content_to_write = content_lines[7:]
        full_content = f"---\n{yaml_str}---\n\n{'\n'.join(content_to_write)}"

        with open(item_file, "w", encoding="utf-8") as f:
            f.write(full_content)

    def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name

        # Find the item file by scanning metadata for the ID
        item_file = self._find_item_file_by_id(column_dir, item.id)
        if item_file and item_file.exists():
            item_file.unlink()
            return True
        return False

    def move_item_between_columns(
        self, board: Board, item: Item, old_column: Column, new_column: Column
    ) -> bool:
        board_dir = self._get_board_directory(board)

        old_column_safe_name = self._get_safe_name(old_column.name)
        old_column_dir = board_dir / old_column_safe_name

        # Find the item file by scanning metadata for the ID
        old_item_file = self._find_item_file_by_id(old_column_dir, item.id)

        new_column_safe_name = self._get_safe_name(new_column.name)
        new_column_dir = board_dir / new_column_safe_name
        new_column_dir.mkdir(exist_ok=True)  # Ensure target directory exists

        if old_item_file and old_item_file.exists():
            item.updated_at = datetime.now()

            # Get unique filename for the new location
            new_item_filename = self._get_unique_filename(new_column_dir, item)
            self.save_item_with_title(new_column_dir, item, new_item_filename)

            old_item_file.unlink()

            return True

        return False

    def _get_board_directory(self, board: Board) -> Path:
        safe_name = self._get_safe_name(board.name)
        return self.boards_dir / safe_name

    def _generate_id_from_name(self, name: str) -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        safe_name = re.sub(r"\s+", "_", safe_name.strip())
        return safe_name or "unnamed"

    def _get_safe_name(self, name: str) -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        safe_name = re.sub(r"\s+", "-", safe_name.strip())
        return safe_name or "unnamed"

    def _get_title_filename(self, title: str) -> str:
        import re

        safe_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
        safe_title = re.sub(r"\s+", "_", safe_title.strip())
        return safe_title or "unnamed"

    def _find_item_file_by_id(self, column_dir: Path, item_id: str) -> Path | None:
        if not column_dir.exists():
            return None

        for item_file in column_dir.glob("*.md"):
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)

                item_metadata = post.metadata
                if item_metadata.get("id") == item_id:
                    return item_file
            except Exception:
                # Skip files that can't be read
                continue

        return None

    def _get_unique_filename(self, column_dir: Path, item: Item) -> str:
        base_filename = self._get_title_filename(item.title)
        potential_file = column_dir / f"{base_filename}.md"

        if not potential_file.exists():
            return base_filename

        try:
            with open(potential_file, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            existing_metadata = post.metadata
            if existing_metadata.get("id") == item.id:
                # Same item, can reuse the filename
                return base_filename
        except Exception:
            pass

        counter = 1
        while True:
            test_filename = f"{base_filename}_{counter}"
            test_file = column_dir / f"{test_filename}.md"

            if not test_file.exists():
                return test_filename

            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)

                existing_metadata = post.metadata
                if existing_metadata.get("id") == item.id:
                    return test_filename
            except Exception:
                pass

            counter += 1
            if counter > 100:  # Safety valve
                return f"{base_filename}_{item.id[:8]}"

    def list_board_names(self) -> list[str]:
        boards = self.load_boards()
        return [board.name for board in boards]

    def create_sample_board(self, name: str = "Sample Board") -> Board:
        board = Board(name=name)

        todo_col = board.add_column("To Do", 0)
        progress_col = board.add_column("In Progress", 1)
        review_col = board.add_column("Review", 2)
        done_col = board.add_column("Done", 3)

        item1 = todo_col.add_item("Learn keyboard shortcuts")
        item1.description = (
            "Press 'g?' to view help dialog with all available shortcuts.\n\n"
            "Basic navigation:\n"
            "- h/j/k/l: Navigate left/down/up/right\n"
            "- o: Create new item\n"
            "- i: Edit selected item\n"
            "- d: Delete selected item\n"
            "- p: Toggle parent grouping\n"
            "- H/L: Move item between columns"
        )

        item2 = todo_col.add_item("Explore markdown files")
        item2.description = (
            "Your boards are stored as markdown files in the data/boards/ directory.\n\n"
            "Each board has its own folder with:\n"
            "- kanban.md: Board structure and metadata\n"
            "- Column folders with column.md files\n"
            "- Item files in items/ subfolders"
        )

        item3 = progress_col.add_item("Create your first board")
        item3.description = (
            "Try creating a new board by:\n"
            "1. Exiting MKanban (press 'q')\n"
            "2. Creating a new markdown file in data/boards/\n"
            "3. Or modify this sample board to suit your needs"
        )

        item4 = review_col.add_item("Organize with parents")
        item4.description = (
            "Parents help organize related items across columns.\n\n"
            "Toggle parent grouping with 'p' to see items grouped by their parent.\n"
            "Items with the same parent are shown together regardless of column."
        )

        item5 = done_col.add_item("Install MKanban")
        item5.description = "Great! You've successfully installed and launched MKanban."

        return board
