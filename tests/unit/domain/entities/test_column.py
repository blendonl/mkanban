from unittest.mock import patch

from src.domain.entities.column import Column
from tests.fixtures.entity_factories import ColumnFactory, ItemFactory


class TestColumn:
    """Test cases for the Column entity."""

    def test_column_creation_with_defaults(self):
        """Test creating a column with default values."""
        column = Column(name="Test Column")

        assert column.name == "Test Column"
        assert column.position == 0
        assert column.items == []
        assert column.id == "test-column"
        assert column.created_at is not None
        assert column.updated_at is not None

    def test_column_creation_with_all_fields(self):
        """Test creating a column with all fields specified."""
        items = ItemFactory.create_batch(3)

        column = Column(
            name="Complete Column",
            position=2,
            items=items
        )

        assert column.name == "Complete Column"
        assert column.position == 2
        assert len(column.items) == 3
        assert column.id == "complete-column"
        assert all(item in column.items for item in items)

    def test_column_id_generation_from_name(self):
        """Test that column ID is generated from name."""
        test_cases = [
            ("To Do", "to-do"),
            ("In Progress", "in-progress"),
            ("Done!", "done"),
            ("Review & Test", "review-test"),
            ("Column 123", "column-123"),
        ]

        for name, expected_id in test_cases:
            column = Column(name=name)
            assert column.id == expected_id

    def test_column_update(self):
        """Test updating column properties."""
        column = ColumnFactory.create()
        original_updated_at = column.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            column.update(name="Updated Column", position=5)

        assert column.name == "Updated Column"
        assert column.position == 5
        assert column.updated_at > original_updated_at

    def test_add_item(self):
        """Test adding an item to the column."""
        column = ColumnFactory.create()
        item = ItemFactory.create(title="New Task")

        column.add_item(item)

        assert len(column.items) == 1
        assert item in column.items
        assert item.column_id == column.id

    def test_add_item_updates_column_id(self):
        """Test that adding an item updates the item's column_id."""
        column = ColumnFactory.create()
        item = ItemFactory.create(title="Task", column_id="different-column")

        column.add_item(item)

        assert item.column_id == column.id

    def test_add_item_at_position(self):
        """Test adding an item at a specific position."""
        column = ColumnFactory.create_with_items(item_count=3)
        new_item = ItemFactory.create(title="Inserted Task")

        column.add_item(new_item, position=1)

        assert len(column.items) == 4
        assert column.items[1] == new_item
        assert new_item.column_id == column.id

    def test_add_item_at_invalid_position(self):
        """Test adding an item at an invalid position appends to end."""
        column = ColumnFactory.create_with_items(item_count=2)
        new_item = ItemFactory.create(title="Task")

        # Position beyond list length
        column.add_item(new_item, position=10)

        assert len(column.items) == 3
        assert column.items[-1] == new_item

    def test_remove_item_success(self):
        """Test successfully removing an item from the column."""
        column = ColumnFactory.create_with_items(item_count=3)
        item_to_remove = column.items[1]
        item_id = item_to_remove.id
        original_count = len(column.items)

        result = column.remove_item(item_id)

        assert result is True
        assert len(column.items) == original_count - 1
        assert item_to_remove not in column.items

    def test_remove_item_not_found(self):
        """Test removing a non-existent item."""
        column = ColumnFactory.create_with_items(item_count=2)
        original_count = len(column.items)

        result = column.remove_item("non-existent-id")

        assert result is False
        assert len(column.items) == original_count

    def test_get_item_by_id(self):
        """Test retrieving an item by ID."""
        column = ColumnFactory.create_with_items(item_count=3)
        target_item = column.items[1]

        result = column.get_item_by_id(target_item.id)

        assert result == target_item

    def test_get_item_by_id_not_found(self):
        """Test retrieving a non-existent item by ID."""
        column = ColumnFactory.create_with_items(item_count=2)

        result = column.get_item_by_id("non-existent-id")

        assert result is None

    def test_get_items_by_parent(self):
        """Test retrieving items by parent ID."""
        column = ColumnFactory.create()
        parent_id = "epic-123"

        # Add items with and without parent
        item1 = ItemFactory.create(title="Task 1", parent_id=parent_id)
        item2 = ItemFactory.create(title="Task 2")
        item3 = ItemFactory.create(title="Task 3", parent_id=parent_id)

        column.items.extend([item1, item2, item3])

        items_with_parent = column.get_items_by_parent(parent_id)

        assert len(items_with_parent) == 2
        assert item1 in items_with_parent
        assert item3 in items_with_parent
        assert item2 not in items_with_parent

    def test_get_items_by_parent_none_found(self):
        """Test retrieving items by parent ID when none exist."""
        column = ColumnFactory.create_with_items(item_count=2)

        items_with_parent = column.get_items_by_parent("non-existent-parent")

        assert len(items_with_parent) == 0

    def test_get_orphaned_items(self):
        """Test retrieving items without parent assignments."""
        column = ColumnFactory.create()
        parent_id = "epic-123"

        # Add items with and without parent
        orphaned_item1 = ItemFactory.create(title="Orphaned 1")
        orphaned_item2 = ItemFactory.create(title="Orphaned 2")
        parented_item = ItemFactory.create(title="Parented", parent_id=parent_id)

        column.items.extend([orphaned_item1, parented_item, orphaned_item2])

        orphaned_items = column.get_orphaned_items()

        assert len(orphaned_items) == 2
        assert orphaned_item1 in orphaned_items
        assert orphaned_item2 in orphaned_items
        assert parented_item not in orphaned_items

    def test_reorder_items(self):
        """Test reordering items in the column."""
        column = ColumnFactory.create_with_items(item_count=4)
        original_items = column.items.copy()

        # Move first item to position 2
        item_to_move = original_items[0]
        column.reorder_items(item_to_move.id, 2)

        expected_order = [original_items[1], original_items[2], original_items[0], original_items[3]]
        assert column.items == expected_order

    def test_reorder_items_to_end(self):
        """Test moving an item to the end of the column."""
        column = ColumnFactory.create_with_items(item_count=3)
        item_to_move = column.items[0]

        column.reorder_items(item_to_move.id, 2)

        assert column.items[-1] == item_to_move

    def test_reorder_items_invalid_id(self):
        """Test reordering with invalid item ID."""
        column = ColumnFactory.create_with_items(item_count=3)
        original_items = column.items.copy()

        result = column.reorder_items("non-existent-id", 1)

        assert result is False
        assert column.items == original_items

    def test_reorder_items_invalid_position(self):
        """Test reordering with invalid position."""
        column = ColumnFactory.create_with_items(item_count=3)
        item_to_move = column.items[0]
        original_items = column.items.copy()

        # Position beyond list bounds
        result = column.reorder_items(item_to_move.id, 10)

        # Item should be moved to the end
        assert result is True
        assert column.items[-1] == item_to_move

    def test_clear_items(self):
        """Test clearing all items from the column."""
        column = ColumnFactory.create_with_items(item_count=5)

        column.clear_items()

        assert len(column.items) == 0

    def test_item_count_property(self):
        """Test the item count property."""
        column = ColumnFactory.create_with_items(item_count=7)

        assert column.item_count == 7

        column.add_item(ItemFactory.create())
        assert column.item_count == 8

        column.remove_item(column.items[0].id)
        assert column.item_count == 7

    def test_column_updated_at_changes_on_modifications(self):
        """Test that updated_at changes when column is modified."""
        column = ColumnFactory.create()
        original_updated_at = column.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            column.add_item(ItemFactory.create())

        assert column.updated_at > original_updated_at

    def test_column_serialization(self):
        """Test that column can be serialized to dict."""
        column = ColumnFactory.create_with_items(item_count=2)

        column_dict = column.model_dump()

        assert isinstance(column_dict, dict)
        assert column_dict["name"] == column.name
        assert column_dict["position"] == column.position
        assert column_dict["id"] == column.id
        assert "items" in column_dict
        assert len(column_dict["items"]) == 2

    def test_column_equality(self):
        """Test column equality comparison."""
        column1 = ColumnFactory.create(name="Test", position=1)
        column2 = ColumnFactory.create(name="Test", position=1)
        column3 = ColumnFactory.create(name="Different", position=1)

        # Different instances with same data should be equal
        assert column1.id == column2.id
        # Different names should have different IDs
        assert column1.id != column3.id

    def test_column_with_complex_scenario(self):
        """Test column behavior in a complex scenario."""
        column = ColumnFactory.create(name="Development", position=1)

        # Add items with different characteristics
        urgent_task = ItemFactory.create(
            title="Critical Bug Fix",
            parent_id="epic-1",
            tags=["urgent", "bug"]
        )
        regular_task = ItemFactory.create(
            title="Regular Feature",
            tags=["feature"]
        )
        review_task = ItemFactory.create(
            title="Code Review",
            parent_id="epic-2",
            tags=["review"]
        )

        # Add items in specific order
        column.add_item(regular_task)
        column.add_item(urgent_task, position=0)  # Insert at beginning
        column.add_item(review_task)

        # Verify order
        assert column.items[0] == urgent_task
        assert column.items[1] == regular_task
        assert column.items[2] == review_task

        # Test filtering by parent
        epic1_items = column.get_items_by_parent("epic-1")
        assert len(epic1_items) == 1
        assert urgent_task in epic1_items

        # Test orphaned items
        orphaned = column.get_orphaned_items()
        assert len(orphaned) == 1
        assert regular_task in orphaned

        # Test reordering
        column.reorder_items(review_task.id, 1)
        assert column.items[1] == review_task
        assert column.items[2] == regular_task