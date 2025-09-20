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

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon.service_manager import ServiceManager, run_daemon
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

    config = DaemonConfiguration(
        enabled=not args.disable,
        polling_interval=args.polling_interval,
        tmux_session_only=args.tmux_session_only,
        session_name=board_name,
        default_board=board_name,
        default_column=args.default_column,
        in_progress_column=args.in_progress_column,
        done_column=args.done_column,
        data_path=data_path or get_mkanban_data_path(),
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
        help=f"Path for MKanban data (default: $MKANBAN_PATH or {get_mkanban_data_path()})",
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

        logger.info(f"Starting MKanban daemon...")
        logger.info(f"Data directory: {config.data_path}")
        logger.info(f"Session name: {config.session_name}")
        logger.info(f"Board name: {config.default_board}")
        logger.info(f"Tmux session only: {config.tmux_session_only}")
        logger.info(f"Polling interval: {config.polling_interval}s")

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
