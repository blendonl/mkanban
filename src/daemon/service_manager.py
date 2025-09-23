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

from src.core.exceptions import MKanbanError
from src.core.constants import DAEMON_SHUTDOWN_SLEEP
from src.daemon.core.configuration_service import ConfigurationService
from src.daemon.core.session_context_manager import SessionContextManager
from src.core.dependency_container import (
    get_container,
    get_git_monitor,
    get_jira_daemon,
    get_session_context_manager,
)


class ServiceManager:
    """Manages the MKanban daemon service lifecycle"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.container = get_container()
        # Register the provided config service in the container
        self.container.register_instance(ConfigurationService, config_service)

        # Get services from DI container
        self.session_manager = get_session_context_manager()
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
        from src.daemon.sync.sync_coordinator import SyncCoordinator
        from src.daemon.ipc.ipc_server import IPCServer, setup_ipc_handlers

        # Initialize git monitor using DI
        git_monitor = get_git_monitor()

        # Add current session repository to monitoring if available
        if (self.session_manager.current_context and
                self.session_manager.current_context.repository_path):
            git_monitor.add_repository(
                self.session_manager.current_context.repository_path
            )

        self.services["git_monitor"] = git_monitor

        # Initialize sync coordinator (not yet in DI - still manual)
        self.services["sync_coordinator"] = SyncCoordinator(self.config_service)

        # Initialize Jira daemon if enabled
        if self.config_service.is_jira_enabled():
            self.services["jira_daemon"] = get_jira_daemon()
            self.logger.info("Jira daemon initialized")

        # Initialize IPC server with session-specific socket path
        ipc_socket_path = self.config_service.get_socket_path()
        ipc_server = IPCServer(socket_path=ipc_socket_path, request_handler=self._handle_ipc_request)
        setup_ipc_handlers(ipc_server, self)
        self.services["ipc_server"] = ipc_server

        # Register session change callbacks
        self.session_manager.add_change_callback(self._handle_session_change)
        if "git_monitor" in self.services:
            self.session_manager.add_change_callback(
                self.services["git_monitor"].handle_session_change
            )
        if "sync_coordinator" in self.services:
            self.session_manager.add_change_callback(
                self.services["sync_coordinator"].handle_session_change
            )

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
                await asyncio.sleep(DAEMON_SHUTDOWN_SLEEP)

    async def _handle_session_change(self, old_context, new_context) -> None:
        """Handle session context change"""
        self.logger.info(
            f"ServiceManager handling session change: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )

    def _handle_ipc_request(self, message) -> "IPCResponse":
        """Handle IPC request messages"""
        from src.daemon.ipc.messages import IPCResponse, IPCResponseStatus

        try:
            message_type = message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type)

            if message_type == "status":
                # Return daemon status
                return IPCResponse(
                    status=IPCResponseStatus.SUCCESS,
                    data={
                        "running": self.running,
                        "session": self.session_manager.current_context.session_name if self.session_manager.current_context else None,
                        "services": list(self.services.keys())
                    }
                )
            elif message_type == "stop":
                # Stop the daemon
                self.running = False
                return IPCResponse(
                    status=IPCResponseStatus.SUCCESS,
                    data={"message": "Stopping daemon"}
                )
            else:
                return IPCResponse(
                    status=IPCResponseStatus.ERROR,
                    error=f"Unknown message type: {message_type}"
                )
        except Exception as e:
            return IPCResponse(
                status=IPCResponseStatus.ERROR,
                error=f"Error processing request: {e}"
            )

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals"""
        session_name = self.config_service.get_board_name()
        self.logger.info(f"[{session_name}] Received signal {signum}, shutting down...")
        self.running = False

    def get_jira_daemon(self):
        """Get the Jira daemon service"""
        return self.services.get("jira_daemon")

    async def force_jira_sync(self) -> int:
        """Force Jira synchronization"""
        jira_daemon = self.get_jira_daemon()
        if jira_daemon:
            return await jira_daemon.force_sync()
        return 0

    def get_jira_status(self) -> dict:
        """Get Jira daemon status"""
        jira_daemon = self.get_jira_daemon()
        if jira_daemon:
            return jira_daemon.get_status()
        return {"running": False, "error": "Jira daemon not initialized"}


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
