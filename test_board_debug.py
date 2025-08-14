#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.markdown_storage import MarkdownStorage

def debug_board():
    print("Debugging board state...")
    
    # Load the board
    storage = MarkdownStorage(Path('data'))
    board = storage.load_board_by_name('default')

    if not board:
        print('Failed to load board')
        return

    print(f"Board loaded: {board.name}")
    print(f"Board has {len(board.columns)} columns")
    
    for col in board.columns:
        print(f"\nColumn: '{col.name}' (id: {col.id})")
        print(f"  Items: {len(col.items)}")
        for item in col.items:
            print(f"    - {item.title} (id: {item.id}, column_id: {item.column_id})")

if __name__ == "__main__":
    debug_board()