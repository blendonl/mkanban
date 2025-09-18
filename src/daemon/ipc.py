"""Inter-Process Communication for MKanban Daemon

Provides communication between the daemon and CLI using Unix domain sockets.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

from infrastructure.tmux.session_manager import get_mkanban_data_path


@dataclass
class IPCMessage:
    """IPC message structure"""

    command: str
    data: Dict[str, Any] = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "IPCMessage":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class IPCResponse:
    """IPC response structure"""

    success: bool
    data: Dict[str, Any] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "IPCResponse":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


class IPCServer:
    """IPC server for the daemon"""

    def __init__(self, socket_path: Optional[Path] = None):
        self.socket_path = socket_path or (get_mkanban_data_path() / "daemon.sock")
        self.server: Optional[asyncio.Server] = None
        self.logger = logging.getLogger("mkanban-daemon")
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, command: str, handler: Callable) -> None:
        """Register a command handler"""
        self.handlers[command] = handler

    async def start(self) -> None:
        """Start the IPC server"""
        # Remove existing socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Ensure directory exists
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Start server
        self.server = await asyncio.start_unix_server(
            self._handle_client, path=str(self.socket_path)
        )

        self.logger.info(f"IPC server started on {self.socket_path}")

    async def stop(self) -> None:
        """Stop the IPC server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Clean up socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        self.logger.info("IPC server stopped")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a client connection"""
        try:
            # Read message
            data = await reader.read(4096)
            if not data:
                return

            message_str = data.decode("utf-8")
            message = IPCMessage.from_json(message_str)

            # Process message
            response = await self._process_message(message)

            # Send response
            response_str = response.to_json()
            writer.write(response_str.encode("utf-8"))
            await writer.drain()

        except Exception as e:
            self.logger.error(f"Error handling IPC client: {e}")
            error_response = IPCResponse(success=False, error=str(e))
            writer.write(error_response.to_json().encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _process_message(self, message: IPCMessage) -> IPCResponse:
        """Process an IPC message"""
        command = message.command

        if command not in self.handlers:
            return IPCResponse(
                success=False,
                error=f"Unknown command: {command}",
                request_id=message.request_id,
            )

        try:
            handler = self.handlers[command]
            result = await handler(message.data)

            return IPCResponse(success=True, data=result, request_id=message.request_id)
        except Exception as e:
            return IPCResponse(
                success=False, error=str(e), request_id=message.request_id
            )


class IPCClient:
    """IPC client for CLI commands"""

    def __init__(self, socket_path: Optional[Path] = None):
        self.socket_path = socket_path or (get_mkanban_data_path() / "daemon.sock")

    async def send_command(
        self, command: str, data: Dict[str, Any] = None
    ) -> IPCResponse:
        """Send a command to the daemon"""
        if not self.socket_path.exists():
            raise ConnectionError("Daemon is not running")

        message = IPCMessage(command=command, data=data or {})

        try:
            reader, writer = await asyncio.open_unix_connection(str(self.socket_path))

            # Send message
            message_str = message.to_json()
            writer.write(message_str.encode("utf-8"))
            await writer.drain()

            # Read response
            response_data = await reader.read(4096)
            response_str = response_data.decode("utf-8")
            response = IPCResponse.from_json(response_str)

            writer.close()
            await writer.wait_closed()

            return response

        except Exception as e:
            raise ConnectionError(f"Failed to communicate with daemon: {e}")

    def send_command_sync(
        self, command: str, data: Dict[str, Any] = None
    ) -> IPCResponse:
        """Send a command synchronously"""
        return asyncio.run(self.send_command(command, data))


def setup_ipc_handlers(server: IPCServer, service_manager) -> None:
    """Setup standard IPC command handlers"""

    async def handle_status(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status command"""
        return {
            "running": service_manager.running,
            "services": list(service_manager.services.keys()),
            "config": {
                "polling_interval": service_manager.daemon_config.polling_interval,
                "tmux_session_only": service_manager.daemon_config.tmux_session_only,
                "default_board": service_manager.daemon_config.default_board,
            },
        }

    async def handle_sync(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle manual sync command"""
        # Trigger immediate sync
        if "git_monitor" in service_manager.services:
            git_monitor = service_manager.services["git_monitor"]
            events = await git_monitor.get_events()

            if events and "task_synchronizer" in service_manager.services:
                task_synchronizer = service_manager.services["task_synchronizer"]
                await task_synchronizer.process_events(events)

                return {"synced_events": len(events)}

        return {"synced_events": 0}

    async def handle_current_branch(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle current branch info command"""
        from infrastructure.tmux.session_manager import TmuxSessionManager

        tmux_manager = TmuxSessionManager()

        if tmux_manager.is_in_tmux_session():
            repo = tmux_manager.get_active_session_repository()
            if repo:
                from infrastructure.git.repository import GitOperations

                git_ops = GitOperations(repo)
                current_branch = git_ops.get_current_branch()

                return {"repository": str(repo), "current_branch": current_branch}

        return {"repository": None, "current_branch": None}

    # Register handlers
    server.register_handler("status", handle_status)
    server.register_handler("sync", handle_sync)
    server.register_handler("current_branch", handle_current_branch)
