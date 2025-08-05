#!/usr/bin/env python3
"""Debug version of main.py to catch the tab_size error."""

import traceback
from pathlib import Path
import click
from src.app import MKanbanApp

@click.command()
@click.option('--data-dir', type=click.Path(exists=True), default="./data",
              help="Directory containing markdown board files")
@click.option('--board', help="Specific board file to open")
def main(data_dir: str, board: str):
    """Launch MKanban TUI application with debug error tracking."""
    try:
        data_path = Path(data_dir)
        app = MKanbanApp(data_path, board)
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        
        # Check if it's the tab_size error
        if 'tab_size' in str(e):
            print("\n--- TAB_SIZE ERROR DETECTED ---")
            print("This error suggests an attribute is being set on a string instead of a widget")
            print("Stack trace above should show the exact location")

if __name__ == "__main__":
    main()