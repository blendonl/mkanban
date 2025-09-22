import pytest
from unittest.mock import patch
from datetime import datetime

from src.domain.entities.item import Item
from tests.fixtures.entity_factories import ItemFactory


class TestItem:
    """Test cases for the Item entity."""

    def test_item_creation_with_defaults(self):
        """Test creating an item with default values."""
        item = Item(title="Test Task")

        assert item.title == "Test Task"
        assert item.description == ""
        assert item.status == "To Do"
        assert item.tags == []
        assert item.priority == "medium"
        assert item.estimated_hours is None
        assert item.column_id is None
        assert item.parent_id is None
        assert item.completed_at is None
        assert item.id == "test-task"
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_item_creation_with_all_fields(self):
        """Test creating an item with all fields specified."""
        item = Item(
            title="Complete Task",
            description="A comprehensive task",
            status="In Progress",
            tags=["urgent", "feature"],
            priority="high",
            estimated_hours=8,
            column_id="col-123",
            parent_id="epic-456"
        )

        assert item.title == "Complete Task"
        assert item.description == "A comprehensive task"
        assert item.status == "In Progress"
        assert item.tags == ["urgent", "feature"]
        assert item.priority == "high"
        assert item.estimated_hours == 8
        assert item.column_id == "col-123"
        assert item.parent_id == "epic-456"
        assert item.id == "complete-task"

    def test_item_id_generation_from_title(self):
        """Test that item ID is generated from title."""
        test_cases = [
            ("Simple Task", "simple-task"),
            ("Task with Numbers 123", "task-with-numbers-123"),
            ("Task/With\\Special*Chars", "task-with-special-chars"),
            ("Fix Bug #123", "fix-bug-123"),
            ("Multi   Spaces   Task", "multi-spaces-task"),
        ]

        for title, expected_id in test_cases:
            item = Item(title=title)
            assert item.id == expected_id

    def test_item_update(self):
        """Test updating item properties."""
        item = ItemFactory.create()
        original_updated_at = item.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            item.update(
                description="Updated description",
                status="In Progress",
                priority="high"
            )

        assert item.description == "Updated description"
        assert item.status == "In Progress"
        assert item.priority == "high"
        assert item.updated_at > original_updated_at

    def test_add_tag(self):
        """Test adding a tag to the item."""
        item = ItemFactory.create(tags=["existing"])

        item.add_tag("new-tag")

        assert "new-tag" in item.tags
        assert "existing" in item.tags
        assert len(item.tags) == 2

    def test_add_tag_duplicate(self):
        """Test adding a duplicate tag doesn't create duplicates."""
        item = ItemFactory.create(tags=["existing"])

        item.add_tag("existing")

        assert item.tags.count("existing") == 1
        assert len(item.tags) == 1

    def test_remove_tag_success(self):
        """Test successfully removing a tag."""
        item = ItemFactory.create(tags=["tag1", "tag2", "tag3"])

        result = item.remove_tag("tag2")

        assert result is True
        assert "tag2" not in item.tags
        assert len(item.tags) == 2
        assert "tag1" in item.tags
        assert "tag3" in item.tags

    def test_remove_tag_not_found(self):
        """Test removing a non-existent tag."""
        item = ItemFactory.create(tags=["tag1", "tag2"])

        result = item.remove_tag("non-existent")

        assert result is False
        assert len(item.tags) == 2

    def test_has_tag(self):
        """Test checking if item has a specific tag."""
        item = ItemFactory.create(tags=["urgent", "feature", "frontend"])

        assert item.has_tag("urgent") is True
        assert item.has_tag("feature") is True
        assert item.has_tag("backend") is False
        assert item.has_tag("") is False

    def test_mark_completed(self):
        """Test marking an item as completed."""
        item = ItemFactory.create(status="In Progress")

        with patch('src.utils.date_utils.now') as mock_now:
            mock_time = datetime.now().timestamp()
            mock_now.return_value = mock_time
            item.mark_completed()

        assert item.status == "Done"
        assert item.completed_at == mock_time

    def test_mark_completed_already_completed(self):
        """Test marking an already completed item."""
        item = ItemFactory.create(status="Done", completed_at=123456789)
        original_completed_at = item.completed_at

        item.mark_completed()

        # Should not change completed_at if already completed
        assert item.status == "Done"
        assert item.completed_at == original_completed_at

    def test_reopen_item(self):
        """Test reopening a completed item."""
        item = ItemFactory.create(status="Done", completed_at=123456789)

        item.reopen()

        assert item.status == "To Do"
        assert item.completed_at is None

    def test_is_completed(self):
        """Test checking if item is completed."""
        completed_item = ItemFactory.create(status="Done")
        incomplete_item = ItemFactory.create(status="In Progress")

        assert completed_item.is_completed() is True
        assert incomplete_item.is_completed() is False

    def test_is_overdue(self):
        """Test checking if item is overdue."""
        # Item with due date in the past
        past_due = datetime.now().timestamp() - 86400  # Yesterday
        overdue_item = ItemFactory.create(due_date=past_due)

        # Item with due date in the future
        future_due = datetime.now().timestamp() + 86400  # Tomorrow
        future_item = ItemFactory.create(due_date=future_due)

        # Item with no due date
        no_due_item = ItemFactory.create()

        assert overdue_item.is_overdue() is True
        assert future_item.is_overdue() is False
        assert no_due_item.is_overdue() is False

    def test_is_high_priority(self):
        """Test checking if item is high priority."""
        high_item = ItemFactory.create(priority="high")
        medium_item = ItemFactory.create(priority="medium")
        low_item = ItemFactory.create(priority="low")

        assert high_item.is_high_priority() is True
        assert medium_item.is_high_priority() is False
        assert low_item.is_high_priority() is False

    def test_estimated_hours_validation(self):
        """Test that estimated hours accepts valid values."""
        # Valid cases
        valid_hours = [1, 0.5, 8, 40]
        for hours in valid_hours:
            item = Item(title="Test", estimated_hours=hours)
            assert item.estimated_hours == hours

        # Edge cases
        zero_hours = Item(title="Test", estimated_hours=0)
        assert zero_hours.estimated_hours == 0

    def test_priority_values(self):
        """Test that priority accepts valid values."""
        valid_priorities = ["low", "medium", "high", "critical"]
        for priority in valid_priorities:
            item = Item(title="Test", priority=priority)
            assert item.priority == priority

    def test_move_to_column(self):
        """Test moving item to different column."""
        item = ItemFactory.create(column_id="col-1")

        item.move_to_column("col-2")

        assert item.column_id == "col-2"

    def test_assign_to_parent(self):
        """Test assigning item to a parent."""
        item = ItemFactory.create()

        item.assign_to_parent("epic-123")

        assert item.parent_id == "epic-123"

    def test_unassign_from_parent(self):
        """Test unassigning item from parent."""
        item = ItemFactory.create(parent_id="epic-123")

        item.unassign_from_parent()

        assert item.parent_id is None

    def test_item_updated_at_changes_on_modifications(self):
        """Test that updated_at changes when item is modified."""
        item = ItemFactory.create()
        original_updated_at = item.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            item.add_tag("new-tag")

        assert item.updated_at > original_updated_at

    def test_item_serialization(self):
        """Test that item can be serialized to dict."""
        item = ItemFactory.create(
            title="Serialization Test",
            tags=["test", "serialization"],
            priority="high"
        )

        item_dict = item.model_dump()

        assert isinstance(item_dict, dict)
        assert item_dict["title"] == "Serialization Test"
        assert item_dict["tags"] == ["test", "serialization"]
        assert item_dict["priority"] == "high"
        assert item_dict["id"] == "serialization-test"

    def test_item_equality(self):
        """Test item equality comparison."""
        item1 = ItemFactory.create(title="Same Task")
        item2 = ItemFactory.create(title="Same Task")
        item3 = ItemFactory.create(title="Different Task")

        # Items with same title should have same ID
        assert item1.id == item2.id
        # Items with different titles should have different IDs
        assert item1.id != item3.id

    def test_item_duration_calculation(self):
        """Test calculating time spent on item."""
        # Create item with start and end times
        start_time = datetime.now().timestamp() - 7200  # 2 hours ago
        end_time = datetime.now().timestamp()

        item = ItemFactory.create(
            status="Done",
            created_at=start_time,
            completed_at=end_time
        )

        duration = item.get_duration_hours()

        # Should be approximately 2 hours
        assert abs(duration - 2.0) < 0.1

    def test_item_duration_incomplete(self):
        """Test duration calculation for incomplete item."""
        item = ItemFactory.create(status="In Progress")

        duration = item.get_duration_hours()

        assert duration is None

    def test_item_with_complex_scenario(self):
        """Test item behavior in a complex scenario."""
        # Create item with comprehensive data
        item = ItemFactory.create(
            title="Complex Feature Implementation",
            description="Implement user authentication with OAuth",
            tags=["feature", "authentication", "security"],
            priority="high",
            estimated_hours=16,
            parent_id="epic-auth",
            column_id="in-progress"
        )

        # Verify initial state
        assert item.is_high_priority() is True
        assert item.has_tag("security") is True
        assert item.is_completed() is False

        # Add more tags
        item.add_tag("backend")
        item.add_tag("oauth")
        assert len(item.tags) == 5

        # Update progress
        item.update(description="Updated with OAuth 2.0 specs")

        # Move through workflow
        item.move_to_column("review")
        assert item.column_id == "review"

        # Complete the task
        item.mark_completed()
        assert item.is_completed() is True
        assert item.completed_at is not None

        # Verify all data is maintained
        assert item.title == "Complex Feature Implementation"
        assert item.parent_id == "epic-auth"
        assert item.estimated_hours == 16
        assert "oauth" in item.tags