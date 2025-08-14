import frontmatter
from pathlib import Path
from datetime import datetime
import re

from ..models.board import Board
from ..models.column import Column
from ..models.item import Item
from ..models.parent import Parent


class BoardStorage:
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

        metadata = post.metadata.get("metadata", post.metadata)

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
            description=metadata.get("description", ""),
            created_at=metadata.get("created_at", datetime.now()),
            updated_at=metadata.get("updated_at", datetime.now()),
        )

        self._parse_columns_from_content(board, post.content, kanban_file.parent)

        for parent_data in metadata.get("parents", []):
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
        columns_data = []
        
        for folder_path in board_dir.iterdir():
            if folder_path.is_dir() and folder_path.name != "items":
                column_name = folder_path.name.replace("-", " ").replace("_", " ").title()
                column_id = self._generate_id_from_name(column_name)
                position = None
                
                # Check for column.md metadata file
                column_md_path = folder_path / "column.md"
                if column_md_path.exists():
                    try:
                        with open(column_md_path, "r", encoding="utf-8") as f:
                            post = frontmatter.load(f)
                        
                        metadata = post.metadata.get("metadata", post.metadata)
                        column_id = metadata.get("id", column_id)
                        position = metadata.get("position")
                    except Exception:
                        # If column.md can't be read, use defaults
                        pass
                
                columns_data.append({
                    'id': column_id,
                    'name': column_name,
                    'position': position,
                    'folder_path': folder_path
                })
        
        # Sort columns by position (None positions go last), then by name
        def sort_key(col):
            if col['position'] is None:
                return (1, col['name'])  # Sort by name for None positions
            return (0, col['position'])  # Sort by position for specified positions
        
        columns_data.sort(key=sort_key)
        
        # Create Column objects
        for col_data in columns_data:
            column = Column(
                id=col_data['id'],
                name=col_data['name'],
                position=col_data['position'] if col_data['position'] is not None else len(board.columns)
            )
            board.columns.append(column)
            self._load_items_for_column(board, column, col_data['folder_path'])

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

        item_metadata = post.metadata.get("metadata", post.metadata)
        item_id = item_metadata.get("id")
        if not item_id:
            item_id = self._generate_id_from_name(item_metadata.get("title", item_file.stem))
        
        # Extract title from first # heading in content, fallback to metadata or filename
        title = item_metadata.get("title", item_file.stem)
        content_lines = post.content.strip().split("\n")
        for line in content_lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()  # Remove "# " prefix
                break
        
        return Item(
            id=item_id,
            title=title,
            description=post.content.strip(),
            column_id=column_id,
            parent_id=item_metadata.get("parent_id"),
            created_at=item_metadata.get("created_at", datetime.now()),
            updated_at=item_metadata.get("updated_at", datetime.now()),
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
            "name": board.name,
            "created_at": board.created_at,
            "updated_at": board.updated_at,
            "board_metadata": board.metadata,
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

        post = frontmatter.Post(content="\n".join(content_lines), metadata=board_data)

        with open(kanban_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def save_column_with_items(self, board: Board, column: Column) -> None:
        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name
        column_dir.mkdir(exist_ok=True)

        # Save column metadata if position is explicitly set or column has custom id
        needs_metadata = (
            column.position != 0 or  # Has explicit position
            column.id != self._generate_id_from_name(column.name)  # Has custom id
        )
        
        if needs_metadata:
            self._save_column_metadata(column_dir, column)

        # Save items directly in the column folder
        for item in column.items:
            item_filename = self._get_unique_filename(column_dir, item)
            self.save_item_with_title(column_dir, item, item_filename)

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

        item_metadata = {
            "id": item.id,
            "title": item.title,
            "column_id": item.column_id,
            "parent_id": item.parent_id,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

        description = item.description or ""
        description_lines = description.split("\n")
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
            content_lines = [f"# {item.title}", "", description]

        post = frontmatter.Post(
            content="\n".join(content_lines), metadata=item_metadata
        )

        with open(item_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def _save_column_metadata(self, column_dir: Path, column: Column) -> None:
        """Save column metadata to column.md file"""
        column_md_path = column_dir / "column.md"
        
        column_metadata = {
            "id": column.id,
            "position": column.position,
            "created_at": column.created_at,
            "updated_at": column.updated_at,
        }
        
        if column.limit is not None:
            column_metadata["limit"] = column.limit
        
        content = f"# {column.name}\n\nColumn metadata and configuration."
        
        post = frontmatter.Post(content=content, metadata=column_metadata)
        
        with open(column_md_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def delete_item_from_column(self, board: Board, item: Item) -> bool:
        column = None
        for col in board.columns:
            if col.id == item.column_id:
                column = col
                break

        if not column:
            return False

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
        self, board: Board, item: Item, old_column_id: str, new_column_id: str
    ) -> bool:
        old_column = None
        new_column = None

        for col in board.columns:
            if col.id == old_column_id:
                old_column = col
            elif col.id == new_column_id:
                new_column = col

        if not old_column or not new_column:
            return False

        board_dir = self._get_board_directory(board)

        old_column_safe_name = self._get_safe_name(old_column.name)
        old_column_dir = board_dir / old_column_safe_name

        # Find the item file by scanning metadata for the ID
        old_item_file = self._find_item_file_by_id(old_column_dir, item.id)

        new_column_safe_name = self._get_safe_name(new_column.name)
        new_column_dir = board_dir / new_column_safe_name
        new_column_dir.mkdir(exist_ok=True)  # Ensure target directory exists

        if old_item_file and old_item_file.exists():
            item.column_id = new_column_id
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
        safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        return safe_name or 'unnamed'
    
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

                item_metadata = post.metadata.get("metadata", post.metadata)
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

            existing_metadata = post.metadata.get("metadata", post.metadata)
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

                existing_metadata = post.metadata.get("metadata", post.metadata)
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
        board = Board(
            name=name,
            description="Welcome to MKanban! This is a sample board to help you get started. "
            "You can edit items by pressing 'i', create new items with 'o', "
            "and delete items with 'd'. Use vim motions (h/j/k/l) to navigate.",
        )

        todo_col = board.add_column("To Do", 0)
        progress_col = board.add_column("In Progress", 1)
        review_col = board.add_column("Review", 2)
        done_col = board.add_column("Done", 3)

        item1 = todo_col.add_item("Learn keyboard shortcuts", todo_col.id)
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

        item2 = todo_col.add_item("Explore markdown files", todo_col.id)
        item2.description = (
            "Your boards are stored as markdown files in the data/boards/ directory.\n\n"
            "Each board has its own folder with:\n"
            "- kanban.md: Board structure and metadata\n"
            "- Column folders with column.md files\n"
            "- Item files in items/ subfolders"
        )

        item3 = progress_col.add_item("Create your first board", progress_col.id)
        item3.description = (
            "Try creating a new board by:\n"
            "1. Exiting MKanban (press 'q')\n"
            "2. Creating a new markdown file in data/boards/\n"
            "3. Or modify this sample board to suit your needs"
        )

        item4 = review_col.add_item("Organize with parents", review_col.id)
        item4.description = (
            "Parents help organize related items across columns.\n\n"
            "Toggle parent grouping with 'p' to see items grouped by their parent.\n"
            "Items with the same parent are shown together regardless of column."
        )

        item5 = done_col.add_item("Install MKanban", done_col.id)
        item5.description = "Great! You've successfully installed and launched MKanban."

        return board
