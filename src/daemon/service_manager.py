"""Daemon Service Manager

Handles the lifecycle of the MKanban daemon service including
startup, shutdown, configuration loading, and coordination
between different service components.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config.settings import Settings
from core.exceptions import MKanbanError
from infrastructure.tmux.session_manager import (
    get_mkanban_data_path,
    ensure_mkanban_directory,
)


@dataclass
class DaemonConfig:
    """Configuration specific to daemon operations"""

    enabled: bool = True
    polling_interval: int = 5  # seconds
    tmux_session_only: bool = True  # Only monitor active tmux session
    default_board: str = "git-branches"
    default_column: str = "to-do"
    in_progress_column: str = "in-progress"
    done_column: str = "done"
    branch_patterns: list[str] = None
    excluded_branches: list[str] = None
    data_path: Optional[Path] = None

    def __post_init__(self):
        if self.branch_patterns is None:
            # Include common patterns but also allow arbitrary branch names
            self.branch_patterns = [
                "feature/*",
                "bugfix/*",
                "hotfix/*",
                "fix/*",
                "feat/*",
                "test",
                "test/*",
                "*",
            ]
        if self.excluded_branches is None:
            self.excluded_branches = [
                "main",
                "master",
                "develop",
                "staging",
                "production",
            ]
        if self.data_path is None:
            self.data_path = ensure_mkanban_directory()


class ServiceManager:
    """Manages the MKanban daemon service lifecycle"""

    def __init__(self, settings: Settings, daemon_config: DaemonConfig):
        self.settings = settings
        self.daemon_config = daemon_config
        self.logger = self._setup_logging()
        self.running = False
        self.services: Dict[str, Any] = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the daemon"""
        logger = logging.getLogger("mkanban-daemon")
        logger.setLevel(logging.DEBUG)

        # Create logs directory
        log_dir = Path.home() / ".mkanban" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(log_dir / "daemon.log")
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    async def start(self) -> None:
        """Start the daemon service"""
        if self.running:
            raise MKanbanError("Daemon is already running")

        self.logger.info("Starting MKanban daemon...")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Initialize services
            await self._initialize_services()

            self.running = True
            self.logger.info("MKanban daemon started successfully")

            # Main service loop
            await self._run_service_loop()

        except Exception as e:
            self.logger.error(f"Failed to start daemon: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the daemon service"""
        if not self.running:
            return

        self.logger.info("Stopping MKanban daemon...")
        self.running = False

        # Cleanup services
        await self._cleanup_services()

        self.logger.info("MKanban daemon stopped")

    async def _initialize_services(self) -> None:
        """Initialize all daemon services"""
        from daemon.git_monitor import GitMonitor
        from daemon.task_synchronizer import TaskSynchronizer
        from daemon.ipc import IPCServer, setup_ipc_handlers

        # Initialize git monitor
        self.services["git_monitor"] = GitMonitor(
            polling_interval=self.daemon_config.polling_interval,
            tmux_session_only=self.daemon_config.tmux_session_only,
        )

        # Initialize task synchronizer
        self.services["task_synchronizer"] = TaskSynchronizer(
            self.settings, self.daemon_config
        )

        # Initialize IPC server
        ipc_server = IPCServer()
        setup_ipc_handlers(ipc_server, self)
        self.services["ipc_server"] = ipc_server

        # Start services
        for service in self.services.values():
            if hasattr(service, "start"):
                await service.start()

    async def _cleanup_services(self) -> None:
        """Cleanup all daemon services"""
        for service in self.services.values():
            if hasattr(service, "stop"):
                try:
                    await service.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping service: {e}")

        self.services.clear()

    async def _run_service_loop(self) -> None:
        """Main service loop"""
        while self.running:
            try:
                # Check for git events
                if "git_monitor" in self.services:
                    events = await self.services["git_monitor"].get_events()

                    # Process events
                    if events and "task_synchronizer" in self.services:
                        await self.services["task_synchronizer"].process_events(events)

                # Sleep for polling interval
                await asyncio.sleep(self.daemon_config.polling_interval)

            except Exception as e:
                self.logger.error(f"Error in service loop: {e}")
                # Continue running unless it's a critical error
                await asyncio.sleep(1)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


async def run_daemon(settings: Settings, daemon_config: DaemonConfig) -> None:
    """Run the daemon with the given configuration"""
    manager = ServiceManager(settings, daemon_config)
    try:
        await manager.start()
    except KeyboardInterrupt:
        pass
    finally:
        await manager.stop()
