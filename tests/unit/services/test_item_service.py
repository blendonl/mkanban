import pytest
from unittest.mock import MagicMock

from src.services.item_service import ItemService
from src.core.exceptions import ItemNotFoundError, ColumnNotFoundError, ValidationError
from tests.fixtures.entity_factories import BoardFactory, ColumnFactory, ItemFactory, ParentFactory
from tests.fixtures.mock_factories import MockRepositoryFactory, MockServiceFactory


class TestItemService:
    """Test cases for the ItemService class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_storage = MockRepositoryFactory.create_storage_repository()
        self.mock_validator = MockServiceFactory.create_validation_service()
        self.mock_logger = MockServiceFactory.create_logger()

        self.service = ItemService(
            storage_repository=self.mock_storage,
            validation_service=self.mock_validator,
            logger=self.mock_logger
        )

    def test_create_item_success(self):
        """Test successfully creating an item."""
        board = BoardFactory.create()
        column = board.columns[0]

        # Mock validation passes
        self.mock_validator.validate_item_title.return_value = None
        self.mock_validator.validate_column_capacity.return_value = None

        result = self.service.create_item(
            board=board,
            column_id=column.id,
            title="New Task",
            description="A new test task"
        )

        assert result.title == "New Task"
        assert result.description == "A new test task"
        assert result.column_id == column.id
        self.mock_validator.validate_item_title.assert_called_once_with("New Task")
        self.mock_validator.validate_column_capacity.assert_called_once_with(column)
        self.mock_logger.info.assert_called()

    def test_create_item_invalid_column(self):
        """Test creating an item in a non-existent column."""
        board = BoardFactory.create()

        with pytest.raises(ColumnNotFoundError) as exc_info:
            self.service.create_item(
                board=board,
                column_id="non-existent-column",
                title="New Task"
            )

        assert "Column with id 'non-existent-column' not found" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_create_item_validation_failure(self):
        """Test creating an item with invalid title."""
        board = BoardFactory.create()
        column = board.columns[0]
        validation_error = ValidationError("Item title cannot be empty")
        self.mock_validator.validate_item_title.side_effect = validation_error

        with pytest.raises(ValidationError):
            self.service.create_item(
                board=board,
                column_id=column.id,
                title=""
            )

        self.mock_validator.validate_item_title.assert_called_once_with("")

    def test_create_item_with_parent_success(self):
        """Test creating an item with a parent."""
        board = BoardFactory.create()
        parent = ParentFactory.create()
        board.parents.append(parent)
        column = board.columns[0]

        result = self.service.create_item(
            board=board,
            column_id=column.id,
            title="Child Task",
            parent_id=parent.id
        )

        assert result.parent_id == parent.id
        self.mock_logger.info.assert_called()

    def test_create_item_with_invalid_parent(self):
        """Test creating an item with non-existent parent."""
        board = BoardFactory.create()
        column = board.columns[0]

        with pytest.raises(ValidationError) as exc_info:
            self.service.create_item(
                board=board,
                column_id=column.id,
                title="Child Task",
                parent_id="non-existent-parent"
            )

        assert "Parent with id 'non-existent-parent' not found" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_create_item_column_at_capacity(self):
        """Test creating an item when column is at capacity."""
        board = BoardFactory.create()
        column = board.columns[0]
        capacity_error = ValidationError("Column is at capacity")
        self.mock_validator.validate_column_capacity.side_effect = capacity_error

        with pytest.raises(ValidationError):
            self.service.create_item(
                board=board,
                column_id=column.id,
                title="New Task"
            )

        self.mock_validator.validate_column_capacity.assert_called_once_with(column)

    def test_update_item_success(self):
        """Test successfully updating an item."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]

        result = self.service.update_item(
            board=board,
            item_id=item.id,
            description="Updated description",
            priority="high"
        )

        assert result is True
        assert item.description == "Updated description"
        assert item.priority == "high"

    def test_update_item_with_title_validation(self):
        """Test updating an item with title validation."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]

        self.service.update_item(
            board=board,
            item_id=item.id,
            title="Updated Title"
        )

        self.mock_validator.validate_item_title.assert_called_once_with("Updated Title")

    def test_update_item_not_found(self):
        """Test updating a non-existent item."""
        board = BoardFactory.create()

        with pytest.raises(ItemNotFoundError) as exc_info:
            self.service.update_item(
                board=board,
                item_id="non-existent-item",
                description="Updated description"
            )

        assert "Item with id 'non-existent-item' not found" in str(exc_info.value)

    def test_delete_item_success(self):
        """Test successfully deleting an item."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]
        column = board.columns[0]

        # Mock storage operations
        self.mock_storage.delete_item_from_column.return_value = True
        self.mock_storage.save_board_to_storage.return_value = True

        result = self.service.delete_item(board=board, item_id=item.id)

        assert result is True
        self.mock_storage.delete_item_from_column.assert_called_once_with(board, item, column)
        self.mock_storage.save_board_to_storage.assert_called_once_with(board)
        self.mock_logger.info.assert_called()

    def test_delete_item_storage_failure(self):
        """Test deleting an item when storage fails."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]

        # Mock storage failure
        self.mock_storage.delete_item_from_column.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            self.service.delete_item(board=board, item_id=item.id)

        assert "Failed to delete item from storage" in str(exc_info.value)
        self.mock_logger.error.assert_called_once()

    def test_delete_item_not_found(self):
        """Test deleting a non-existent item."""
        board = BoardFactory.create()

        with pytest.raises(ItemNotFoundError) as exc_info:
            self.service.delete_item(board=board, item_id="non-existent-item")

        assert "Item with id 'non-existent-item' not found" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_move_item_between_columns_success(self):
        """Test successfully moving an item between columns."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]
        source_column = board.columns[0]
        target_column = board.columns[1]

        # Mock storage operations
        self.mock_storage.move_item_between_columns.return_value = True
        self.mock_storage.save_board_to_storage.return_value = True
        self.mock_validator.validate_column_capacity.return_value = None

        result = self.service.move_item_between_columns(
            board=board,
            item_id=item.id,
            target_column_id=target_column.id
        )

        assert result is True
        assert item.column_id == target_column.id
        self.mock_storage.move_item_between_columns.assert_called_once_with(
            board, item, source_column, target_column
        )
        self.mock_validator.validate_column_capacity.assert_called_once_with(target_column)

    def test_move_item_between_columns_same_column(self):
        """Test moving an item to the same column."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]
        column = board.columns[0]

        result = self.service.move_item_between_columns(
            board=board,
            item_id=item.id,
            target_column_id=column.id
        )

        assert result is False

    def test_move_item_between_columns_item_not_found(self):
        """Test moving a non-existent item."""
        board = BoardFactory.create()

        with pytest.raises(ItemNotFoundError) as exc_info:
            self.service.move_item_between_columns(
                board=board,
                item_id="non-existent-item",
                target_column_id=board.columns[0].id
            )

        assert "Item with id 'non-existent-item' not found" in str(exc_info.value)

    def test_move_item_between_columns_target_not_found(self):
        """Test moving an item to a non-existent column."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]

        with pytest.raises(ColumnNotFoundError) as exc_info:
            self.service.move_item_between_columns(
                board=board,
                item_id=item.id,
                target_column_id="non-existent-column"
            )

        assert "Target column with id 'non-existent-column' not found" in str(exc_info.value)

    def test_move_item_target_column_at_capacity(self):
        """Test moving an item to a column at capacity."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]
        target_column = board.columns[1]
        capacity_error = ValidationError("Column is at capacity")
        self.mock_validator.validate_column_capacity.side_effect = capacity_error

        with pytest.raises(ValidationError):
            self.service.move_item_between_columns(
                board=board,
                item_id=item.id,
                target_column_id=target_column.id
            )

    def test_move_item_storage_failure(self):
        """Test moving an item when storage fails."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]
        target_column = board.columns[1]

        # Mock storage failure
        self.mock_storage.move_item_between_columns.return_value = False

        result = self.service.move_item_between_columns(
            board=board,
            item_id=item.id,
            target_column_id=target_column.id
        )

        assert result is False

    def test_set_item_parent_success(self):
        """Test successfully setting an item's parent."""
        board = BoardFactory.create_with_items()
        parent = ParentFactory.create()
        board.parents.append(parent)
        item = board.columns[0].items[0]

        result = self.service.set_item_parent(
            board=board,
            item_id=item.id,
            parent_id=parent.id
        )

        assert result is True
        assert item.parent_id == parent.id

    def test_set_item_parent_remove_parent(self):
        """Test removing an item's parent."""
        board = BoardFactory.create_with_items()
        parent = ParentFactory.create()
        board.parents.append(parent)
        item = board.columns[0].items[0]
        item.parent_id = parent.id

        result = self.service.set_item_parent(
            board=board,
            item_id=item.id,
            parent_id=None
        )

        assert result is True
        assert item.parent_id is None

    def test_set_item_parent_invalid_parent(self):
        """Test setting an item's parent to non-existent parent."""
        board = BoardFactory.create_with_items()
        item = board.columns[0].items[0]

        with pytest.raises(ValidationError) as exc_info:
            self.service.set_item_parent(
                board=board,
                item_id=item.id,
                parent_id="non-existent-parent"
            )

        assert "Parent with id 'non-existent-parent' not found" in str(exc_info.value)

    def test_set_item_parent_item_not_found(self):
        """Test setting parent for non-existent item."""
        board = BoardFactory.create()
        parent = ParentFactory.create()
        board.parents.append(parent)

        with pytest.raises(ItemNotFoundError) as exc_info:
            self.service.set_item_parent(
                board=board,
                item_id="non-existent-item",
                parent_id=parent.id
            )

        assert "Item with id 'non-existent-item' not found" in str(exc_info.value)

    def test_get_items_grouped_by_parent(self):
        """Test retrieving items grouped by parent."""
        board = BoardFactory.create()
        column = board.columns[0]
        parent1 = ParentFactory.create(name="Epic 1")
        parent2 = ParentFactory.create(name="Epic 2")
        board.parents.extend([parent1, parent2])

        # Add items with different parent assignments
        orphaned_item = ItemFactory.create(title="Orphaned Task")
        parent1_item1 = ItemFactory.create(title="Epic 1 Task 1", parent_id=parent1.id)
        parent1_item2 = ItemFactory.create(title="Epic 1 Task 2", parent_id=parent1.id)
        parent2_item = ItemFactory.create(title="Epic 2 Task", parent_id=parent2.id)

        column.items.extend([orphaned_item, parent1_item1, parent1_item2, parent2_item])

        result = self.service.get_items_grouped_by_parent(board, column.id)

        # Should return items in order: orphaned first, then grouped by parent
        assert len(result) == 4
        assert result[0] == orphaned_item  # Orphaned items first
        # Parent groups should follow
        parent_items = result[1:]
        assert parent1_item1 in parent_items
        assert parent1_item2 in parent_items
        assert parent2_item in parent_items

    def test_get_items_grouped_by_parent_column_not_found(self):
        """Test grouping items for non-existent column."""
        board = BoardFactory.create()

        with pytest.raises(ColumnNotFoundError) as exc_info:
            self.service.get_items_grouped_by_parent(board, "non-existent-column")

        assert "Column with id 'non-existent-column' not found" in str(exc_info.value)

    def test_service_with_complex_scenario(self):
        """Test service behavior in a complex scenario."""
        # Setup: Create board with multiple columns and parents
        board = BoardFactory.create()
        parent = ParentFactory.create(name="Authentication Epic")
        board.parents.append(parent)

        todo_column = board.columns[0]
        in_progress_column = board.columns[1]

        # Create an item in todo column
        item = self.service.create_item(
            board=board,
            column_id=todo_column.id,
            title="Implement login",
            description="Add user login functionality",
            parent_id=parent.id
        )

        # Verify item was created correctly
        assert item.title == "Implement login"
        assert item.parent_id == parent.id
        assert item in todo_column.items

        # Update the item
        self.service.update_item(
            board=board,
            item_id=item.id,
            priority="high",
            status="In Progress"
        )

        # Move item to in-progress column
        self.mock_storage.move_item_between_columns.return_value = True
        move_result = self.service.move_item_between_columns(
            board=board,
            item_id=item.id,
            target_column_id=in_progress_column.id
        )

        assert move_result is True
        assert item.column_id == in_progress_column.id

        # Test grouping functionality
        grouped_items = self.service.get_items_grouped_by_parent(board, in_progress_column.id)
        assert item in grouped_items

        # Verify all mocks were called appropriately
        self.mock_validator.validate_item_title.assert_called()
        self.mock_validator.validate_column_capacity.assert_called()
        self.mock_storage.move_item_between_columns.assert_called()
        self.mock_logger.info.assert_called()