#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage.markdown_storage import MarkdownStorage
from pathlib import Path

def test_load():
    print("Loading board and checking for duplicates...")
    
    # Load the board
    storage = MarkdownStorage(Path('data'))
    board = storage.load_board_by_name('default')

    if not board:
        print('Failed to load board')
        return

    print(f"Board loaded: {board.name}")
    
    # Check for duplicate items
    all_item_ids = []
    for col in board.columns:
        print(f"\nColumn '{col.name}': {len(col.items)} items")
        for item in col.items:
            print(f"  - ID: {item.id}, Title: '{item.title}'")
            all_item_ids.append(item.id)
    
    # Check for duplicates
    unique_ids = set(all_item_ids)
    if len(all_item_ids) != len(unique_ids):
        print(f"\nFOUND DUPLICATES! Total items: {len(all_item_ids)}, Unique IDs: {len(unique_ids)}")
        for item_id in unique_ids:
            count = all_item_ids.count(item_id)
            if count > 1:
                print(f"  Item '{item_id}' appears {count} times")
    else:
        print(f"\nNo duplicates found. Total items: {len(all_item_ids)}")

if __name__ == "__main__":
    test_load()