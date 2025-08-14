#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.markdown_storage import MarkdownStorage
from src.controllers.column_controller import ColumnController

def test_move_operation():
    print("Testing move operation...")
    
    # Load the board
    storage = MarkdownStorage(Path('data'))
    board = storage.load_board_by_name('default')

    if not board:
        print('Failed to load board')
        return

    print(f"Board loaded: {board.name}")
    
    # Find the first item in To Do column to move
    item_to_move = None
    source_column = None
    for col in board.columns:
        if col.name.lower() == "to do" and col.items:
            item_to_move = col.items[0]
            source_column = col
            break
    
    if not item_to_move:
        print("No item found in To Do column!")
        return
        
    print(f"Found item '{item_to_move.title}' in column '{source_column.name}'")
    
    # Find target column (In Progress)
    target_column = None
    for col in board.columns:
        if col.name.lower() == "in progress":
            target_column = col
            break
    
    if not target_column:
        print("Target column 'In Progress' not found!")
        return
    
    print(f"Moving to column '{target_column.name}'")
    
    # Print state before move
    print("\nState before move:")
    for col in board.columns:
        print(f"  {col.name}: {len(col.items)} items")
        for item in col.items:
            print(f"    - {item.title}")
    
    # Create column controller and move the item
    column_controller = ColumnController(board, source_column, storage)
    success = column_controller.move_item(item_to_move.id, target_column.id)
    
    if success:
        print("\nMove operation successful!")
        
        # Print state after move
        print("\nState after move:")
        for col in board.columns:
            print(f"  {col.name}: {len(col.items)} items")
            for item in col.items:
                print(f"    - {item.title}")
        
        # Check disk state after move
        print("\nDisk state after move:")
        board_dir = Path('data/boards/default')
        for col_dir in board_dir.iterdir():
            if col_dir.is_dir():
                files = list(col_dir.glob('*.md'))
                print(f'  {col_dir.name}: {len(files)} files')
                for f in files:
                    print(f'    - {f.name}')
        
        # Reload board to verify persistence
        print("\nReloading board to verify persistence...")
        reloaded_board = storage.load_board_by_name('default')
        print("Items after reload:")
        for col in reloaded_board.columns:
            print(f"  {col.name}: {len(col.items)} items")
            for item in col.items:
                print(f"    - {item.title}")
                
    else:
        print("Move operation failed!")

if __name__ == "__main__":
    test_move_operation()