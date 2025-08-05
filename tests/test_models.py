"""Tests for data models."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Board, Column, Item, Parent


def test_board_creation():
    """Test board creation and basic operations."""
    board = Board(name="Test Board")
    
    assert board.name == "Test Board"
    assert len(board.columns) == 0
    assert len(board.items) == 0
    assert len(board.parents) == 0


def test_column_operations():
    """Test column operations."""
    board = Board(name="Test Board")
    
    # Add columns
    col1 = board.add_column("Column 1", 0)
    col2 = board.add_column("Column 2", 1)
    
    assert len(board.columns) == 2
    assert col1.name == "Column 1"
    assert col1.position == 0
    assert col2.position == 1
    
    # Remove column
    board.remove_column(col1.id)
    assert len(board.columns) == 1


def test_item_operations():
    """Test item operations."""
    board = Board(name="Test Board")
    column = board.add_column("Test Column")
    
    # Add item
    item = board.add_item("Test Item", column.id)
    assert len(board.items) == 1
    assert item.title == "Test Item"
    assert item.column_id == column.id
    
    # Get column items
    column_items = board.get_column_items(column.id)
    assert len(column_items) == 1
    assert column_items[0].id == item.id
    
    # Remove item
    board.remove_item(item.id)
    assert len(board.items) == 0


def test_parent_operations():
    """Test parent operations."""
    board = Board(name="Test Board")
    column = board.add_column("Test Column")
    
    # Add parent
    parent = board.add_parent("Test Parent", "green")
    assert len(board.parents) == 1
    assert parent.name == "Test Parent"
    assert parent.color == "green"
    
    # Add item with parent
    item = board.add_item("Child Item", column.id, parent.id)
    assert item.parent_id == parent.id
    assert item.has_parent is True
    
    # Get parent items
    parent_items = board.get_parent_items(parent.id)
    assert len(parent_items) == 1
    assert parent_items[0].id == item.id
    
    # Get orphaned items
    orphaned_item = board.add_item("Orphaned Item", column.id)
    orphaned_items = board.get_orphaned_items()
    assert len(orphaned_items) == 1
    assert orphaned_items[0].id == orphaned_item.id
    
    # Remove parent
    board.remove_parent(parent.id)
    assert len(board.parents) == 0
    # Item should have parent unlinked
    updated_item = next((i for i in board.items if i.id == item.id), None)
    assert updated_item.parent_id is None


def test_item_movement():
    """Test moving items between columns."""
    board = Board(name="Test Board")
    col1 = board.add_column("Column 1")
    col2 = board.add_column("Column 2")
    
    item = board.add_item("Test Item", col1.id)
    assert item.column_id == col1.id
    
    # Move item
    item.move_to_column(col2.id)
    assert item.column_id == col2.id
    
    # Check column contents
    col1_items = board.get_column_items(col1.id)
    col2_items = board.get_column_items(col2.id)
    assert len(col1_items) == 0
    assert len(col2_items) == 1


if __name__ == "__main__":
    test_board_creation()
    test_column_operations()
    test_item_operations()
    test_parent_operations()
    test_item_movement()
    print("✅ All model tests passed!")