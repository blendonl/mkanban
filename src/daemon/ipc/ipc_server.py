"""Inter-Process Communication Server

Provides a Unix socket server for communicating with the daemon from
the TUI application. Handles status requests, configuration updates,
and control commands.
"""

# Re-export all IPC classes for backward compatibility
from .messages import IPCMessage, IPCResponse, IPCMessageType, IPCResponseStatus
from .server import IPCServer, setup_ipc_handlers
from .client import IPCClient

__all__ = [
    "IPCMessage",
    "IPCResponse",
    "IPCMessageType",
    "IPCResponseStatus",
    "IPCServer",
    "IPCClient",
    "setup_ipc_handlers"
]