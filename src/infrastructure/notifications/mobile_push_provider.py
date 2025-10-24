import requests
from typing import Optional
from src.domain.entities.action_executor import NotificationPriority
from src.utils.logger_factory import LoggerFactory


class MobilePushProvider:
    """Mobile push notification provider using ntfy.sh"""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the MobilePushProvider.

        Args:
            config: Configuration dictionary with keys:
                - ntfy_server: ntfy server URL (default: https://ntfy.sh)
                - ntfy_topic: Topic to publish to (required)
                - ntfy_token: Authentication token (optional)
        """
        self.config = config or {}
        self.server = self.config.get("ntfy_server", "https://ntfy.sh")
        self.topic = self.config.get("ntfy_topic")
        self.token = self.config.get("ntfy_token")
        self.logger = LoggerFactory().get_daemon_logger("mobile_push_provider")

        if not self.topic:
            self.logger.warning("ntfy_topic not configured, mobile push disabled")

    def send(
        self,
        message: str,
        title: str = "MKanban",
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> bool:
        """
        Send a mobile push notification via ntfy.sh.

        Args:
            message: Notification message
            title: Notification title
            priority: Notification priority

        Returns:
            True if notification was sent successfully
        """
        if not self.topic:
            self.logger.warning("Cannot send mobile push: ntfy_topic not configured")
            return False

        try:
            # Map priority to ntfy priority
            ntfy_priority_map = {
                NotificationPriority.LOW: 2,
                NotificationPriority.NORMAL: 3,
                NotificationPriority.HIGH: 4,
                NotificationPriority.URGENT: 5
            }
            ntfy_priority = ntfy_priority_map.get(priority, 3)

            # Build request
            url = f"{self.server}/{self.topic}"
            headers = {
                "Title": title,
                "Priority": str(ntfy_priority),
                "Tags": "kanban,reminder"
            }

            # Add auth token if configured
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            # Send notification
            response = requests.post(
                url,
                data=message.encode('utf-8'),
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.debug(f"Sent mobile push notification: {title}")
                return True
            else:
                self.logger.error(f"ntfy.sh returned {response.status_code}: {response.text}")
                return False

        except requests.Timeout:
            self.logger.error("ntfy.sh request timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send mobile push: {e}", exc_info=True)
            return False

    def is_configured(self) -> bool:
        """Check if mobile push is properly configured"""
        return self.topic is not None
