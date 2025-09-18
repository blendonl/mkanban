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

from daemon.service_manager import ServiceManager, DaemonConfig, run_daemon
from config.settings import Settings
from infrastructure.tmux.session_manager import get_mkanban_data_path, ensure_mkanban_directory


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def create_daemon_config(args) -> DaemonConfig:
    """Create daemon configuration from command line arguments"""
    return DaemonConfig(
        enabled=not args.disable,
        polling_interval=args.polling_interval,
        tmux_session_only=args.tmux_session_only,
        default_board=args.board_name,
        default_column=args.default_column,
        in_progress_column=args.in_progress_column,
        done_column=args.done_column,
        branch_patterns=args.branch_patterns.split(',') if args.branch_patterns else None,
        excluded_branches=args.excluded_branches.split(',') if args.excluded_branches else None,
        data_path=Path(args.data_path) if args.data_path else None,
    )


def create_settings(daemon_config: DaemonConfig) -> Settings:
    """Create settings for the daemon"""
    return Settings(data_dir=str(daemon_config.data_path))


async def main():
    """Main entry point for the daemon"""
    parser = argparse.ArgumentParser(
        description="MKanban Git Daemon - Automatically manage kanban tasks based on git branches"
    )
    
    # Basic options
    parser.add_argument(
        "--disable", 
        action="store_true",
        help="Disable the daemon (for testing configuration)"
    )
    parser.add_argument(
        "--polling-interval",
        type=int,
        default=5,
        help="Polling interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    
    # Tmux integration
    parser.add_argument(
        "--no-tmux-session-only",
        dest="tmux_session_only",
        action="store_false",
        default=True,
        help="Monitor all repositories, not just the active tmux session"
    )
    
    # Board configuration
    parser.add_argument(
        "--board-name",
        default="git-branches",
        help="Name of the board for git tasks (default: git-branches)"
    )
    parser.add_argument(
        "--default-column",
        default="to-do",
        help="Default column for new tasks (default: to-do)"
    )
    parser.add_argument(
        "--in-progress-column",
        default="in-progress",
        help="Column for active branch tasks (default: in-progress)"
    )
    parser.add_argument(
        "--done-column",
        default="done",
        help="Column for completed tasks (default: done)"
    )
    
    # Branch filtering
    parser.add_argument(
        "--branch-patterns",
        help="Comma-separated branch patterns to include (e.g., 'feature/*,bugfix/*')"
    )
    parser.add_argument(
        "--excluded-branches",
        help="Comma-separated branch names to exclude (e.g., 'main,master,develop')"
    )
    
    # Data path
    parser.add_argument(
        "--data-path",
        help=f"Path for MKanban data (default: $MKANBAN_PATH or {get_mkanban_data_path()})"
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
        daemon_config = create_daemon_config(args)
        settings = create_settings(daemon_config)
        
        logger.info(f"Starting MKanban daemon...")
        logger.info(f"Data directory: {daemon_config.data_path}")
        logger.info(f"Board name: {daemon_config.default_board}")
        logger.info(f"Tmux session only: {daemon_config.tmux_session_only}")
        logger.info(f"Polling interval: {daemon_config.polling_interval}s")
        
        if daemon_config.enabled:
            # Run the daemon
            await run_daemon(settings, daemon_config)
        else:
            logger.info("Daemon is disabled (--disable flag)")
            
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error(f"Daemon failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())