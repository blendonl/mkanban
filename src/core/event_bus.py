"""Simple event bus for inter-service communication"""

from typing import Dict, List, Callable, Any
from src.utils.logger_factory import LoggerFactory


class EventBus:
    """Simple event bus for publishing and subscribing to events"""

    _instance = None
    _handlers: Dict[str, List[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
            cls._instance.logger = LoggerFactory().get_daemon_logger("event_bus")
        return cls._instance

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            self.logger.debug(f"Subscribed handler to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self.logger.debug(f"Unsubscribed handler from event: {event_type}")

    def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            event_data: Event data dictionary
        """
        if event_type not in self._handlers:
            self.logger.debug(f"No handlers for event: {event_type}")
            return

        self.logger.debug(f"Publishing event: {event_type} with {len(self._handlers[event_type])} handlers")

        for handler in self._handlers[event_type]:
            try:
                handler(event_data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}", exc_info=True)

    def clear(self) -> None:
        """Clear all event handlers"""
        self._handlers.clear()
        self.logger.debug("Cleared all event handlers")


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    return EventBus()
