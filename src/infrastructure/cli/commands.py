import click
from pathlib import Path
from typing import Optional
from ...core.exceptions import MKanbanError


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
    help="Create a new item with neovide editor (requires --board)",
)
def main_command(
    data_dir: Path,
    board: Optional[str],
    new_task_title: Optional[str],
    new_task_description: str,
    column: str,
    new_item: bool,
) -> None:
    try:
        from .task_creator import TaskCreator
        from ...config.settings import Settings
        
        settings = Settings(data_dir=str(data_dir))
        task_creator = TaskCreator(settings)
        
        if new_item:
            if not board:
                click.echo("Error: --board is required when using --new-item")
                return
            
            task_creator.create_item_with_editor(board, column)
            return
        
        if new_task_title:
            if not board:
                click.echo("Error: --board is required when creating a new task")
                return
            
            task_creator.create_task_via_cli(board, new_task_title, new_task_description, column)
            return
        
        from ...app import MKanbanApp
        app = MKanbanApp(data_dir=data_dir, initial_board=board)
        app.run()
        
    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


if __name__ == "__main__":
    main_command()