"""Markdown storage implementation for boards with separate item files."""

import frontmatter
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..models import Board, Column, Item, Parent


class MarkdownStorage:
    """Handles saving and loading boards with separate item files."""

    def __init__(self, data_dir: Path):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.boards_dir = self.data_dir / "boards"
        self.boards_dir.mkdir(exist_ok=True)

    def load_boards(self) -> List[Board]:
        """Load all boards from board folders."""
        boards = []

        # Load from board folders (new structure)
        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                board_file = board_dir / "board.md"
                if board_file.exists():
                    board = self.load_board_from_file(board_file)
                    if board:
                        boards.append(board)

        return boards

    def load_board_from_file(self, board_file: Path) -> Optional[Board]:
        """Load a single board from its markdown file."""
        if not board_file.exists():
            return None

        with open(board_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Handle frontmatter structure
        metadata = post.metadata.get('metadata', post.metadata)

        board = Board(
            id=metadata['id'],
            name=metadata['name'],
            description=metadata.get('description', ''),
            created_at=metadata.get('created_at', datetime.now()),
            updated_at=metadata.get('updated_at', datetime.now()),
            metadata=metadata.get('board_metadata', {})
        )

        # Load columns
        for col_data in metadata.get('columns', []):
            column = Column(
                id=col_data['id'],
                name=col_data['name'],
                position=col_data['position']
            )
            board.columns.append(column)

        # Load parents
        for parent_data in metadata.get('parents', []):
            parent = Parent(
                id=parent_data['id'],
                name=parent_data['name'],
                description=parent_data.get('description', ''),
                color=parent_data.get('color', 'blue'),
                created_at=parent_data.get('created_at', datetime.now()),
                updated_at=parent_data.get('updated_at', datetime.now()),
                metadata=parent_data.get('metadata', {})
            )
            board.parents.append(parent)

        # Parse items from markdown content
        self._parse_items_from_content(board, post.content)

        return board

    def _parse_items_from_content(self, board: Board, content: str) -> None:
        """Parse items from markdown content with links."""
        import re

        current_column = None
        lines = content.split('\n')
        board_dir = self._get_board_directory(board)

        for line in lines:
            line = line.strip()

            # Find column headers (## Column Name)
            column_match = re.match(r'^## (.+)$', line)
            if column_match:
                column_name = column_match.group(1).strip()
                # Find matching column
                current_column = None
                for col in board.columns:
                    if col.name == column_name:
                        current_column = col
                        break
                continue

            # Find item links - support multiple path formats
            # New format: column-folder/item.md
            # Legacy formats: ../items/item.md, items/item.md
            item_match = re.match(
                r'^- \[(.+?)\]\((.+?)/(.+?)\.md\)(?:\s*\*\((.+?)\)\*)?', line)
            if item_match and current_column:
                title = item_match.group(1)
                folder_path = item_match.group(2)
                item_id = item_match.group(3)
                parent_name = item_match.group(
                    4) if item_match.group(4) else None

                # Load the item file from appropriate location
                item = None
                if folder_path in ['../items', 'items']:
                    # Legacy format
                    item = self.load_item(item_id)
                else:
                    # New format - item in column folder
                    item = self.load_item_from_column(
                        board, current_column, item_id)

                if item:
                    item.column_id = current_column.id

                    # Find parent ID by name
                    if parent_name:
                        for parent in board.parents:
                            if parent.name == parent_name:
                                item.parent_id = parent.id
                                break

                    board.items.append(item)

    def load_board(self, board_id: str) -> Optional[Board]:
        """Load a specific board by ID."""
        # Try to find board in folders first (new structure)
        for board_dir in self.boards_dir.iterdir():
            if board_dir.is_dir():
                board_file = board_dir / "board.md"
                if board_file.exists():
                    board = self.load_board_from_file(board_file)
                    if board and board.id == board_id:
                        return board

        return None

    def load_board_by_name(self, board_name: str) -> Optional[Board]:
        """Load a specific board by name."""
        boards = self.load_boards()
        for board in boards:
            if board.name.lower() == board_name.lower():
                return board
        return None

    def load_item(self, item_id: str) -> Optional[Item]:
        """Load an item from its individual markdown file (legacy location)."""
        # Legacy method - items are now stored in column folders
        return None

    def load_item_from_column(self, board: Board, column: Column, item_id: str) -> Optional[Item]:
        """Load an item from a column folder."""
        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name
        item_file = column_dir / f"{item_id}.md"

        if not item_file.exists():
            return None

        with open(item_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Handle frontmatter structure - it may add a 'metadata' wrapper
        item_metadata = post.metadata.get('metadata', post.metadata)
        return Item(
            id=item_metadata['id'],
            title=item_metadata['title'],
            description=post.content.strip(),
            column_id=item_metadata['column_id'],
            parent_id=item_metadata.get('parent_id'),
            created_at=item_metadata.get('created_at', datetime.now()),
            updated_at=item_metadata.get('updated_at', datetime.now()),
            metadata=item_metadata.get('metadata', {})
        )

    def save_boards(self, boards: List[Board]) -> None:
        """Save each board to its own file."""
        for board in boards:
            self.save_board(board)

    def save_board(self, board: Board) -> None:
        """Save a single board to its own folder structure."""
        # Create board directory
        board_dir = self._get_board_directory(board)
        board_dir.mkdir(exist_ok=True)

        # Board file is always board.md inside the board directory
        board_file = board_dir / "board.md"

        # Prepare board metadata
        board_data = {
            'id': board.id,
            'name': board.name,
            'description': board.description,
            'created_at': board.created_at,
            'updated_at': board.updated_at,
            'board_metadata': board.metadata,
            'columns': [],
            'parents': []
        }

        # Add columns
        for column in sorted(board.columns, key=lambda c: c.position):
            col_data = {
                'id': column.id,
                'name': column.name,
                'position': column.position
            }
            board_data['columns'].append(col_data)

        # Add parents
        for parent in board.parents:
            parent_data = {
                'id': parent.id,
                'name': parent.name,
                'description': parent.description,
                'color': parent.color,
                'created_at': parent.created_at,
                'updated_at': parent.updated_at,
                'metadata': parent.metadata
            }
            board_data['parents'].append(parent_data)

        # Generate markdown content with item links
        content_lines = [
            f"# {board.name}",
            "",
            board.description,
            ""
        ]

        # Add columns with item links
        for column in sorted(board.columns, key=lambda c: c.position):
            # Create column directory
            column_safe_name = self._get_safe_name(column.name)
            column_dir = board_dir / column_safe_name
            column_dir.mkdir(exist_ok=True)

            content_lines.extend([
                f"## {column.name}",
                ""
            ])

            # Get items for this column
            column_items = board.get_column_items(column.id)

            if not column_items:
                content_lines.append("*No items*")
            else:
                for item in column_items:
                    # Create markdown link to item file in column folder
                    item_link = f"[{item.title}]({
                        column_safe_name}/{item.id}.md)"

                    # Add parent indicator if present
                    if item.parent_id:
                        parent_name = "Unknown Parent"
                        for parent in board.parents:
                            if parent.id == item.parent_id:
                                parent_name = parent.name
                                break
                        item_link += f" *({parent_name})*"

                    content_lines.append(f"- {item_link}")

            content_lines.append("")

        # Save individual item files in their column folders
        for item in board.items:
            self.save_item_in_column(board, item)

        # Save board file
        post = frontmatter.Post(content="\n".join(
            content_lines), metadata=board_data)

        with open(board_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def save_item(self, item: Item) -> None:
        """Save an item to its individual markdown file (legacy location)."""
        # Legacy method - items are now saved in column folders via save_item_in_column
        pass

    def delete_item(self, item_id: str) -> bool:
        """Delete an item from legacy location (backwards compatibility)."""
        # Legacy method - items are now deleted via delete_item_from_column
        return False

    def save_item_in_column(self, board: Board, item: Item) -> None:
        """Save an item to its column folder."""
        # Find the column for this item
        column = None
        for col in board.columns:
            if col.id == item.column_id:
                column = col
                break

        if not column:
            return

        board_dir = self._get_board_directory(board)
        column_safe_name = self._get_safe_name(column.name)
        column_dir = board_dir / column_safe_name
        column_dir.mkdir(exist_ok=True)

        item_file = column_dir / f"{item.id}.md"

        item_metadata = {
            'id': item.id,
            'title': item.title,
            'column_id': item.column_id,
            'parent_id': item.parent_id,
            'created_at': item.created_at,
            'updated_at': item.updated_at,
            'metadata': item.metadata
        }

        post = frontmatter.Post(
            content=item.description or "", metadata=item_metadata)

        with open(item_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def delete_item_from_column(self, board: Board, item: Item) -> bool:
        """Delete an item's markdown file from its column folder."""
        # Find the column for this item
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
        item_file = column_dir / f"{item.id}.md"

        if item_file.exists():
            item_file.unlink()
            return True
        return False

    def _get_board_directory(self, board: Board) -> Path:
        """Get the directory path for a board."""
        safe_name = self._get_safe_name(board.name)
        return self.boards_dir / safe_name

    def _get_safe_name(self, name: str) -> str:
        """Convert a name to a safe directory/file name."""
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        safe_name = re.sub(r'\s+', '-', safe_name.strip())
        return safe_name or 'unnamed'

    def list_board_names(self) -> List[str]:
        """List all board names."""
        boards = self.load_boards()
        return [board.name for board in boards]

    def create_sample_board(self, name: str = "sample") -> Board:
        """Create a sample board for testing."""
        board = Board(name=name.title())

        # Add default columns
        todo_col = board.add_column("To Do", 0)
        progress_col = board.add_column("In Progress", 1)
        done_col = board.add_column("Done", 2)

        # Add sample parent
        feature_parent = board.add_parent("Feature Development", "green")

        # Add sample items
        board.add_item("Create project structure", todo_col.id)
        board.add_item("Implement data models",
                       progress_col.id, feature_parent.id)
        board.add_item("Setup development environment", done_col.id)

        return board
