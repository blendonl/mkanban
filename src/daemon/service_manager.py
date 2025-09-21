"""Daemon Service Manager

Handles the lifecycle of the MKanban daemon service including
startup, shutdown, configuration loading, and coordination
between different service components.
"""

import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Dict, Any

from core.exceptions import MKanbanError
from daemon.core.configuration_service import ConfigurationService
from daemon.core.session_context_manager import SessionContextManager


class ServiceManager:
    """Manages the MKanban daemon service lifecycle"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.session_manager = SessionContextManager(
            config_service.config.tmux_session_only
        )
        self.logger = self._setup_logging()
        self.running = False
        self.services: Dict[str, Any] = {}
        self.pid_file = self._get_pid_file_path()

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

    def _get_pid_file_path(self) -> Path:
        """Get the path to the PID file"""
        return self.config_service.config.data_path / "daemon.pid"

    def _write_pid_file(self) -> None:
        """Write the current process PID to the PID file"""
        try:
            self.config_service.config.data_path.mkdir(parents=True, exist_ok=True)
            self.pid_file.write_text(str(os.getpid()))
            self.logger.debug(f"PID file written: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")

    def _remove_pid_file(self) -> None:
        """Remove the PID file"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.debug(f"PID file removed: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Failed to remove PID file: {e}")

    async def start(self) -> None:
        """Start the daemon service"""
        if self.running:
            raise MKanbanError("Daemon is already running")

        # Initialize session context first
        await self.session_manager.initialize_context()
        session_name = self.session_manager.current_context.session_name

        self.logger.info(f"Starting MKanban daemon for session '{session_name}'...")

        # Write PID file
        self._write_pid_file()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Initialize services
            await self._initialize_services()

            self.running = True
            self.logger.info(
                f"MKanban daemon started successfully for session '{session_name}'"
            )

            # Main service loop
            await self._run_service_loop()

        except Exception as e:
            self.logger.error(f"Failed to start daemon: {e}")
            self._remove_pid_file()
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the daemon service"""
        if not self.running:
            return

        session_name = self.config_service.get_board_name()
        self.logger.info(f"Stopping MKanban daemon for session '{session_name}'...")
        self.running = False

        # Cleanup services
        await self._cleanup_services()

        # Remove PID file
        self._remove_pid_file()

        self.logger.info(f"MKanban daemon stopped for session '{session_name}'")

    async def _initialize_services(self) -> None:
        """Initialize all daemon services"""
        from daemon.git_monitor import GitMonitor
        from daemon.sync.sync_coordinator import SyncCoordinator
        from daemon.ipc.ipc_server import IPCServer, setup_ipc_handlers

        # Initialize git monitor with session context manager
        self.services["git_monitor"] = GitMonitor(
            session_context_manager=self.session_manager,
            polling_interval=self.config_service.config.polling_interval,
        )

        # Initialize sync coordinator
        self.services["sync_coordinator"] = SyncCoordinator(self.config_service)

        # Initialize IPC server with session-specific socket path
        ipc_socket_path = self.config_service.get_socket_path()
        ipc_server = IPCServer(socket_path=ipc_socket_path)
        setup_ipc_handlers(ipc_server, self)
        self.services["ipc_server"] = ipc_server

        # Register session change callbacks
        self.session_manager.add_change_callback(self._handle_session_change)
        if "git_monitor" in self.services:
            self.session_manager.add_change_callback(self.services["git_monitor"].handle_session_change)
        if "sync_coordinator" in self.services:
            self.session_manager.add_change_callback(self.services["sync_coordinator"].handle_session_change)

        # Register session switch callbacks for task management
        if "sync_coordinator" in self.services:
            self.session_manager.add_session_switch_callback(
                self.services["sync_coordinator"].handle_session_switch
            )

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
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                if loop_count % 12 == 1:  # Log every minute (5s * 12 = 60s)
                    session_name = self.config_service.get_board_name()
                    self.logger.debug(
                        f"[{session_name}] Service loop iteration {loop_count}"
                    )

                # Check for session changes
                await self.session_manager.check_for_changes()

                # Check for git events
                if "git_monitor" in self.services:
                    events = await self.services["git_monitor"].get_events()

                    if events:
                        session_name = self.config_service.get_board_name()
                        event_types = [e.event_type.value for e in events]
                        self.logger.debug(
                            f"[{session_name}] Got {len(events)} git events: {event_types}"
                        )

                    # Process events
                    if events and "sync_coordinator" in self.services:
                        session_name = self.config_service.get_board_name()
                        self.logger.debug(
                            f"[{session_name}] Processing {len(events)} events "
                            f"with sync coordinator"
                        )
                        await self.services["sync_coordinator"].process_events(events)
                        self.logger.debug(
                            f"[{session_name}] Finished processing {len(events)} events"
                        )

                # Sleep for polling interval
                await asyncio.sleep(self.config_service.config.polling_interval)

            except Exception as e:
                session_name = self.config_service.get_board_name()
                self.logger.error(f"[{session_name}] Error in service loop: {e}")
                # Continue running unless it's a critical error
                await asyncio.sleep(1)

    async def _handle_session_change(self, old_context, new_context) -> None:
        """Handle session context change"""
        self.logger.info(
            f"ServiceManager handling session change: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals"""
        session_name = self.config_service.get_board_name()
        self.logger.info(
            f"[{session_name}] Received signal {signum}, shutting down..."
        )
        self.running = False


async def run_daemon(config_service: ConfigurationService) -> None:
    """Run the daemon with the given configuration"""
    manager = ServiceManager(config_service)
    try:
        await manager.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.getLogger("mkanban-daemon").error(f"Daemon error: {e}")
    finally:
        await manager.stop()
