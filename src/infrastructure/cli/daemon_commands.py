"""Daemon CLI Commands

Handles daemon management commands as a proper command group with subcommands
for start, stop, status, and restart, including Jira integration options.
"""

import click
from typing import Optional
from src.core.exceptions import MKanbanError


@click.group("daemon")
def daemon_command():
    """Daemon management commands."""
    pass


@daemon_command.command("start")
@click.option(
    "--enable-jira",
    is_flag=True,
    help="Enable Jira integration",
)
@click.option(
    "--jira-url",
    help="Jira instance URL (e.g., https://company.atlassian.net)",
)
@click.option(
    "--jira-username",
    help="Jira username (or set JIRA_USERNAME env var)",
)
@click.option(
    "--jira-api-token",
    help="Jira API token (or set JIRA_API_TOKEN env var)",
)
@click.option(
    "--jira-projects",
    help="Comma-separated list of Jira project keys (e.g., 'PROJ,FEAT')",
)
@click.option(
    "--jira-board-name",
    default="jira-tickets",
    help="Name of the MKanban board for Jira tickets (default: jira-tickets)",
)
@click.option(
    "--jira-polling-interval",
    type=int,
    default=300,
    help="Jira polling interval in seconds (default: 300)",
)
@click.option(
    "--jira-bidirectional-sync",
    is_flag=True,
    help="Enable bidirectional sync (update Jira when MKanban items change)",
)
@click.option(
    "--jira-jql-filter",
    help="Additional JQL filter for tickets (e.g., 'assignee = currentUser()')",
)
@click.option(
    "--jira-backlog-limit",
    type=int,
    default=50,
    help="Maximum number of backlog tickets to fetch (-1 for unlimited, default: 50)",
)
@click.option(
    "--board-name",
    default="git-branches",
    help="Name of the board for git tasks (default: git-branches)",
)
@click.option(
    "--polling-interval",
    type=int,
    default=5,
    help="Polling interval in seconds (default: 5)",
)
@click.option(
    "--no-tmux-session-only",
    "tmux_session_only",
    is_flag=True,
    flag_value=False,
    default=True,
    help="Monitor all repositories, not just the active tmux session",
)
@click.option(
    "--disable-session-task-management",
    "enable_session_task_management",
    is_flag=True,
    flag_value=False,
    default=True,
    help="Disable automatic task management when switching tmux sessions",
)
@click.option(
    "--data-path",
    help="Path for MKanban data",
)
def daemon_start(
    enable_jira: bool,
    jira_url: Optional[str],
    jira_username: Optional[str],
    jira_api_token: Optional[str],
    jira_projects: Optional[str],
    jira_board_name: str,
    jira_polling_interval: int,
    jira_bidirectional_sync: bool,
    jira_jql_filter: Optional[str],
    jira_backlog_limit: int,
    board_name: str,
    polling_interval: int,
    tmux_session_only: bool,
    enable_session_task_management: bool,
    data_path: Optional[str],
) -> None:
    """Start the daemon with optional Jira integration."""
    try:
        from src.core.dependency_container import get_daemon_manager

        daemon_manager = get_daemon_manager()

        # Build daemon arguments
        daemon_args = [
            "--board-name", board_name,
            "--polling-interval", str(polling_interval),
        ]

        if data_path:
            daemon_args.extend(["--data-path", data_path])

        if not tmux_session_only:
            daemon_args.append("--no-tmux-session-only")

        if not enable_session_task_management:
            daemon_args.append("--disable-session-task-management")

        # Add Jira options if enabled
        if enable_jira:
            daemon_args.append("--enable-jira")

            if jira_url:
                daemon_args.extend(["--jira-url", jira_url])
            if jira_username:
                daemon_args.extend(["--jira-username", jira_username])
            if jira_api_token:
                daemon_args.extend(["--jira-api-token", jira_api_token])
            if jira_projects:
                daemon_args.extend(["--jira-projects", jira_projects])
            if jira_board_name != "jira-tickets":
                daemon_args.extend(["--jira-board-name", jira_board_name])
            if jira_polling_interval != 300:
                daemon_args.extend(["--jira-polling-interval", str(jira_polling_interval)])
            if jira_bidirectional_sync:
                daemon_args.append("--jira-bidirectional-sync")
            if jira_jql_filter:
                daemon_args.extend(["--jira-jql-filter", jira_jql_filter])
            if jira_backlog_limit != 50:
                daemon_args.extend(["--jira-backlog-limit", str(jira_backlog_limit)])

        daemon_manager.start_daemon_with_args(daemon_args)

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


