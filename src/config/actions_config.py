from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    system: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "command": "notify-send",
        "icon_path": None
    })
    mobile_push: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "provider": "ntfy",
        "ntfy_server": "https://ntfy.sh",
        "ntfy_topic": None,
        "ntfy_token": None
    })
    email: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_address": None,
        "username": None,
        "password": None
    })


@dataclass
class CalendarIntegrationConfig:
    """Configuration for calendar integration"""
    google_calendar: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "calendar_id": "primary",
        "sync_interval": 300,
        "credentials_path": "~/.mkanban/google_credentials.json",
        "token_path": "~/.mkanban/google_token.json"
    })


@dataclass
class ActionsConfiguration:
    """Configuration for actions/reminders system"""
    enabled: bool = True
    polling_interval: int = 30  # seconds
    default_snooze_options: List[str] = field(default_factory=lambda: [
        "10m", "30m", "1h", "3h", "tomorrow", "next_week"
    ])
    max_concurrent_executions: int = 5
    execution_timeout: int = 300  # seconds
    orphan_check_interval: int = 3600  # seconds (1 hour)
    orphan_action: str = "auto_disable"  # auto_disable | auto_delete | warn_only

    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    calendar_integration: CalendarIntegrationConfig = field(default_factory=CalendarIntegrationConfig)
