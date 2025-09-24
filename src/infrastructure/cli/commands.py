import click
from pathlib import Path
from typing import Optional
from src.core.exceptions import MKanbanError
from src.core.dependency_container import get_config_manager, get_board_service
from .daemon_commands import daemon_command


def get_board_names(ctx, param, incomplete):
    """Completion function for board names."""
    try:
        config_manager = get_config_manager()
        boards_path = Path(config_manager.get_boards_path())

        if not boards_path.exists():
            return []

        board_service = get_board_service()
        board_names = board_service.list_board_names()

        return [name for name in board_names if name.startswith(incomplete)]
    except Exception:
        return []


def get_column_names(ctx, param, incomplete):
    """Completion function for column names."""
    try:
        from src.core.dependency_container import get_board_service

        board_name = ctx.params.get("board")
        if not board_name:
            return []

        board_service = get_board_service()
        board = board_service.get_board(board_name)

        if not board:
            return []

        column_names = [col.name for col in board.columns]
        return [name for name in column_names if name.startswith(incomplete)]
    except Exception:
        return []


@click.group(invoke_without_command=True)
@click.option(
    "--completion",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Show completion script for the specified shell",
)
@click.option(
    "--boards-path",
    default=None,
    help="Path to directory containing markdown board files",
    type=click.Path(exists=False, path_type=Path),
)
@click.option(
    "--board",
    default=None,
    help="Specific board file to open",
    type=str,
    shell_complete=get_board_names,
)
@click.option(
    "--new-to-do",
    is_flag=True,
    help="Create a new item with neovide editor (requires --board)",
)
@click.option(
    "--show-current-task",
    is_flag=True,
    help="Show and edit the first task in the specified column (requires --board and --column)",
)
@click.option(
    "--column",
    default="to-do",
    help="Column for --show-current-task (default: to-do)",
    type=str,
    shell_complete=get_column_names,
)
@click.option(
    "--list-todos",
    default=None,
    help="List all todos from current board and pipe to selector command",
    type=str,
    metavar="SELECTOR_COMMAND",
)
@click.pass_context
def main_command(
    ctx: click.Context,
    completion: Optional[str],
    boards_path: Optional[Path],
    board: Optional[str],
    new_to_do: bool,
    show_current_task: bool,
    column: str,
    list_todos: Optional[str],
) -> None:
    try:
        # Handle completion commands first
        if completion:
            shell_name = completion.lower()
            completion_script = {
                "bash": """_mkanban_completion() {
    local cur prev words cword
    _init_completion || return

    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   _MKANBAN_COMPLETE=bash_complete $1 ) )
    return 0
}

complete -F _mkanban_completion mkanban""",
                "zsh": """#compdef mkanban

_mkanban() {
    eval $(env COMMANDLINE="${words[*]}" _MKANBAN_COMPLETE=zsh_complete mkanban)
}

compdef _mkanban mkanban""",
                "fish": '''function __fish_mkanban_complete
    env _MKANBAN_COMPLETE=fish_complete mkanban (commandline -cp)
end

complete --command mkanban --no-files --arguments "(__fish_mkanban_complete)"''',
            }
            click.echo(completion_script.get(shell_name, ""))
            return

        # If a subcommand was invoked, don't run the main app
        if ctx.invoked_subcommand is not None:
            return

        from src.core.dependency_container import (
            get_config_manager,
            get_task_creator,
            get_todo_selector,
        )

        config_manager = get_config_manager()

        # Update configuration with provided boards path if needed
        if boards_path is not None:
            config_manager.update_configuration(boards_path=str(boards_path))

        actual_boards_path = config_manager.get_boards_path()
        task_creator = get_task_creator()

        if list_todos:
            todo_selector = get_todo_selector()
            todo_selector.run_todo_selector(list_todos, board)
            return

        if show_current_task:
            if not board:
                click.echo("Error: --board is required when using --show-current-task")
                return

            task_creator.show_current_task(board, column)
            return

        if new_to_do:
            if not board:
                click.echo("Error: --board is required when using --new-to-do")
                return

            task_creator.create_item_with_editor(board, column)
            return

        from src.app import MKanbanApp

        app = MKanbanApp(boards_path=actual_boards_path, initial_board=board)
        app.run()

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


@main_command.command("new-task")
@click.argument("title", type=str)
@click.option(
    "--description",
    default="",
    help="Description for the new task",
    type=str,
)
@click.option(
    "--column",
    default="to-do",
    help="Column to add the new task to (default: to-do)",
    type=str,
    shell_complete=get_column_names,
)
@click.option(
    "--board",
    required=True,
    help="Board to add the new task to",
    type=str,
    shell_complete=get_board_names,
)
def new_task_command(
    title: str,
    description: str,
    column: str,
    board: str,
) -> None:
    """Create a new task with the specified title."""
    try:
        from src.core.dependency_container import get_task_creator

        task_creator = get_task_creator()
        task_creator.create_task_via_cli(board, title, description, column)

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


# Import and add daemon command group

main_command.add_command(daemon_command)


if __name__ == "__main__":
    main_command()
