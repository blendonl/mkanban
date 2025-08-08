import frontmatter
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

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

    def load_boards(self) -> List[Board]:
        boards = []

        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / "kanban.md"
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board:
                        boards.append(board)

        return boards

    def load_board_from_file(self, kanban_file: Path) -> Optional[Board]:
        if not kanban_file.exists():
            return None

        with open(kanban_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        metadata = post.metadata.get("metadata", post.metadata)

        board = Board(
            id=metadata["id"],
            name=metadata["name"],
            description=metadata.get("description", ""),
            created_at=metadata.get("created_at", datetime.now()),
            updated_at=metadata.get("updated_at", datetime.now()),
            metadata=metadata.get("board_metadata", {}),
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
                metadata=parent_data.get("metadata", {}),
            )
            board.parents.append(parent)

        return board

    def _parse_columns_from_content(
        self, board: Board, content: str, board_dir: Path
    ) -> None:
        import re

        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            column_match = re.match(r"^- \[(.+?)\]\((.+?)/column\.md\)$", line)
            if column_match:
                column_name = column_match.group(1).strip()
                column_folder = column_match.group(2).strip()

                column_file = board_dir / column_folder / "column.md"
                if column_file.exists():
                    column = self.load_column_from_file(
                        column_file, column_name, len(board.columns)
                    )
                    if column:
                        board.columns.append(column)
                        self._load_items_for_column(
                            board, column, board_dir / column_folder
                        )

    def load_board(self, board_id: str) -> Optional[Board]:
        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                kanban_file = board_dir / "kanban.md"
                if kanban_file.exists():
                    board = self.load_board_from_file(kanban_file)
                    if board and board.id == board_id:
                        return board

        return None

    def load_board_by_name(self, board_name: str) -> Optional[Board]:
        boards = self.load_boards()
        for board in boards:
            if board.name.lower() == board_name.lower():
                return board
        return None

    def load_column_from_file(
        self, column_file: Path, column_name: str, position: int
    ) -> Optional[Column]:
        if not column_file.exists():
            return None

        with open(column_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        metadata = post.metadata.get("metadata", post.metadata)

        column = Column(
            id=metadata.get("id", str(uuid4())), name=column_name, position=position
        )
        return column

    def _load_items_for_column(
        self, board: Board, column: Column, column_dir: Path
    ) -> None:
        import re

        column_file = column_dir / "column.md"
        if column_file.exists():
            with open(column_file, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            lines = post.content.split("\n")
            for line in lines:
                line = line.strip()

                item_match = re.match(
                    r"^- \[(.+?)\]\(items/(.+?)\.md\)(?:\s*\*\((.+?)\)\*)?$", line
                )
                if item_match:
                    item_uuid = item_match.group(2).strip()
                    parent_name = item_match.group(3) if item_match.group(3) else None

                    item_file = column_dir / "items" / f"{item_uuid}.md"
                    if item_file.exists():
                        item = self.load_item_from_uuid_file(item_file, column.id)
                        if item:
                            if parent_name:
                                for parent in board.parents:
                                    if parent.name == parent_name:
                                        item.parent_id = parent.id
                                        break

                            column.items.append(item)

    def load_item_from_uuid_file(
        self, item_file: Path, column_id: str
    ) -> Optional[Item]:
        if not item_file.exists():
            return None

        with open(item_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        item_metadata = post.metadata.get("metadata", post.metadata)
        return Item(
            id=item_metadata.get("id", item_file.stem),
            title=item_metadata["title"],
            description=post.content.strip(),
            column_id=column_id,
            parent_id=item_metadata.get("parent_id"),
            created_at=item_metadata.get("created_at", datetime.now()),
            updated_at=item_metadata.get("updated_at", datetime.now()),
            metadata=item_metadata.get("metadata", {}),
        )

    def save_boards(self, boards: List[Board]) -> None:
        for board in boards:
            self.save_board(board)

    def save_board(self, board: Board) -> None:
        board_dir = self._get_board_directory(board)
        board_dir.mkdir(exist_ok=True)

        kanban_file = board_dir / "kanban.md"

        board_data = {
            "id": board.id,
            "name": board.name,
            "description": board.description,
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
                "metadata": parent.metadata,
            }
            board_data["parents"].append(parent_data)

        content_lines = [f"# {board.name}", "", board.description, "", "## Columns", ""]

        for column in sorted(board.columns, key=lambda c: c.position):
            column_safe_name = self._get_safe_name(column.name)
            content_lines.append(f"- [{column.name}]({column_safe_name}/column.md)")

            self.save_column_with_items(board, column)

        post = frontmatter.Post(content="\n".join(content_lines), metadata=board_data)

        with open(kanban_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def save_column_with_items(self, board: Board, column: Column) -> None:
        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name
        column_dir.mkdir(exist_ok=True)

        items_dir = column_dir / "items"
        items_dir.mkdir(exist_ok=True)

        column_data = {
            "id": column.id,
            "name": column.name,
            "position": column.position,
        }

        content_lines = [f"# {column.name}", "", "## Items", ""]

        if not column.items:
            content_lines.append("*No items*")
        else:
            for item in column.items:
                item_uuid = item.id if item.id else str(uuid4())
                item_link = f"[{item.title}](items/{item_uuid}.md)"

                if item.parent_id:
                    parent_name = "Unknown Parent"
                    for parent in board.parents:
                        if parent.id == item.parent_id:
                            parent_name = parent.name
                            break
                    item_link += f" *({parent_name})*"

                content_lines.append(f"- {item_link}")

                # Save individual item file
                self.save_item_with_uuid(items_dir, item, item_uuid)

        post = frontmatter.Post(content="\n".join(content_lines), metadata=column_data)

        column_file = column_dir / "column.md"
        with open(column_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def save_item_with_uuid(self, items_dir: Path, item: Item, item_uuid: str) -> None:
        item_file = items_dir / f"{item_uuid}.md"

        item_metadata = {
            "id": item.id,
            "title": item.title,
            "column_id": item.column_id,
            "parent_id": item.parent_id,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "metadata": item.metadata,
        }

        description = item.description or ""
        description_lines = description.split("\n")
        has_title_header = False

        if description_lines and description_lines[0].strip().startswith(
            f"# {item.title}"
        ):
            has_title_header = True

        if has_title_header:
            content_lines = [description]
        else:
            content_lines = [f"# {item.title}", "", description]

        post = frontmatter.Post(
            content="\n".join(content_lines), metadata=item_metadata
        )

        with open(item_file, "w", encoding="utf-8") as f:
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
        items_dir = column_dir / "items"
        item_file = items_dir / f"{item.id}.md"

        if item_file.exists():
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
        old_items_dir = old_column_dir / "items"
        old_item_file = old_items_dir / f"{item.id}.md"

        new_column_safe_name = self._get_safe_name(new_column.name)
        new_column_dir = board_dir / new_column_safe_name
        new_items_dir = new_column_dir / "items"
        new_items_dir.mkdir(exist_ok=True)  # Ensure target directory exists

        if old_item_file.exists():
            item.column_id = new_column_id
            item.updated_at = datetime.now()

            self.save_item_with_uuid(new_items_dir, item, item.id)

            old_item_file.unlink()

            return True

        return False

    def _get_board_directory(self, board: Board) -> Path:
        safe_name = self._get_safe_name(board.name)
        return self.boards_dir / safe_name

    def _get_safe_name(self, name: str) -> str:
        import re

        safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        safe_name = re.sub(r"\s+", "-", safe_name.strip())
        return safe_name or "unnamed"

    def list_board_names(self) -> List[str]:
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