@daemon_command.command("stop")
def daemon_stop() -> None:
    """Stop the daemon."""
    try:
        from src.core.dependency_container import get_daemon_manager

        daemon_manager = get_daemon_manager()
        daemon_manager.handle_daemon_command("stop")

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


@daemon_command.command("status")
def daemon_status() -> None:
    """Show daemon status."""
    try:
        from src.core.dependency_container import get_daemon_manager

        daemon_manager = get_daemon_manager()
        daemon_manager.handle_daemon_command("status")

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


@daemon_command.command("restart")
@click.option(
    "--enable-jira",
    is_flag=True,
    help="Enable Jira integration",
)
@click.option(
    "--jira-url",
    help="Jira instance URL (e.g., https://company.atlassian.net)",
)
@click.option(
    "--jira-username",
    help="Jira username (or set JIRA_USERNAME env var)",
)
@click.option(
    "--jira-api-token",
    help="Jira API token (or set JIRA_API_TOKEN env var)",
)
@click.option(
    "--jira-projects",
    help="Comma-separated list of Jira project keys (e.g., 'PROJ,FEAT')",
)
@click.option(
    "--jira-board-name",
    default="jira-tickets",
    help="Name of the MKanban board for Jira tickets (default: jira-tickets)",
)
@click.option(
    "--jira-polling-interval",
    type=int,
    default=300,
    help="Jira polling interval in seconds (default: 300)",
)
@click.option(
    "--jira-bidirectional-sync",
    is_flag=True,
    help="Enable bidirectional sync (update Jira when MKanban items change)",
)
@click.option(
    "--jira-jql-filter",
    help="Additional JQL filter for tickets (e.g., 'assignee = currentUser()')",
)
@click.option(
    "--jira-backlog-limit",
    type=int,
    default=50,
    help="Maximum number of backlog tickets to fetch (-1 for unlimited, default: 50)",
)
@click.option(
    "--board-name",
    default="git-branches",
    help="Name of the board for git tasks (default: git-branches)",
)
@click.option(
    "--polling-interval",
    type=int,
    default=5,
    help="Polling interval in seconds (default: 5)",
)
@click.option(
    "--no-tmux-session-only",
    "tmux_session_only",
    is_flag=True,
    flag_value=False,
    default=True,
    help="Monitor all repositories, not just the active tmux session",
)
@click.option(
    "--disable-session-task-management",
    "enable_session_task_management",
    is_flag=True,
    flag_value=False,
    default=True,
    help="Disable automatic task management when switching tmux sessions",
)
@click.option(
    "--data-path",
    help="Path for MKanban data",
)
def daemon_restart(
    enable_jira: bool,
    jira_url: Optional[str],
    jira_username: Optional[str],
    jira_api_token: Optional[str],
    jira_projects: Optional[str],
    jira_board_name: str,
    jira_polling_interval: int,
    jira_bidirectional_sync: bool,
    jira_jql_filter: Optional[str],
    jira_backlog_limit: int,
    board_name: str,
    polling_interval: int,
    tmux_session_only: bool,
    enable_session_task_management: bool,
    data_path: Optional[str],
) -> None:
    """Restart the daemon with optional Jira integration."""
    try:
        from src.core.dependency_container import get_daemon_manager

        daemon_manager = get_daemon_manager()

        # Stop first
        daemon_manager.handle_daemon_command("stop")

        # Build daemon arguments
        daemon_args = [
            "--board-name", board_name,
            "--polling-interval", str(polling_interval),
        ]

        if data_path:
            daemon_args.extend(["--data-path", data_path])

        if not tmux_session_only:
            daemon_args.append("--no-tmux-session-only")

        if not enable_session_task_management:
            daemon_args.append("--disable-session-task-management")

        # Add Jira options if enabled
        if enable_jira:
            daemon_args.append("--enable-jira")

            if jira_url:
                daemon_args.extend(["--jira-url", jira_url])
            if jira_username:
                daemon_args.extend(["--jira-username", jira_username])
            if jira_api_token:
                daemon_args.extend(["--jira-api-token", jira_api_token])
            if jira_projects:
                daemon_args.extend(["--jira-projects", jira_projects])
            if jira_board_name != "jira-tickets":
                daemon_args.extend(["--jira-board-name", jira_board_name])
            if jira_polling_interval != 300:
                daemon_args.extend(["--jira-polling-interval", str(jira_polling_interval)])
            if jira_bidirectional_sync:
                daemon_args.append("--jira-bidirectional-sync")
            if jira_jql_filter:
                daemon_args.extend(["--jira-jql-filter", jira_jql_filter])
            if jira_backlog_limit != 50:
                daemon_args.extend(["--jira-backlog-limit", str(jira_backlog_limit)])

        daemon_manager.start_daemon_with_args(daemon_args)

    except MKanbanError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")