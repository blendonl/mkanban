import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable

from .messages import IPCMessage, IPCResponse


class IPCServer:
    """Inter-process communication server for daemon control"""

    def __init__(self, socket_path: Path, request_handler: Callable[[IPCMessage], IPCResponse]):
        self.socket_path = socket_path
        self.request_handler = request_handler
        self.logger = logging.getLogger("mkanban-daemon")
        self.server: Optional[asyncio.Server] = None
        self._running = False

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection"""
        client_address = writer.get_extra_info('peername', 'unknown')
        self.logger.debug(f"IPC client connected: {client_address}")

        try:
            # Read the message
            data = await reader.read(65536)  # 64KB max message size
            if not data:
                return

            try:
                message_dict = json.loads(data.decode('utf-8'))
                message = IPCMessage.from_dict(message_dict)
                self.logger.debug(f"Received IPC message: {message.message_type.value}")

                # Process the message
                response = self.request_handler(message)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.error(f"Invalid IPC message format: {e}")
                response = IPCResponse.invalid_request(f"Invalid message format: {e}")
            except Exception as e:
                self.logger.error(f"Error processing IPC message: {e}")
                response = IPCResponse.error(f"Internal error: {e}")

            # Send the response
            response_data = json.dumps(response.to_dict()).encode('utf-8')
            writer.write(response_data)
            await writer.drain()

        except Exception as e:
            self.logger.error(f"Error handling IPC client: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            self.logger.debug(f"IPC client disconnected: {client_address}")

    async def start(self) -> bool:
        """Start the IPC server"""
        if self._running:
            self.logger.warning("IPC server is already running")
            return False

        try:
            # Remove existing socket file if it exists
            if self.socket_path.exists():
                self.socket_path.unlink()

            # Ensure parent directory exists
            self.socket_path.parent.mkdir(parents=True, exist_ok=True)

            # Start the server
            self.server = await asyncio.start_unix_server(
                self.handle_client,
                path=str(self.socket_path)
            )

            self._running = True
            self.logger.info(f"IPC server started at {self.socket_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start IPC server: {e}")
            return False

    async def stop(self):
        """Stop the IPC server"""
        if not self._running:
            return

        self._running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

        # Clean up socket file
        try:
            if self.socket_path.exists():
                self.socket_path.unlink()
        except Exception as e:
            self.logger.error(f"Error cleaning up socket file: {e}")

        self.logger.info("IPC server stopped")

    def is_running(self) -> bool:
        """Check if the server is running"""
        return self._running


def setup_ipc_handlers(ipc_server: IPCServer, daemon_manager) -> None:
    """Setup IPC handlers for the daemon

    This function was previously used to configure handlers, but
    the new IPCServer design requires the handler to be passed
    during construction. This is kept for backward compatibility.
    """
    # For now, this is a no-op since the handler is passed in constructor
    pass