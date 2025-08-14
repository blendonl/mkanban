import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import click
from ..models.item import Item


def open_editor_for_cli(file_path: str) -> None:
    """Open neovide editor for CLI usage"""
    try:
        subprocess.run(["neovide", file_path, "+10"], check=True)
    except subprocess.CalledProcessError:
        click.echo("Error: Failed to open neovide editor")
        raise
    except FileNotFoundError:
        click.echo("Error: neovide not found. Please install neovide")
        raise


def open_editor_for_app(file_path: str, app_instance) -> None:
    try:
        with app_instance.suspend():
            subprocess.run(["nvim", str(file_path)], check=True)
    except subprocess.CalledProcessError:
        app_instance.notify("Error opening Nvim", severity="error")
        raise
    except FileNotFoundError:
        app_instance.notify("Nvim not found. Please install nvim", severity="error")
        raise


def create_item_with_editor_cli(
    data_dir: Path, board_name: str, column_name: str, storage_class
):
    """Create a new item using CLI editor (neovide)"""
    storage = storage_class(data_dir)

    board = storage.load_board_by_name(board_name)

    boards = storage.load_boards()
    if boards:
        board = boards[0]
    else:
        sample_board = storage.create_sample_board("default")
        storage.save_board(sample_board)
        board = sample_board

    target_column = None
    
    # First, try to find the specified column
    for column in board.columns:
        if (
            column.name.lower().replace(" ", "-") == column_name.lower()
            or column.name.lower() == column_name.lower()
        ):
            target_column = column
            break
    
    # If column not found and we have columns, use the first one as default
    if not target_column and board.columns:
        target_column = board.columns[0]
        click.echo(f"Column '{column_name}' not found. Using first column '{target_column.name}' instead.")
    
    # If still no column found (empty board), create error
    if not target_column:
        click.echo(f"Error: No columns found in board '{board_name}'")
        return

    item = Item(
        title="New Task",
        column_id=target_column.id,
    )
    template_content = f"""---
id: {item.id}
parent_id: null
title: {item.id} 
created_at: {item.created_at}
updated_at: {item.updated_at}
---

# 
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
        temp_file.write(template_content)
        temp_file_path = temp_file.name

    try:
        open_editor_for_cli(temp_file_path)

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

        new_item = target_column.add_item(title)
        new_item.description = description

        storage.save_board(board)

        click.echo(
            f"Successfully created item '{title}' in column '{target_column.name}' of board '{board_name}'"
        )

    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # Error messages already handled in open_editor_for_cli
    except KeyboardInterrupt:
        click.echo("Item creation cancelled")
    finally:
        try:
            Path(temp_file_path).unlink()
        except Exception:
            pass
