#!/usr/bin/env python3
"""
MKanban - A Terminal User Interface Kanban Board
"""

import click
import asyncio
from pathlib import Path
from src.app import MKanbanApp
from src.storage.markdown_storage import MarkdownStorage
from src.models.item import Item


@click.command()
@click.option(
    "--data-dir",
    default="./data",
    help="Directory containing markdown board files",
    type=click.Path(exists=False, path_type=Path),
)
@click.option(
    "--board",
    default=None,
    help="Specific board file to open",
    type=str,
)
@click.option(
    "--new-task-title",
    default=None,
    help="Create a new task with this title (requires --board)",
    type=str,
)
@click.option(
    "--new-task-description",
    default="",
    help="Description for the new task",
    type=str,
)
@click.option(
    "--column",
    default="to-do",
    help="Column to add the new task to (default: to-do)",
    type=str,
)
def main(data_dir: Path, board: str, new_task_title: str, new_task_description: str, column: str):
    """Launch MKanban TUI application."""
    if new_task_title:
        if not board:
            click.echo("Error: --board is required when creating a new task")
            return
        
        create_new_task(data_dir, board, new_task_title, new_task_description, column)
        return
    
    app = MKanbanApp(data_dir=data_dir, initial_board=board)
    app.run()


def create_new_task(data_dir: Path, board_name: str, title: str, description: str, column_name: str):
    """Create a new task in the specified board and column."""
    storage = MarkdownStorage(data_dir)
    
    board = storage.load_board_by_name(board_name)
    if not board:
        click.echo(f"Error: Board '{board_name}' not found")
        return
    
    target_column = None
    for column in board.columns:
        if column.name.lower().replace(' ', '-') == column_name.lower() or column.name.lower() == column_name.lower():
            target_column = column
            break
    
    if not target_column:
        click.echo(f"Error: Column '{column_name}' not found in board '{board_name}'")
        click.echo(f"Available columns: {', '.join([col.name for col in board.columns])}")
        return
    
    new_item = target_column.add_item(title, target_column.id)
    new_item.description = description
    
    storage.save_board(board)
    
    click.echo(f"Successfully created task '{title}' in column '{target_column.name}' of board '{board_name}'")


if __name__ == "__main__":
    asyncio.run(main())
