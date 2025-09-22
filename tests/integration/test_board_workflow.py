import pytest
from pathlib import Path

from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.core.dependency_container import DependencyContainer


@pytest.mark.integration
class TestBoardWorkflow:
    """Integration tests for complete board workflows."""

    def setup_method(self, test_container):
        """Set up integration test environment."""
        self.container = test_container
        self.board_service = self.container.get(BoardService)
        self.item_service = self.container.get(ItemService)

    def test_complete_board_workflow(self, test_container):
        """Test a complete board workflow from creation to task completion."""
        # Create a new board
        board = self.board_service.create_board(
            "Integration Test Board",
            "Board for testing complete workflow"
        )

        assert board.name == "Integration Test Board"
        assert len(board.columns) >= 3  # Default columns

        # Add a custom column
        custom_column = self.board_service.add_column_to_board(
            board, "Review", position=2
        )

        assert custom_column.name == "Review"
        assert custom_column in board.columns

        # Create items in different columns
        todo_column = board.get_first_column()
        item1 = self.item_service.create_item(
            board=board,
            column_id=todo_column.id,
            title="Implement feature",
            description="Add new feature to the application"
        )

        assert item1.title == "Implement feature"
        assert item1.column_id == todo_column.id

        # Move item through workflow
        in_progress_column = board.columns[1]
        move_result = self.item_service.move_item_between_columns(
            board=board,
            item_id=item1.id,
            target_column_id=in_progress_column.id
        )

        assert move_result is True
        assert item1.column_id == in_progress_column.id

        # Update item
        update_result = self.item_service.update_item(
            board=board,
            item_id=item1.id,
            status="In Progress",
            priority="high"
        )

        assert update_result is True
        assert item1.status == "In Progress"
        assert item1.priority == "high"

        # Save board
        self.board_service.save_board(board)

        # Verify board can be retrieved
        retrieved_board = self.board_service.get_board_by_name(board.name)
        assert retrieved_board.name == board.name
        assert len(retrieved_board.columns) == len(board.columns)

    def test_board_with_parents_workflow(self, test_container):
        """Test workflow with parent/epic organization."""
        # Create board
        board = self.board_service.create_board("Epic Board", "Board with epics")

        # Add parent/epic
        epic = board.add_parent("User Authentication", "blue")
        assert epic.name == "User Authentication"

        # Create items under the epic
        todo_column = board.get_first_column()

        login_task = self.item_service.create_item(
            board=board,
            column_id=todo_column.id,
            title="Implement login",
            description="Create login functionality",
            parent_id=epic.id
        )

        logout_task = self.item_service.create_item(
            board=board,
            column_id=todo_column.id,
            title="Implement logout",
            description="Create logout functionality",
            parent_id=epic.id
        )

        assert login_task.parent_id == epic.id
        assert logout_task.parent_id == epic.id

        # Test grouping by parent
        grouped_items = self.item_service.get_items_grouped_by_parent(
            board, todo_column.id
        )

        # Should contain both items
        epic_items = [item for item in grouped_items if item.parent_id == epic.id]
        assert len(epic_items) == 2

        # Test removing parent assignment
        unassign_result = self.item_service.set_item_parent(
            board=board,
            item_id=login_task.id,
            parent_id=None
        )

        assert unassign_result is True
        assert login_task.parent_id is None

    def test_error_handling_in_workflow(self, test_container):
        """Test error handling in integrated workflows."""
        # Create board
        board = self.board_service.create_board("Error Test Board")

        # Try to create item in non-existent column
        with pytest.raises(Exception):  # Should raise ColumnNotFoundError
            self.item_service.create_item(
                board=board,
                column_id="non-existent-column",
                title="Test Task"
            )

        # Try to move non-existent item
        with pytest.raises(Exception):  # Should raise ItemNotFoundError
            self.item_service.move_item_between_columns(
                board=board,
                item_id="non-existent-item",
                target_column_id=board.columns[0].id
            )

        # Try to create board with duplicate name
        with pytest.raises(Exception):  # Should raise ValidationError
            self.board_service.create_board("Error Test Board")  # Same name