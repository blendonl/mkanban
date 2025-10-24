"""Action Daemon

Manages the lifecycle of actions/reminders including:
- Polling for time-based triggers
- Evaluating and executing actions
- Handling event-based triggers via event bus
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from src.services.action_service import ActionService
from src.services.action_engine import ActionEngine
from src.services.notification_service import NotificationService
from src.infrastructure.repositories.yaml_action_repository import YamlActionRepository
from src.infrastructure.notifications.system_notifier import SystemNotifier
from src.infrastructure.notifications.mobile_push_provider import MobilePushProvider
from src.domain.entities.trigger import TriggerType
from src.utils.logger_factory import LoggerFactory


class ActionDaemon:
    """Daemon service for managing actions and reminders"""

    def __init__(
        self,
        actions_dir: Path,
        config: Dict[str, Any],
        board_service: Optional[Any] = None,
        item_service: Optional[Any] = None
    ):
        """
        Initialize the ActionDaemon.

        Args:
            actions_dir: Directory where action files are stored
            config: Configuration dictionary for actions
            board_service: Optional board service for action execution
            item_service: Optional item service for action execution
        """
        self.actions_dir = Path(actions_dir)
        self.config = config
        self.board_service = board_service
        self.item_service = item_service
        self.logger = LoggerFactory().get_daemon_logger("action_daemon")

        # Initialize repository
        self.action_repository = YamlActionRepository(self.actions_dir)

        # Initialize services
        self.action_service = ActionService(
            action_repository=self.action_repository,
            board_repository=None  # Will be set later if needed
        )

        # Initialize notification service
        self.notification_service = self._setup_notification_service()

        # Initialize action engine
        self.action_engine = ActionEngine(
            action_service=self.action_service,
            notification_service=self.notification_service,
            board_service=self.board_service,
            item_service=self.item_service
        )

        # Daemon state
        self.running = False
        self.polling_task: Optional[asyncio.Task] = None
        self.orphan_check_task: Optional[asyncio.Task] = None

        # Configuration
        self.polling_interval = config.get("polling_interval", 30)
        self.orphan_check_interval = config.get("orphan_check_interval", 3600)

    def _setup_notification_service(self) -> NotificationService:
        """Setup notification service with configured providers"""
        notification_config = self.config.get("notifications", {})

        # System notifier
        system_notifier = None
        system_config = notification_config.get("system", {})
        if system_config.get("enabled", True):
            system_notifier = SystemNotifier(system_config)

        # Mobile push provider
        mobile_push_provider = None
        mobile_config = notification_config.get("mobile_push", {})
        if mobile_config.get("enabled", False):
            mobile_push_provider = MobilePushProvider(mobile_config)

        return NotificationService(
            system_notifier=system_notifier,
            mobile_push_provider=mobile_push_provider,
            email_provider=None,  # TODO: Implement email provider
            config=notification_config
        )

    async def start(self) -> None:
        """Start the action daemon"""
        if self.running:
            self.logger.warning("ActionDaemon is already running")
            return

        self.logger.info("Starting ActionDaemon...")
        self.running = True

        # Start polling task
        self.polling_task = asyncio.create_task(self._polling_loop())

        # Start orphan check task
        self.orphan_check_task = asyncio.create_task(self._orphan_check_loop())

        self.logger.info("ActionDaemon started successfully")

    async def stop(self) -> None:
        """Stop the action daemon"""
        if not self.running:
            return

        self.logger.info("Stopping ActionDaemon...")
        self.running = False

        # Cancel tasks
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

        if self.orphan_check_task:
            self.orphan_check_task.cancel()
            try:
                await self.orphan_check_task
            except asyncio.CancelledError:
                pass

        self.logger.info("ActionDaemon stopped")

    async def _polling_loop(self) -> None:
        """Main polling loop for time-based triggers"""
        self.logger.info(f"Starting action polling loop (interval: {self.polling_interval}s)")

        while self.running:
            try:
                # Evaluate time-based triggers
                actions_to_execute = self.action_engine.evaluate_time_triggers()

                # Execute actions
                for action in actions_to_execute:
                    try:
                        self.logger.info(f"Executing time-triggered action: {action.id}")
                        success = self.action_engine.execute_action(action)
                        if success:
                            self.logger.info(f"Action {action.id} executed successfully")
                        else:
                            self.logger.warning(f"Action {action.id} execution failed")
                    except Exception as e:
                        self.logger.error(f"Error executing action {action.id}: {e}", exc_info=True)

                # Wait for next polling interval
                await asyncio.sleep(self.polling_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(self.polling_interval)

    async def _orphan_check_loop(self) -> None:
        """Periodic check for orphaned actions"""
        self.logger.info(f"Starting orphan check loop (interval: {self.orphan_check_interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self.orphan_check_interval)

                orphan_action = self.config.get("orphan_action", "auto_disable")
                auto_disable = orphan_action == "auto_disable"

                count = self.action_service.cleanup_orphaned_actions(auto_disable=auto_disable)
                if count > 0:
                    self.logger.info(f"Cleaned up {count} orphaned actions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in orphan check loop: {e}", exc_info=True)

    def handle_event(self, trigger_type: TriggerType, event_data: Dict[str, Any]) -> None:
        """
        Handle an event-based trigger.

        Args:
            trigger_type: Type of trigger event
            event_data: Event data dictionary
        """
        try:
            self.logger.debug(f"Handling event: {trigger_type} with data: {event_data}")

            # Evaluate event-based triggers
            actions_to_execute = self.action_engine.evaluate_event_trigger(
                trigger_type, event_data
            )

            # Execute actions
            for action in actions_to_execute:
                try:
                    self.logger.info(f"Executing event-triggered action: {action.id}")
                    success = self.action_engine.execute_action(action, context=event_data)
                    if success:
                        self.logger.info(f"Action {action.id} executed successfully")
                    else:
                        self.logger.warning(f"Action {action.id} execution failed")
                except Exception as e:
                    self.logger.error(f"Error executing action {action.id}: {e}", exc_info=True)

        except Exception as e:
            self.logger.error(f"Error handling event: {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status information"""
        return {
            "running": self.running,
            "polling_interval": self.polling_interval,
            "orphan_check_interval": self.orphan_check_interval,
            "total_actions": len(self.action_service.get_all_actions()),
            "enabled_actions": len(self.action_service.get_enabled_actions()),
            "available_channels": self.notification_service.get_available_channels()
        }
