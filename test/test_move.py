#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from src.controllers.column_controller import ColumnController
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.services.validation_service import ValidationService
from pathlib import Path

def test_move_operation():
    print("Testing move operation...")
    
    # Load the board
    storage = MarkdownStorageImpl(Path('data'))
    validator = ValidationService()
    board_service = BoardService(storage, validator)
    item_service = ItemService(storage, validator)
    board = board_service.get_board('default')

    if not board:
        print('Failed to load board')
        return

    print(f"Board loaded: {board.name}")
    
    # Find the item to move
    item_to_move = None
    source_column = None
    for col in board.columns:
        for item in col.items:
            if item.title == "Item to Move":
                item_to_move = item
                source_column = col
                break
        if item_to_move:
            break
    
    if not item_to_move:
        print("Item 'Item to Move' not found!")
        return
        
    print(f"Found item '{item_to_move.title}' in column '{source_column.name}'")
    
    # Find target column (in-progress)
    target_column = None
    for col in board.columns:
        if col.name.lower() == "in progress":
            target_column = col
            break
    
    if not target_column:
        print("Target column 'In Progress' not found!")
        return
    
    print(f"Moving to column '{target_column.name}'")
    
    # Create column controller and move the item
    column_controller = ColumnController(board, source_column, board_service, item_service)
    success = column_controller.move_item(item_to_move.id, target_column.id)
    
    if success:
        print("Move operation successful!")
        
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