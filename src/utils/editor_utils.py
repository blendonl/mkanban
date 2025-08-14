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
