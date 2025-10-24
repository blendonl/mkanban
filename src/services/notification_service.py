from typing import List, Optional, Any, Dict
from enum import Enum
from src.domain.entities.action_executor import NotificationPriority
from src.utils.logger_factory import LoggerFactory


class NotificationChannel(str, Enum):
    """Available notification channels"""
    SYSTEM = "system"
    MOBILE_PUSH = "mobile_push"
    EMAIL = "email"


class NotificationService:
    """Service for sending notifications across multiple channels and platforms"""

    def __init__(
        self,
        config: Optional[Any] = None,
        logger: Optional[Any] = None,
        system_notifier: Optional[Any] = None,
        mobile_push_provider: Optional[Any] = None,
        email_provider: Optional[Any] = None
    ):
        """
        Initialize the NotificationService.

        Args:
            config: Configuration manager instance
            logger: Logger instance (injected via dependency injection)
            system_notifier: Provider for system notifications (notify-send)
            mobile_push_provider: Provider for mobile push notifications
            email_provider: Provider for email notifications
        """
        self.system_notifier = system_notifier
        self.mobile_push_provider = mobile_push_provider
        self.email_provider = email_provider
        self.config = config.config.actions.notifications if config and hasattr(config, 'config') else {}
        self.logger = logger

    def send_notification(
        self,
        message: str,
        title: str = "MKanban",
        platforms: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> bool:
        """
        Send a notification across specified platforms and channels.

        Args:
            message: Notification message
            title: Notification title
            platforms: Target platforms (desktop, mobile, both)
            channels: Notification channels to use
            priority: Notification priority

        Returns:
            True if at least one notification was sent successfully
        """
        platforms = platforms or ["desktop"]
        channels = channels or ["system"]

        success_count = 0
        total_attempts = 0

        # Determine which platforms to target
        should_send_desktop = "desktop" in platforms or "both" in platforms
        should_send_mobile = "mobile" in platforms or "both" in platforms

        # Send notifications through each channel
        for channel in channels:
            if channel == "system" and should_send_desktop:
                total_attempts += 1
                if self._send_system_notification(message, title, priority):
                    success_count += 1

            elif channel == "mobile_push" and should_send_mobile:
                total_attempts += 1
                if self._send_mobile_push(message, title, priority):
                    success_count += 1

            elif channel == "email":
                total_attempts += 1
                if self._send_email_notification(message, title, priority):
                    success_count += 1

        if total_attempts == 0:
            self.logger.warning("No notification channels attempted")
            return False

        if success_count == 0:
            self.logger.error("All notification attempts failed")
            return False

        self.logger.info(f"Sent {success_count}/{total_attempts} notifications successfully")
        return True

    def _send_system_notification(
        self,
        message: str,
        title: str,
        priority: NotificationPriority
    ) -> bool:
        """Send a system notification (desktop)"""
        if not self.system_notifier:
            self.logger.warning("System notifier not available")
            return False

        try:
            return self.system_notifier.send(
                message=message,
                title=title,
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}", exc_info=True)
            return False

    def _send_mobile_push(
        self,
        message: str,
        title: str,
        priority: NotificationPriority
    ) -> bool:
        """Send a mobile push notification"""
        if not self.mobile_push_provider:
            self.logger.warning("Mobile push provider not available")
            return False

        try:
            return self.mobile_push_provider.send(
                message=message,
                title=title,
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to send mobile push: {e}", exc_info=True)
            return False

    def _send_email_notification(
        self,
        message: str,
        title: str,
        priority: NotificationPriority
    ) -> bool:
        """Send an email notification"""
        if not self.email_provider:
            self.logger.warning("Email provider not available")
            return False

        try:
            return self.email_provider.send(
                message=message,
                subject=title,
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def is_channel_available(self, channel: str) -> bool:
        """Check if a notification channel is available"""
        if channel == "system":
            return self.system_notifier is not None
        elif channel == "mobile_push":
            return self.mobile_push_provider is not None
        elif channel == "email":
            return self.email_provider is not None
        return False

    def get_available_channels(self) -> List[str]:
        """Get list of available notification channels"""
        channels = []
        if self.system_notifier:
            channels.append("system")
        if self.mobile_push_provider:
            channels.append("mobile_push")
        if self.email_provider:
            channels.append("email")
        return channels
