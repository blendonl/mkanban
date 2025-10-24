import subprocess
from typing import Optional
from pathlib import Path
from src.domain.entities.action_executor import NotificationPriority
from src.utils.logger_factory import LoggerFactory


class SystemNotifier:
    """System notification provider using notify-send (Linux/Unix)"""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the SystemNotifier.

        Args:
            config: Configuration dictionary with optional keys:
                - command: Command to use (default: "notify-send")
                - icon_path: Path to notification icon
        """
        self.config = config or {}
        self.command = self.config.get("command", "notify-send")
        self.icon_path = self.config.get("icon_path")
        self.logger = LoggerFactory().get_daemon_logger("system_notifier")

        # Check if notify-send is available
        self.is_available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if notify-send command is available"""
        try:
            result = subprocess.run(
                ["which", self.command],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def send(
        self,
        message: str,
        title: str = "MKanban",
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> bool:
        """
        Send a system notification.

        Args:
            message: Notification message
            title: Notification title
            priority: Notification priority

        Returns:
            True if notification was sent successfully
        """
        if not self.is_available:
            self.logger.warning(f"{self.command} is not available on this system")
            return False

        try:
            # Build notify-send command
            cmd = [self.command]

            # Add urgency level based on priority
            urgency_map = {
                NotificationPriority.LOW: "low",
                NotificationPriority.NORMAL: "normal",
                NotificationPriority.HIGH: "normal",
                NotificationPriority.URGENT: "critical"
            }
            cmd.extend(["-u", urgency_map.get(priority, "normal")])

            # Add icon if configured
            if self.icon_path and Path(self.icon_path).exists():
                cmd.extend(["-i", str(self.icon_path)])

            # Add title and message
            cmd.append(title)
            cmd.append(message)

            # Execute notify-send
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.logger.debug(f"Sent system notification: {title}")
                return True
            else:
                self.logger.error(f"notify-send failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("notify-send timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}", exc_info=True)
            return False
