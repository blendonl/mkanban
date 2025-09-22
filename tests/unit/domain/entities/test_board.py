from unittest.mock import patch

from src.domain.entities.board import Board
from tests.fixtures.entity_factories import BoardFactory, ColumnFactory, ItemFactory, ParentFactory


class TestBoard:
    """Test cases for the Board entity."""

    def test_board_creation_with_defaults(self):
        """Test creating a board with default values."""
        board = Board(name="Test Board")

        assert board.name == "Test Board"
        assert board.description == ""
        assert board.file_path is None
        assert board.columns == []
        assert board.parents == []
        assert board.id == "test_board"
        assert board.created_at is not None
        assert board.updated_at is not None

    def test_board_creation_with_all_fields(self):
        """Test creating a board with all fields specified."""
        columns = ColumnFactory.create_default_columns()
        parents = ParentFactory.create_batch(2)

        board = Board(
            name="Full Board",
            description="A complete board",
            columns=columns,
            parents=parents,
            file_path="/path/to/board.md"
        )

        assert board.name == "Full Board"
        assert board.description == "A complete board"
        assert board.file_path == "/path/to/board.md"
        assert len(board.columns) == 3
        assert len(board.parents) == 2
        assert board.id == "full-board"

    def test_board_id_generation_from_file_path(self):
        """Test that board ID is generated from file path when provided."""
        board = Board(
            name="",
            file_path="/data/boards/my-project/kanban.md"
        )

        assert board.id == "my-project"
        assert board.name == "my-project"

    def test_board_id_generation_from_name(self):
        """Test that board ID is generated from name when no file path."""
        board = Board(name="My Awesome Project")

        assert board.id == "my-awesome-project"
        assert board.name == "My Awesome Project"

    def test_board_id_fallback_to_unnamed(self):
        """Test that board ID falls back to 'unnamed_board' when name is empty."""
        board = Board(name="")

        assert board.id == "unnamed_board"
        assert board.name == ""

    def test_board_update(self):
        """Test updating board properties."""
        board = BoardFactory.create()
        original_updated_at = board.updated_at

        # Small delay to ensure updated_at changes
        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            board.update(description="Updated description", name="New Name")

        assert board.description == "Updated description"
        assert board.name == "New Name"
        assert board.updated_at > original_updated_at

    def test_add_column(self):
        """Test adding a column to the board."""
        board = BoardFactory.create_empty()

        column = board.add_column("New Column")

        assert len(board.columns) == 1
        assert column.name == "New Column"
        assert column.position == 0
        assert column in board.columns

    def test_add_column_with_position(self):
        """Test adding a column with a specific position."""
        board = BoardFactory.create()  # Has default columns
        original_count = len(board.columns)

        column = board.add_column("Priority", position=1)

        assert len(board.columns) == original_count + 1
        assert column.name == "Priority"
        assert column.position == 1
        # Verify columns are sorted by position
        positions = [col.position for col in board.columns]
        assert positions == sorted(positions)

    def test_remove_column_success(self):
        """Test successfully removing a column."""
        board = BoardFactory.create()
        column_to_remove = board.columns[0]
        column_id = column_to_remove.id
        original_count = len(board.columns)

        result = board.remove_column(column_id)

        assert result is True
        assert len(board.columns) == original_count - 1
        assert column_to_remove not in board.columns

    def test_remove_column_not_found(self):
        """Test removing a non-existent column."""
        board = BoardFactory.create()
        original_count = len(board.columns)

        result = board.remove_column("non-existent-id")

        assert result is False
        assert len(board.columns) == original_count

    def test_get_column_by_id(self):
        """Test retrieving a column by ID."""
        board = BoardFactory.create()
        target_column = board.columns[1]

        result = board.get_column_by_id(target_column.id)

        assert result == target_column

    def test_get_column_by_id_not_found(self):
        """Test retrieving a non-existent column by ID."""
        board = BoardFactory.create()

        result = board.get_column_by_id("non-existent-id")

        assert result is None

    def test_get_first_column(self):
        """Test getting the first column by position."""
        board = BoardFactory.create()

        first_column = board.get_first_column()

        assert first_column is not None
        assert first_column.position == 0
        # Verify it's actually the column with minimum position
        all_positions = [col.position for col in board.columns]
        assert first_column.position == min(all_positions)

    def test_get_first_column_empty_board(self):
        """Test getting first column from empty board."""
        board = BoardFactory.create_empty()

        first_column = board.get_first_column()

        assert first_column is None

    def test_get_orphaned_items(self):
        """Test getting items without parent assignments."""
        board = BoardFactory.create_with_items()
        parent = ParentFactory.create()
        board.parents.append(parent)

        # Assign parent to some items
        board.columns[0].items[0].parent_id = parent.id

        orphaned_items = board.get_orphaned_items()

        # Should include all items except the one with parent_id
        total_items = sum(len(col.items) for col in board.columns)
        assert len(orphaned_items) == total_items - 1
        assert board.columns[0].items[0] not in orphaned_items

    def test_get_orphaned_items_all_orphaned(self):
        """Test getting orphaned items when all items are orphaned."""
        board = BoardFactory.create_with_items()

        orphaned_items = board.get_orphaned_items()

        total_items = sum(len(col.items) for col in board.columns)
        assert len(orphaned_items) == total_items

    def test_add_parent(self):
        """Test adding a parent to the board."""
        board = BoardFactory.create_empty()

        parent = board.add_parent("Epic 1", "blue")

        assert len(board.parents) == 1
        assert parent.name == "Epic 1"
        assert parent.color == "blue"
        assert parent in board.parents

    def test_remove_parent_success(self):
        """Test successfully removing a parent."""
        board = BoardFactory.create()
        parent = ParentFactory.create()
        board.parents.append(parent)
        original_count = len(board.parents)

        result = board.remove_parent(parent.id)

        assert result is True
        assert len(board.parents) == original_count - 1
        assert parent not in board.parents

    def test_remove_parent_not_found(self):
        """Test removing a non-existent parent."""
        board = BoardFactory.create()
        original_count = len(board.parents)

        result = board.remove_parent("non-existent-id")

        assert result is False
        assert len(board.parents) == original_count

    def test_get_parent_by_id(self):
        """Test retrieving a parent by ID."""
        board = BoardFactory.create()
        parent = ParentFactory.create()
        board.parents.append(parent)

        result = board.get_parent_by_id(parent.id)

        assert result == parent

    def test_get_parent_by_id_not_found(self):
        """Test retrieving a non-existent parent by ID."""
        board = BoardFactory.create()

        result = board.get_parent_by_id("non-existent-id")

        assert result is None

    def test_board_updated_at_changes_on_modifications(self):
        """Test that updated_at changes when board is modified."""
        board = BoardFactory.create_empty()
        original_updated_at = board.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            board.add_column("New Column")

        assert board.updated_at > original_updated_at

    def test_board_serialization(self):
        """Test that board can be serialized to dict."""
        board = BoardFactory.create()

        board_dict = board.model_dump()

        assert isinstance(board_dict, dict)
        assert board_dict["name"] == board.name
        assert board_dict["description"] == board.description
        assert board_dict["id"] == board.id
        assert "columns" in board_dict
        assert "parents" in board_dict

    def test_board_with_complex_scenario(self):
        """Test board behavior in a complex scenario."""
        # Create board with columns, items, and parents
        board = BoardFactory.create_empty()

        # Add columns in non-sequential order
        col3 = board.add_column("Done", 2)
        col1 = board.add_column("To Do", 0)
        col2 = board.add_column("In Progress", 1)

        # Add parents
        epic1 = board.add_parent("Epic 1", "blue")
        epic2 = board.add_parent("Epic 2", "green")

        # Add items to columns
        item1 = ItemFactory.create(title="Task 1", column_id=col1.id, parent_id=epic1.id)
        item2 = ItemFactory.create(title="Task 2", column_id=col2.id)
        item3 = ItemFactory.create(title="Task 3", column_id=col3.id, parent_id=epic2.id)

        col1.items.append(item1)
        col2.items.append(item2)
        col3.items.append(item3)

        # Verify structure
        assert len(board.columns) == 3
        assert len(board.parents) == 2
        assert board.get_first_column() == col1

        # Verify orphaned items
        orphaned = board.get_orphaned_items()
        assert len(orphaned) == 1
        assert item2 in orphaned

        # Verify columns are properly sorted
        positions = [col.position for col in board.columns]
        assert positions == [0, 1, 2]