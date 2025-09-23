from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class IPCMessageType(Enum):
    STATUS = "status"
    REFRESH = "refresh"
    SYNC_REPOSITORY = "sync_repository"
    SHUTDOWN = "shutdown"
    GET_CONFIG = "get_config"
    UPDATE_CONFIG = "update_config"


class IPCResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    INVALID_REQUEST = "invalid_request"


@dataclass
class IPCMessage:
    """Inter-process communication message"""

    message_type: IPCMessageType
    data: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    @classmethod
    def create_status_request(cls, request_id: Optional[str] = None) -> "IPCMessage":
        """Create a status request message"""
        return cls(
            message_type=IPCMessageType.STATUS,
            request_id=request_id
        )

    @classmethod
    def create_refresh_request(cls, repository_path: Optional[Path] = None, request_id: Optional[str] = None) -> "IPCMessage":
        """Create a refresh request message"""
        data = {}
        if repository_path:
            data["repository_path"] = str(repository_path)

        return cls(
            message_type=IPCMessageType.REFRESH,
            data=data,
            request_id=request_id
        )

    @classmethod
    def create_sync_repository_request(cls, repository_path: Path, request_id: Optional[str] = None) -> "IPCMessage":
        """Create a sync repository request message"""
        return cls(
            message_type=IPCMessageType.SYNC_REPOSITORY,
            data={"repository_path": str(repository_path)},
            request_id=request_id
        )

    @classmethod
    def create_shutdown_request(cls, request_id: Optional[str] = None) -> "IPCMessage":
        """Create a shutdown request message"""
        return cls(
            message_type=IPCMessageType.SHUTDOWN,
            request_id=request_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "message_type": self.message_type.value,
            "data": self.data,
            "request_id": self.request_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPCMessage":
        """Create from dictionary"""
        return cls(
            message_type=IPCMessageType(data["message_type"]),
            data=data.get("data", {}),
            request_id=data.get("request_id"),
        )


@dataclass
class IPCResponse:
    """Inter-process communication response"""

    status: IPCResponseStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    request_id: Optional[str] = None

    @classmethod
    def success(cls, data: Dict[str, Any] = None, request_id: Optional[str] = None) -> "IPCResponse":
        """Create a success response"""
        return cls(
            status=IPCResponseStatus.SUCCESS,
            data=data or {},
            request_id=request_id
        )

    @classmethod
    def error(cls, error_message: str, request_id: Optional[str] = None) -> "IPCResponse":
        """Create an error response"""
        return cls(
            status=IPCResponseStatus.ERROR,
            error_message=error_message,
            request_id=request_id
        )

    @classmethod
    def not_found(cls, error_message: str = "Resource not found", request_id: Optional[str] = None) -> "IPCResponse":
        """Create a not found response"""
        return cls(
            status=IPCResponseStatus.NOT_FOUND,
            error_message=error_message,
            request_id=request_id
        )

    @classmethod
    def invalid_request(cls, error_message: str = "Invalid request", request_id: Optional[str] = None) -> "IPCResponse":
        """Create an invalid request response"""
        return cls(
            status=IPCResponseStatus.INVALID_REQUEST,
            error_message=error_message,
            request_id=request_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "status": self.status.value,
            "data": self.data,
            "request_id": self.request_id,
        }
        if self.error_message:
            result["error_message"] = self.error_message
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPCResponse":
        """Create from dictionary"""
        return cls(
            status=IPCResponseStatus(data["status"]),
            data=data.get("data", {}),
            error_message=data.get("error_message"),
            request_id=data.get("request_id"),
        )