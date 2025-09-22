import click
from pathlib import Path
from typing import Optional
from src.core.exceptions import MKanbanError


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
@click.option(
    "--show-current-task",
    is_flag=True,
    help="Show and edit the first task in the specified column (requires --board and --column)",
)
@click.option(
    "--daemon",
    type=click.Choice(["start", "stop", "status", "restart"]),
    help="Daemon management commands",
)
@click.option(
    "--list-todos",
    is_flag=True,
    help="List all todos from current board and pipe to selector command",
)
@click.option(
    "--selector-command",
    default="fzf",
    help="External command to use for todo selection (e.g., 'rofi -dmenu', 'dmenu', 'fzf')",
    type=str,
)
def main_command(
    data_dir: Path,
    board: Optional[str],
    new_task_title: Optional[str],
    new_task_description: str,
    column: str,
    new_item: bool,
    show_current_task: bool,
    daemon: Optional[str],
    list_todos: bool,
    selector_command: str,
) -> None:
    try:
        # Handle daemon commands first
        if daemon:
            from src.infrastructure.cli.daemon_manager import DaemonManager

            daemon_manager = DaemonManager()
            daemon_manager.handle_daemon_command(daemon)
            return

        from src.infrastructure.cli.task_creator import TaskCreator
        from src.core.dependency_container import get_config_manager, get_container

        config_manager = get_config_manager()

        # Update configuration with provided data directory if needed
        if data_dir != Path("./data"):
            config_manager.update_configuration(data_dir=str(data_dir))

        actual_data_dir = config_manager.get_data_dir()
        container = get_container()
        task_creator = TaskCreator(container, actual_data_dir)

        if list_todos:
            from src.infrastructure.cli.todo_selector import TodoSelector

            todo_selector = TodoSelector(container, actual_data_dir)
            todo_selector.run_todo_selector(selector_command, board)
            return

        if show_current_task:
            if not board:
                click.echo("Error: --board is required when using --show-current-task")
                return

            task_creator.show_current_task(board, column)
            return

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

            task_creator.create_task_via_cli(
                board, new_task_title, new_task_description, column
            )
            return

        from app import MKanbanApp

        app = MKanbanApp(data_dir=data_dir, initial_board=board)
        app.run()

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


if __name__ == "__main__":
    main_command()
