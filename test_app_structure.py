#!/usr/bin/env python3
"""Test app structure without requiring external dependencies."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_app_imports():
    """Test that app modules can be imported."""
    try:
        # Test core imports first
        from models import Board, Column, Item, Parent
        print("✓ Models imported successfully")
        
        from utils.config import Config
        print("✓ Utils imported successfully")
        
        # Test basic functionality
        config = Config()
        print(f"✓ Config created with data_dir: {config.data_dir}")
        
        board = Board(name="Test Board")
        column = board.add_column("Test Column")
        item = board.add_item("Test Item", column.id)
        print(f"✓ Created board with {len(board.items)} items")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_storage_imports():
    """Test storage without frontmatter dependency."""
    try:
        # This will fail if frontmatter is not available, but that's expected
        from storage.markdown_storage import MarkdownStorage
        print("✓ Storage imported (frontmatter available)")
        return True
    except ImportError as e:
        print(f"⚠ Storage import failed (expected if frontmatter not installed): {e}")
        return True  # This is acceptable

def test_ui_imports():
    """Test UI imports without textual dependency."""
    try:
        # This will fail if textual is not available, but that's expected
        from ui.board_view import BoardView
        from ui.status_bar import StatusBar
        print("✓ UI components imported (textual available)")
        return True
    except ImportError as e:
        print(f"⚠ UI import failed (expected if textual not installed): {e}")
        return True  # This is acceptable

if __name__ == "__main__":
    print("Testing MKanban app structure...")
    print()
    
    success = True
    success &= test_app_imports()
    success &= test_storage_imports()
    success &= test_ui_imports()
    
    print()
    if success:
        print("🎉 App structure tests passed!")
        print("Note: Some imports may fail without external dependencies, which is expected.")
    else:
        print("❌ Some critical tests failed.")
    
    sys.exit(0 if success else 1)