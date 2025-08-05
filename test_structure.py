#!/usr/bin/env python3
"""Simple test to verify our code structure without external dependencies."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that our modules can be imported."""
    try:
        from models import Board, Column, Item, Parent
        print("✓ Models imported successfully")
        
        # Test basic model creation
        board = Board(name="Test Board")
        column = board.add_column("Test Column")
        item = board.add_item("Test Item", column.id)
        parent = board.add_parent("Test Parent")
        
        print(f"✓ Created board '{board.name}' with {len(board.columns)} columns, {len(board.items)} items, {len(board.parents)} parents")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error creating models: {e}")
        return False

def test_board_operations():
    """Test board operations."""
    try:
        from models import Board
        
        board = Board(name="Operations Test")
        
        # Add columns
        todo = board.add_column("To Do", 0)
        progress = board.add_column("In Progress", 1) 
        done = board.add_column("Done", 2)
        
        # Add parent
        feature = board.add_parent("Feature Work", "green")
        
        # Add items
        item1 = board.add_item("Task 1", todo.id)
        item2 = board.add_item("Task 2", progress.id, feature.id)
        item3 = board.add_item("Task 3", done.id)
        
        # Test queries
        todo_items = board.get_column_items(todo.id)
        feature_items = board.get_parent_items(feature.id)
        orphaned = board.get_orphaned_items()
        
        print(f"✓ Board operations work:")
        print(f"  - To Do items: {len(todo_items)}")
        print(f"  - Feature items: {len(feature_items)}")
        print(f"  - Orphaned items: {len(orphaned)}")
        
        # Test item movement
        item1.move_to_column(progress.id)
        progress_items = board.get_column_items(progress.id)
        print(f"  - Progress items after move: {len(progress_items)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Board operations error: {e}")
        return False

if __name__ == "__main__":
    print("Testing MKanban structure...")
    print()
    
    success = True
    success &= test_imports()
    success &= test_board_operations()
    
    print()
    if success:
        print("🎉 All tests passed! Structure is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)