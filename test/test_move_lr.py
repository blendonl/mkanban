#!/usr/bin/env python3

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.markdown_storage import MarkdownStorage
from src.ui.widgets.board_widget import BoardWidget

async def test_move_left_right():
    print("Testing move left/right functions...")
    
    # Load the board
    storage = MarkdownStorage(Path('data'))
    board = storage.load_board_by_name('default')

    if not board:
        print('Failed to load board')
        return

    print(f"Board loaded: {board.name}")
    
    # Create a mock app with storage
    class MockApp:
        def __init__(self, storage):
            self.storage = storage
    
    mock_app = MockApp(storage)
    
    # Create board widget and set it up
    board_widget = BoardWidget()
    board_widget.app = mock_app
    board_widget.set_board(board)
    
    # Mock get_selected_item to return an item from Review column (middle column)
    review_column = None
    test_item = None
    for col in board.columns:
        if col.name.lower() == "review" and col.items:
            review_column = col
            test_item = col.items[0]
            break
    
    if not test_item:
        print("No item found in Review column for testing!")
        return
    
    print(f"Selected item: '{test_item.title}' in column '{review_column.name}'")
    
    # Mock the get_selected_item method
    def mock_get_selected_item():
        return test_item
    
    board_widget.get_selected_item = mock_get_selected_item
    
    # Mock the _find_column_for_item method
    def mock_find_column_for_item(item):
        class MockColumnWidget:
            def __init__(self, column):
                self.column = column
        return MockColumnWidget(review_column)
    
    board_widget._find_column_for_item = mock_find_column_for_item
    
    # Mock refresh_board method
    def mock_refresh_board(focus_item_id=None):
        print(f"Board refreshed with focus on item: {focus_item_id}")
    
    board_widget.refresh_board = mock_refresh_board
    
    print("\nState before move left:")
    for col in board.columns:
        print(f"  {col.name}: {len(col.items)} items")
        for item in col.items:
            print(f"    - {item.title}")
    
    # Test move left
    print(f"\nTesting move left - moving '{test_item.title}' from Review to In Progress...")
    await board_widget.move_left()
    
    print("\nState after move left:")
    for col in board.columns:
        print(f"  {col.name}: {len(col.items)} items")
        for item in col.items:
            print(f"    - {item.title}")
    
    # Reload board to verify persistence
    print("\nReloading board to verify persistence...")
    reloaded_board = storage.load_board_by_name('default')
    print("Items after reload:")
    for col in reloaded_board.columns:
        print(f"  {col.name}: {len(col.items)} items")
        for item in col.items:
            print(f"    - {item.title}")

if __name__ == "__main__":
    asyncio.run(test_move_left_right())