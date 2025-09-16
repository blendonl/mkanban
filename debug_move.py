#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.storage.markdown_storage_impl import MarkdownStorage

def debug_move_functions():
    print("Loading board...")
    storage = MarkdownStorage(Path('data'))
    
    try:
        board = storage.load_board_by_name('default')
        if not board:
            print("No board found with name 'default'")
            return
            
        print(f"Board loaded: {board.name}")
        print(f"Columns: {[col.name for col in board.columns]}")
        
        # Print current state
        print("\nCurrent board state:")
        for i, col in enumerate(board.columns):
            print(f"  Column {i}: {col.name} ({col.id}) - {len(col.items)} items")
            for item in col.items:
                print(f"    - {item.title} (id: {item.id})")
                
        # Test that we can find items in all columns
        print("\nTesting item access:")
        for col in board.columns:
            if col.items:
                test_item = col.items[0]
                print(f"Found item '{test_item.title}' in column '{col.name}' with column_id '{test_item.column_id}'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_move_functions()