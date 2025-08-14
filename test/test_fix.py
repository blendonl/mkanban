#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from storage.markdown_storage import MarkdownStorage
from pathlib import Path

def test_storage_fix():
    print("Testing storage fix...")
    
    # Load the board
    storage = MarkdownStorage(Path('data'))
    board = storage.load_board_by_name('default')

    if board:
        print('Board loaded successfully')
        print('Columns:')
        for col in board.columns:
            print(f'  {col.name}: {len(col.items)} items')
            for item in col.items:
                print(f'    - {item.id}: {item.title}')
        
        # Now save the board to trigger the cleanup
        storage.save_board(board)
        print('Board saved successfully - orphaned files should be cleaned up')
        
        # Check disk state after save
        print("\nDisk state after save:")
        board_dir = Path('data/boards/default')
        for col_dir in board_dir.iterdir():
            if col_dir.is_dir():
                files = list(col_dir.glob('*.md'))
                print(f'  {col_dir.name}: {len(files)} files')
                for f in files:
                    print(f'    - {f.name}')
    else:
        print('Failed to load board')

if __name__ == "__main__":
    test_storage_fix()