from typing import List, Optional
from datetime import datetime

from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.domain.entities.parent import Parent
from src.utils.date_utils import now


class BoardFactory:
    """Factory for creating test Board instances."""

    @staticmethod
    def create(
        name: str = "Test Board",
        description: str = "A test board",
        columns: Optional[List[Column]] = None,
        parents: Optional[List[Parent]] = None,
        **kwargs
    ) -> Board:
        """Create a test board with optional customization."""
        if columns is None:
            columns = ColumnFactory.create_default_columns()

        if parents is None:
            parents = []

        return Board(
            name=name,
            description=description,
            columns=columns,
            parents=parents,
            created_at=kwargs.get("created_at", now()),
            updated_at=kwargs.get("updated_at", now()),
            **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
        )

    @staticmethod
    def create_with_items(
        name: str = "Board with Items",
        item_count_per_column: int = 2
    ) -> Board:
        """Create a board with items in each column."""
        board = BoardFactory.create(name=name)

        for i, column in enumerate(board.columns):
            for j in range(item_count_per_column):
                item = ItemFactory.create(
                    title=f"Item {i+1}-{j+1}",
                    description=f"Test item {j+1} in {column.name}",
                    column_id=column.id
                )
                column.items.append(item)

        return board

    @staticmethod
    def create_empty(name: str = "Empty Board") -> Board:
        """Create an empty board with no columns."""
        return Board(name=name, description="An empty test board")


class ColumnFactory:
    """Factory for creating test Column instances."""

    @staticmethod
    def create(
        name: str = "Test Column",
        position: int = 0,
        items: Optional[List[Item]] = None,
        **kwargs
    ) -> Column:
        """Create a test column with optional customization."""
        if items is None:
            items = []

        return Column(
            name=name,
            position=position,
            items=items,
            created_at=kwargs.get("created_at", now()),
            updated_at=kwargs.get("updated_at", now()),
            **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
        )

    @staticmethod
    def create_default_columns() -> List[Column]:
        """Create default set of columns (To Do, In Progress, Done)."""
        return [
            ColumnFactory.create("To Do", 0),
            ColumnFactory.create("In Progress", 1),
            ColumnFactory.create("Done", 2),
        ]

    @staticmethod
    def create_with_items(
        name: str = "Column with Items",
        item_count: int = 3,
        position: int = 0
    ) -> Column:
        """Create a column with specified number of items."""
        column = ColumnFactory.create(name=name, position=position)
        for i in range(item_count):
            item = ItemFactory.create(
                title=f"Item {i+1}",
                description=f"Test item {i+1}",
                column_id=column.id
            )
            column.items.append(item)
        return column


class ItemFactory:
    """Factory for creating test Item instances."""

    @staticmethod
    def create(
        title: str = "Test Item",
        description: str = "A test item",
        status: str = "To Do",
        tags: Optional[List[str]] = None,
        column_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> Item:
        """Create a test item with optional customization."""
        if tags is None:
            tags = ["test"]

        return Item(
            title=title,
            description=description,
            status=status,
            tags=tags,
            column_id=column_id,
            parent_id=parent_id,
            created_at=kwargs.get("created_at", now()),
            updated_at=kwargs.get("updated_at", now()),
            **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
        )

    @staticmethod
    def create_with_parent(
        title: str = "Item with Parent",
        parent: Optional[Parent] = None,
        **kwargs
    ) -> Item:
        """Create an item linked to a parent."""
        if parent is None:
            parent = ParentFactory.create()

        return ItemFactory.create(
            title=title,
            parent_id=parent.id,
            **kwargs
        )

    @staticmethod
    def create_batch(
        count: int = 3,
        title_prefix: str = "Item",
        **kwargs
    ) -> List[Item]:
        """Create a batch of items with incrementing titles."""
        items = []
        for i in range(count):
            item = ItemFactory.create(
                title=f"{title_prefix} {i+1}",
                description=f"Test item {i+1}",
                **kwargs
            )
            items.append(item)
        return items


class ParentFactory:
    """Factory for creating test Parent instances."""

    @staticmethod
    def create(
        name: str = "Test Epic",
        color: str = "blue",
        description: str = "A test epic",
        **kwargs
    ) -> Parent:
        """Create a test parent with optional customization."""
        return Parent(
            name=name,
            color=color,
            description=description,
            created_at=kwargs.get("created_at", now()),
            updated_at=kwargs.get("updated_at", now()),
            **{k: v for k, v in kwargs.items() if k not in ["created_at", "updated_at"]}
        )

    @staticmethod
    def create_batch(
        count: int = 3,
        name_prefix: str = "Epic",
        colors: Optional[List[str]] = None
    ) -> List[Parent]:
        """Create a batch of parents with different colors."""
        if colors is None:
            colors = ["blue", "green", "red", "yellow", "purple"]

        parents = []
        for i in range(count):
            color = colors[i % len(colors)]
            parent = ParentFactory.create(
                name=f"{name_prefix} {i+1}",
                color=color,
                description=f"Test epic {i+1}"
            )
            parents.append(parent)
        return parents


class ScenarioFactory:
    """Factory for creating common test scenarios."""

    @staticmethod
    def create_full_board() -> Board:
        """Create a board with columns, items, and parents."""
        # Create parents
        parents = ParentFactory.create_batch(2)

        # Create board with default columns
        board = BoardFactory.create(
            name="Full Test Board",
            description="A complete board for testing",
            parents=parents
        )

        # Add items to columns with some having parents
        for i, column in enumerate(board.columns):
            # Add 2-3 items per column
            item_count = 2 + (i % 2)
            for j in range(item_count):
                parent_id = parents[j % len(parents)].id if j < len(parents) else None
                item = ItemFactory.create(
                    title=f"{column.name} Item {j+1}",
                    description=f"Test item {j+1} in {column.name}",
                    column_id=column.id,
                    parent_id=parent_id,
                    status=column.name
                )
                column.items.append(item)

        return board

    @staticmethod
    def create_kanban_workflow() -> Board:
        """Create a board simulating a typical Kanban workflow."""
        board = BoardFactory.create(
            name="Kanban Workflow",
            description="A board simulating real Kanban usage"
        )

        # Create epic parent
        epic = ParentFactory.create(
            name="User Authentication Epic",
            color="blue",
            description="Epic for user authentication features"
        )
        board.parents.append(epic)

        # Add realistic tasks
        todo_items = [
            ItemFactory.create(
                title="Design login page mockups",
                description="Create wireframes and mockups for the login page",
                column_id=board.columns[0].id,
                parent_id=epic.id,
                tags=["design", "frontend"]
            ),
            ItemFactory.create(
                title="Set up authentication API endpoints",
                description="Create REST endpoints for login/logout",
                column_id=board.columns[0].id,
                parent_id=epic.id,
                tags=["backend", "api"]
            ),
        ]

        in_progress_items = [
            ItemFactory.create(
                title="Implement password validation",
                description="Add client and server-side password validation",
                column_id=board.columns[1].id,
                parent_id=epic.id,
                tags=["frontend", "backend", "validation"]
            ),
        ]

        done_items = [
            ItemFactory.create(
                title="Research authentication libraries",
                description="Compare OAuth, JWT, and session-based auth",
                column_id=board.columns[2].id,
                parent_id=epic.id,
                tags=["research", "security"]
            ),
        ]

        board.columns[0].items.extend(todo_items)
        board.columns[1].items.extend(in_progress_items)
        board.columns[2].items.extend(done_items)

        return board