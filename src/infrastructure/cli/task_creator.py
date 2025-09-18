import subprocess
import tempfile
import click
from pathlib import Path
from typing import Optional
from ...core.exceptions import MKanbanError, BoardNotFoundError, ColumnNotFoundError
from ...config.settings import Settings
from ...services.board_service import BoardService
from ...services.item_service import ItemService
from ...services.validation_service import ValidationService
from ..storage.markdown_storage_impl import MarkdownStorageImpl


class TaskCreator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._storage = MarkdownStorageImpl(Path(settings.data_dir))
        self._validator = ValidationService()
        self._board_service = BoardService(self._storage, self._validator)
        self._item_service = ItemService(self._storage, self._validator)

    def create_task_via_cli(
        self, 
        board_name: str, 
        title: str, 
        description: str, 
        column_name: str
    ) -> None:
        try:
            board = self._board_service.get_board_by_name(board_name)
        except BoardNotFoundError:
            click.echo(f"Error: Board '{board_name}' not found")
            available_boards = self._board_service.list_board_names()
            if available_boards:
                click.echo(f"Available boards: {', '.join(available_boards)}")
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
            click.echo(f"Available columns: {', '.join([col.name for col in board.columns])}")
            return

        try:
            self._item_service.create_item(board, target_column.id, title, description)
            self._board_service.save_board(board)
            
            click.echo(
                f"Successfully created task '{title}' in column '{target_column.name}' of board '{board_name}'"
            )
        except MKanbanError as e:
            click.echo(f"Error: {e}")

    def create_item_with_editor(self, board_name: str, column_name: str) -> None:
        try:
            board = self._board_service.get_or_create_sample_board(board_name)
        except MKanbanError as e:
            click.echo(f"Error: {e}")
            return

        target_column = self._find_target_column(board, column_name)
        if not target_column:
            click.echo(f"Error: No columns found in board '{board_name}'")
            return

        template_content = self._create_item_template()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_file.write(template_content)
            temp_file_path = temp_file.name

        try:
            self._open_editor_for_cli(temp_file_path)

            with open(temp_file_path, "r") as f:
                edited_content = f.read()

            title = self._extract_title_from_content(edited_content)
            if not title or title == "New Item":
                click.echo("No title specified. Aborting item creation.")
                return

            self._item_service.create_item(
                board, target_column.id, title, edited_content.strip()
            )
            self._board_service.save_board(board)

            click.echo(
                f"Successfully created item '{title}' in column '{target_column.name}' of board '{board_name}'"
            )

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        except KeyboardInterrupt:
            click.echo("Item creation cancelled")
        except MKanbanError as e:
            click.echo(f"Error: {e}")
        finally:
            try:
                Path(temp_file_path).unlink()
            except Exception:
                pass

    def _find_target_column(self, board, column_name: str):
        target_column = None
        
        for column in board.columns:
            if (
                column.name.lower().replace(" ", "-") == column_name.lower()
                or column.name.lower() == column_name.lower()
            ):
                target_column = column
                break
        
        if not target_column and board.columns:
            target_column = board.columns[0]
            click.echo(f"Column '{column_name}' not found. Using first column '{target_column.name}' instead.")
        
        return target_column

    def _create_item_template(self) -> str:
        from ...utils.date_utils import now
        from uuid import uuid4
        
        item_id = str(uuid4())[:8]
        timestamp = now()
        
        return f"""---
id: {item_id}
parent_id: null
title: New Item
created_at: {timestamp}
updated_at: {timestamp}
---

# 
"""

    def _extract_title_from_content(self, content: str) -> str:
        title_line = next(
            (
                line
                for line in content.split("\n")
                if line.strip().startswith("# ")
            ),
            None,
        )
        return title_line.replace("# ", "").strip() if title_line else "New Item"

    def show_current_task(self, board_name: str, column_name: str) -> None:
        try:
            board = self._board_service.get_board_by_name(board_name)
        except BoardNotFoundError:
            click.echo(f"Error: Board '{board_name}' not found")
            available_boards = self._board_service.list_board_names()
            if available_boards:
                click.echo(f"Available boards: {', '.join(available_boards)}")
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
            click.echo(f"Available columns: {', '.join([col.name for col in board.columns])}")
            return

        if not target_column.items:
            click.echo(f"No tasks found in column '{target_column.name}'")
            return

        # Get the first item from the column
        first_item = target_column.items[0]
        
        # Find the item's file path
        from ..storage.file_operations import get_board_directory_path, get_column_directory_path, find_item_file_by_id
        
        data_dir = self.settings.get_data_dir()
        boards_dir = data_dir / "boards"
        board_dir = get_board_directory_path(boards_dir, board_name)
        column_dir = get_column_directory_path(board_dir, target_column.name)
        item_file = find_item_file_by_id(column_dir, first_item.id)
        
        if not item_file or not item_file.exists():
            click.echo(f"Error: Task file not found for '{first_item.title}'")
            return

        try:
            self._open_editor_for_current_task(str(item_file))
            click.echo(f"Opened task '{first_item.title}' from column '{target_column.name}'")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            click.echo(f"Error opening editor: {e}")

    def _open_editor_for_current_task(self, file_path: str) -> None:
        from ...config.environment import Environment
        editor = Environment.get_editor()
        
        try:
            subprocess.run([editor, file_path], check=True)
        except subprocess.CalledProcessError:
            click.echo(f"Error: Failed to open {editor} editor")
            raise
        except FileNotFoundError:
            click.echo(f"Error: {editor} not found. Please install {editor} or set EDITOR environment variable")
            raise

    def _open_editor_for_cli(self, file_path: str) -> None:
        try:
            subprocess.run(["neovide", file_path, "+10"], check=True)
        except subprocess.CalledProcessError:
            click.echo("Error: Failed to open neovide editor")
            raise
        except FileNotFoundError:
            click.echo("Error: neovide not found. Please install neovide")
            raise