#!/usr/bin/env python3
"""MKanban Daemon Executable

Background service that monitors git repositories and automatically
manages kanban tasks based on git branch state, focusing on the
active tmux session.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports BEFORE importing daemon modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon.service_manager import run_daemon
from daemon.core.configuration_service import ConfigurationService, DaemonConfiguration
from infrastructure.tmux.session_manager import (
    get_mkanban_data_path,
    ensure_mkanban_directory,
)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


def create_configuration_service(args) -> ConfigurationService:
    """Create configuration service from command line arguments"""
    from infrastructure.tmux.session_manager import TmuxSessionManager
    from daemon.core.configuration_service import JiraConfig
    import os

    # Determine board name and data path - use session name if in tmux and tmux_session_only is True
    board_name = args.board_name
    data_path = Path(args.data_path) if args.data_path else None

    if args.tmux_session_only:
        tmux_manager = TmuxSessionManager()
        current_session = tmux_manager.get_current_session()
        if current_session:
            board_name = current_session.name

            # Use global data path - session isolation happens via board name
            if not args.data_path:
                data_path = get_mkanban_data_path()

    # Create Jira configuration
    jira_config = JiraConfig()
    if args.enable_jira:
        jira_config.enabled = True
        jira_config.api_url = args.jira_url or os.getenv("JIRA_URL", "")
        jira_config.username = args.jira_username or os.getenv("JIRA_USERNAME", "")
        jira_config.api_token = args.jira_api_token or os.getenv("JIRA_API_TOKEN", "")
        jira_config.board_name = args.jira_board_name
        jira_config.polling_interval = args.jira_polling_interval
        jira_config.bidirectional_sync = args.jira_bidirectional_sync
        jira_config.jql_filter = args.jira_jql_filter or ""
        jira_config.backlog_limit = args.jira_backlog_limit

        if args.jira_projects:
            jira_config.project_keys = [
                key.strip() for key in args.jira_projects.split(",")
            ]

    config = DaemonConfiguration(
        enabled=not args.disable,
        polling_interval=args.polling_interval,
        tmux_session_only=args.tmux_session_only,
        enable_session_task_management=args.enable_session_task_management,
        auto_complete_on_session_switch=args.auto_complete_on_session_switch,
        auto_activate_on_session_switch=args.auto_activate_on_session_switch,
        session_name=board_name,
        default_board=board_name,
        default_column=args.default_column,
        in_progress_column=args.in_progress_column,
        done_column=args.done_column,
        data_path=data_path or get_mkanban_data_path(),
        jira=jira_config,
    )

    if args.branch_patterns:
        config.branch_patterns = args.branch_patterns.split(",")
    if args.excluded_branches:
        config.excluded_branches = args.excluded_branches.split(",")

    return ConfigurationService(config)


def main():
    """Main entry point for the daemon - synchronous wrapper for console script"""
    asyncio.run(async_main())


async def async_main():
    """Async main entry point for the daemon"""
    parser = argparse.ArgumentParser(
        description="MKanban Git Daemon - Automatically manage kanban tasks based on git branches"
    )

    # Basic options
    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable the daemon (for testing configuration)",
    )
    parser.add_argument(
        "--polling-interval",
        type=int,
        default=5,
        help="Polling interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    # Tmux integration
    parser.add_argument(
        "--no-tmux-session-only",
        dest="tmux_session_only",
        action="store_false",
        default=True,
        help="Monitor all repositories, not just the active tmux session",
    )

    # Session-based task management
    parser.add_argument(
        "--disable-session-task-management",
        dest="enable_session_task_management",
        action="store_false",
        default=True,
        help="Disable automatic task management when switching tmux sessions",
    )
    parser.add_argument(
        "--no-auto-complete-on-session-switch",
        dest="auto_complete_on_session_switch",
        action="store_false",
        default=True,
        help="Don't automatically move in-progress tasks to done when switching sessions",
    )
    parser.add_argument(
        "--no-auto-activate-on-session-switch",
        dest="auto_activate_on_session_switch",
        action="store_false",
        default=True,
        help="Don't automatically move current branch task to in-progress when switching sessions",
    )

    # Board configuration
    parser.add_argument(
        "--board-name",
        default="git-branches",
        help="Name of the board for git tasks (default: git-branches)",
    )
    parser.add_argument(
        "--default-column",
        default="to-do",
        help="Default column for new tasks (default: to-do)",
    )
    parser.add_argument(
        "--in-progress-column",
        default="in-progress",
        help="Column for active branch tasks (default: in-progress)",
    )
    parser.add_argument(
        "--done-column",
        default="done",
        help="Column for completed tasks (default: done)",
    )

    # Branch filtering
    parser.add_argument(
        "--branch-patterns",
        help="Comma-separated branch patterns to include (e.g., 'feature/*,bugfix/*')",
    )
    parser.add_argument(
        "--excluded-branches",
        help="Comma-separated branch names to exclude (e.g., 'main,master,develop')",
    )

    # Data path
    parser.add_argument(
        "--data-path",
        help=f"Path for MKanban data (default: {get_mkanban_data_path()})",
    )

    # Jira integration options
    jira_group = parser.add_argument_group("Jira Integration")
    jira_group.add_argument(
        "--enable-jira",
        action="store_true",
        help="Enable Jira integration",
    )
    jira_group.add_argument(
        "--jira-url",
        help="Jira instance URL (e.g., https://company.atlassian.net)",
    )
    jira_group.add_argument(
        "--jira-username",
        help="Jira username (or set JIRA_USERNAME env var)",
    )
    jira_group.add_argument(
        "--jira-api-token",
        help="Jira API token (or set JIRA_API_TOKEN env var)",
    )
    jira_group.add_argument(
        "--jira-projects",
        help="Comma-separated list of Jira project keys (e.g., 'PROJ,FEAT')",
    )
    jira_group.add_argument(
        "--jira-board-name",
        default="jira-tickets",
        help="Name of the MKanban board for Jira tickets (default: jira-tickets)",
    )
    jira_group.add_argument(
        "--jira-polling-interval",
        type=int,
        default=300,
        help="Jira polling interval in seconds (default: 300)",
    )
    jira_group.add_argument(
        "--jira-bidirectional-sync",
        action="store_true",
        help="Enable bidirectional sync (update Jira when MKanban items change)",
    )
    jira_group.add_argument(
        "--jira-jql-filter",
        help="Additional JQL filter for tickets (e.g., 'assignee = currentUser()')",
    )
    jira_group.add_argument(
        "--jira-backlog-limit",
        type=int,
        default=50,
        help="Maximum number of backlog tickets to fetch (-1 for unlimited, default: 50)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("mkanban-daemon")

    try:
        # Ensure data directory exists
        ensure_mkanban_directory()

        # Create configuration
        config_service = create_configuration_service(args)
        config = config_service.config

        logger.info("Starting MKanban daemon...")
        logger.info(f"Data directory: {config.data_path}")
        logger.info(f"Session name: {config.session_name}")
        logger.info(f"Board name: {config.default_board}")
        logger.info(f"Tmux session only: {config.tmux_session_only}")
        logger.info(f"Polling interval: {config.polling_interval}s")
        logger.info(f"Session task management: {config.enable_session_task_management}")
        if config.enable_session_task_management:
            logger.info(
                f"  Auto-complete on session switch: {config.auto_complete_on_session_switch}"
            )
            logger.info(
                f"  Auto-activate on session switch: {config.auto_activate_on_session_switch}"
            )

        # Log Jira configuration
        if config.jira.enabled:
            logger.info("Jira integration enabled:")
            logger.info(f"  URL: {config.jira.api_url}")
            logger.info(f"  Board: {config.jira.board_name}")
            logger.info(f"  Projects: {config.jira.project_keys}")
            logger.info(f"  Polling interval: {config.jira.polling_interval}s")
            logger.info(f"  Bidirectional sync: {config.jira.bidirectional_sync}")
            if config.jira.jql_filter:
                logger.info(f"  JQL filter: {config.jira.jql_filter}")
        else:
            logger.info("Jira integration disabled")

        if config.enabled:
            # Run the daemon
            await run_daemon(config_service)
        else:
            logger.info("Daemon is disabled (--disable flag)")

    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error(f"Daemon failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
