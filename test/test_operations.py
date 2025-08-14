#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from src.controllers.column_controller import ColumnController
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.services.validation_service import ValidationService
from pathlib import Path

def test_operations():
    print("Testing move and delete operations...")
    
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
    
    print("\nInitial state:")
    for col in board.columns:
        print(f"  {col.name}: {len(col.items)} items")
        for item in col.items:
            print(f"    - {item.id}: {item.title}")
    
    # Test 1: Move an item from To Do to In Progress
    print("\n=== TEST 1: Move item ===")
    todo_column = next((col for col in board.columns if col.name == "To Do"), None)
    in_progress_column = next((col for col in board.columns if col.name == "In Progress"), None)
    
    if todo_column and in_progress_column and todo_column.items:
        item_to_move = todo_column.items[0]  # Move first item
        print(f"Moving '{item_to_move.title}' from '{todo_column.name}' to '{in_progress_column.name}'")
        
        # Check files before move
        print("Files before move:")
        print_file_state()
        
        # Perform the move operation
        column_controller = ColumnController(board, todo_column, board_service, item_service)
        success = column_controller.move_item(item_to_move.id, in_progress_column.id)
        
        if success:
            print("Move operation successful!")
            
            # Check files after move
            print("Files after move:")
            print_file_state()
            
            # Reload board to verify persistence
            print("\nReloading board to verify persistence...")
            reloaded_board = storage.load_board_by_name('default')
            print("Items after reload:")
            for col in reloaded_board.columns:
                print(f"  {col.name}: {len(col.items)} items")
                for item in col.items:
                    print(f"    - {item.id}: {item.title}")
        else:
            print("Move operation failed!")
    
    # Test 2: Delete an item
    print("\n=== TEST 2: Delete item ===")
    # Reload the board for fresh state
    board = storage.load_board_by_name('default')
    done_column = next((col for col in board.columns if col.name == "Done"), None)
    
    if done_column and done_column.items:
        item_to_delete = done_column.items[0]  # Delete first item from Done
        print(f"Deleting '{item_to_delete.title}' from '{done_column.name}'")
        
        # Check files before delete
        print("Files before delete:")
        print_file_state()
        
        # Perform the delete operation
        column_controller = ColumnController(board, done_column, storage)
        success = column_controller.delete_item(item_to_delete)
        
        if success:
            print("Delete operation successful!")
            
            # Check files after delete
            print("Files after delete:")
            print_file_state()
            
            # Reload board to verify persistence
            print("\nReloading board to verify persistence...")
            reloaded_board = storage.load_board_by_name('default')
            print("Items after reload:")
            for col in reloaded_board.columns:
                print(f"  {col.name}: {len(col.items)} items")
                for item in col.items:
                    print(f"    - {item.id}: {item.title}")
        else:
            print("Delete operation failed!")

def print_file_state():
    board_dir = Path('data/boards/default')
    for col_dir in board_dir.iterdir():
        if col_dir.is_dir():
            files = list(col_dir.glob('*.md'))
            print(f"    {col_dir.name}: {len(files)} files")
            for f in files:
                print(f"      - {f.name}")

if __name__ == "__main__":
    test_operations()