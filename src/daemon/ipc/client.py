import json
import asyncio
import logging
from pathlib import Path
from typing import Optional
import socket

from .messages import IPCMessage, IPCResponse


class IPCClient:
    """Inter-process communication client for daemon control"""

    def __init__(self, socket_path: Path, timeout: float = 10.0):
        self.socket_path = socket_path
        self.timeout = timeout
        self.logger = logging.getLogger("mkanban-client")

    async def send_message(self, message: IPCMessage) -> Optional[IPCResponse]:
        """Send a message to the daemon and wait for response"""
        if not self.socket_path.exists():
            self.logger.error(f"Daemon socket not found: {self.socket_path}")
            return None

        try:
            # Connect to the daemon
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(str(self.socket_path)),
                timeout=self.timeout
            )

            try:
                # Send message
                message_data = json.dumps(message.to_dict()).encode('utf-8')
                writer.write(message_data)
                await writer.drain()

                # Read response
                response_data = await asyncio.wait_for(
                    reader.read(65536),  # 64KB max response size
                    timeout=self.timeout
                )

                if not response_data:
                    self.logger.error("No response from daemon")
                    return None

                # Parse response
                response_dict = json.loads(response_data.decode('utf-8'))
                return IPCResponse.from_dict(response_dict)

            finally:
                writer.close()
                await writer.wait_closed()

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout communicating with daemon (timeout: {self.timeout}s)")
            return None
        except (ConnectionRefusedError, FileNotFoundError):
            self.logger.error("Could not connect to daemon - is it running?")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Invalid response from daemon: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error communicating with daemon: {e}")
            return None

    async def get_status(self) -> Optional[IPCResponse]:
        """Get daemon status"""
        message = IPCMessage.create_status_request()
        return await self.send_message(message)

    async def refresh_repository(self, repository_path: Optional[Path] = None) -> Optional[IPCResponse]:
        """Request repository refresh"""
        message = IPCMessage.create_refresh_request(repository_path)
        return await self.send_message(message)

    async def sync_repository(self, repository_path: Path) -> Optional[IPCResponse]:
        """Request repository sync"""
        message = IPCMessage.create_sync_repository_request(repository_path)
        return await self.send_message(message)

    async def shutdown_daemon(self) -> Optional[IPCResponse]:
        """Request daemon shutdown"""
        message = IPCMessage.create_shutdown_request()
        return await self.send_message(message)

    def is_daemon_running(self) -> bool:
        """Check if daemon is running (synchronous)"""
        return self.socket_path.exists()