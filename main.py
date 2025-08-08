#!/usr/bin/env python3

import click
import asyncio
import subprocess
import tempfile
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
@click.option(
    "--new-item",
    is_flag=True,
    help="Create a new item with neovim editor (requires --board)",
)
def main(
    data_dir: Path,
    board: str,
    new_task_title: str,
    new_task_description: str,
    column: str,
    new_item: bool,
):
    if new_item:
        if not board:
            click.echo("Error: --board is required when using --new-item")
            return

        create_new_item_with_editor(data_dir, board, column)
        return

    if new_task_title:
        if not board:
            click.echo("Error: --board is required when creating a new task")
            return

        create_new_task(data_dir, board, new_task_title, new_task_description, column)
        return

    app = MKanbanApp(data_dir=data_dir, initial_board=board)
    app.run()


def create_new_task(
    data_dir: Path, board_name: str, title: str, description: str, column_name: str
):
    storage = MarkdownStorage(data_dir)

    board = storage.load_board_by_name(board_name)
    if not board:
        click.echo(f"Error: Board '{board_name}' not found")
        return

    target_column = None
    for column in board.columns:
        if (
            column.name.lower().replace(" ", "-") == column_name.lower()
            or column.name.lower() == column_name.lower()
        ):
            target_column = column
            break

    if not target_column:
        click.echo(f"Error: Column '{column_name}' not found in board '{board_name}'")
        click.echo(
            f"Available columns: {', '.join([col.name for col in board.columns])}"
        )
        return

    new_item = target_column.add_item(title, target_column.id)
    new_item.description = description

    storage.save_board(board)

    click.echo(
        f"Successfully created task '{title}' in column '{
            target_column.name
        }' of board '{board_name}'"
    )


def create_new_item_with_editor(data_dir: Path, board_name: str, column_name: str):
    storage = MarkdownStorage(data_dir)

    board = storage.load_board_by_name(board_name)
    if not board:
        click.echo(f"Error: Board '{board_name}' not found")
        return

    target_column = None
    if column_name == "to-do" and not any(
        col.name.lower().replace(" ", "-") == "to-do" or col.name.lower() == "to-do"
        for col in board.columns
    ):
        target_column = board.columns[0] if board.columns else None
    else:
        for column in board.columns:
            if (
                column.name.lower().replace(" ", "-") == column_name.lower()
                or column.name.lower() == column_name.lower()
            ):
                target_column = column
                break

    if not target_column:
        click.echo(f"Error: Column '{column_name}' not found in board '{board_name}'")
        click.echo(
            f"Available columns: {', '.join([col.name for col in board.columns])}"
        )
        return
    item = Item(
        title="New Task",
        column_id=column.id,
    )
    template_content = f"""
---
metadata:
  column_id: {column.id}
  created_at: {item.created_at} 
  id: {item.id} 
  parent_id: null
  updated_at: {item.updated_at} 
---

# New Item

## Description
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
        temp_file.write(template_content)
        temp_file_path = temp_file.name

    try:
        subprocess.run(["nvim", temp_file_path], check=True)

        with open(temp_file_path, "r") as f:
            edited_content = f.read()

        title_line = next(
            (
                line
                for line in edited_content.split("\n")
                if line.strip().startswith("# ")
            ),
            None,
        )
        title = title_line.replace("# ", "").strip() if title_line else "New Item"

        description = edited_content.strip()

        if not title or title == "New Item":
            click.echo("No title specified. Aborting item creation.")
            return

        new_item = target_column.add_item(title, target_column.id)
        new_item.description = description

        storage.save_board(board)

        click.echo(
            f"Successfully created item '{title}' in column '{target_column.name}' of board '{board_name}'"
        )

    except subprocess.CalledProcessError:
        click.echo("Error: Failed to open neovim editor")
    except KeyboardInterrupt:
        click.echo("Item creation cancelled")
    finally:
        try:
            Path(temp_file_path).unlink()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
