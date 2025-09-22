"""Jira Event Processor

Processes Jira-related events and determines what actions should be taken
on the MKanban board (create items, update status, etc.).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from daemon.core.configuration_service import ConfigurationService
from daemon.jira.jira_client import JiraTicket


@dataclass
class JiraEvent:
    """Represents a Jira event (ticket created, updated, etc.)"""
    event_type: str  # "created", "updated", "status_changed", "deleted"
    ticket: JiraTicket
    timestamp: datetime
    changes: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.changes is None:
            self.changes = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessedJiraEvent:
    """Result of processing a Jira event"""
    original_event: JiraEvent
    actions: List[str]  # Actions to take: "create_item", "update_item", "move_item", etc.
    metadata: Dict[str, Any]


class JiraEventProcessor:
    """Processes Jira events and determines required actions"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")

    async def process_events(self, events: List[JiraEvent]) -> List[ProcessedJiraEvent]:
        """Process a list of Jira events and determine required actions"""
        processed_events = []

        for event in events:
            try:
                processed = await self._process_single_event(event)
                if processed:
                    processed_events.append(processed)
            except Exception as e:
                self.logger.error(f"Failed to process Jira event {event.event_type} for {event.ticket.key}: {e}")

        return processed_events

    async def _process_single_event(self, event: JiraEvent) -> Optional[ProcessedJiraEvent]:
        """Process a single Jira event"""
        jira_config = self.config_service.get_jira_config()

        # Check if we should track this ticket
        if not self.config_service.should_track_jira_ticket(event.ticket.key):
            self.logger.debug(f"Skipping ticket {event.ticket.key} - not in tracked projects")
            return None

        actions = []
        metadata = {
            "ticket_key": event.ticket.key,
            "ticket_data": event.ticket.to_dict(),
            "event_timestamp": event.timestamp,
        }

        if event.event_type == "created":
            actions = await self._handle_ticket_created(event, metadata)
        elif event.event_type == "updated":
            actions = await self._handle_ticket_updated(event, metadata)
        elif event.event_type == "status_changed":
            actions = await self._handle_status_changed(event, metadata)
        elif event.event_type == "deleted":
            actions = await self._handle_ticket_deleted(event, metadata)
        else:
            self.logger.warning(f"Unknown Jira event type: {event.event_type}")

        if actions:
            return ProcessedJiraEvent(
                original_event=event,
                actions=actions,
                metadata=metadata
            )

        return None

    async def _handle_ticket_created(self, event: JiraEvent, metadata: Dict[str, Any]) -> List[str]:
        """Handle ticket creation event"""
        self.logger.debug(f"Processing ticket creation: {event.ticket.key}")

        # Determine which column to place the new item
        target_column = self._map_jira_status_to_column(event.ticket.status)
        metadata["target_column"] = target_column

        return ["create_item"]

    async def _handle_ticket_updated(self, event: JiraEvent, metadata: Dict[str, Any]) -> List[str]:
        """Handle ticket update event"""
        self.logger.debug(f"Processing ticket update: {event.ticket.key}")

        actions = []

        # Check if status changed
        if event.changes and "status" in event.changes:
            old_status = event.changes["status"].get("from")
            new_status = event.changes["status"].get("to")

            if old_status != new_status:
                target_column = self._map_jira_status_to_column(new_status)
                metadata["target_column"] = target_column
                metadata["old_status"] = old_status
                metadata["new_status"] = new_status
                actions.append("move_item")

        # Always update metadata for any update
        actions.append("update_item_metadata")

        return actions

    async def _handle_status_changed(self, event: JiraEvent, metadata: Dict[str, Any]) -> List[str]:
        """Handle ticket status change event"""
        self.logger.debug(f"Processing status change: {event.ticket.key} -> {event.ticket.status}")

        target_column = self._map_jira_status_to_column(event.ticket.status)
        metadata["target_column"] = target_column

        return ["move_item", "update_item_metadata"]

    async def _handle_ticket_deleted(self, event: JiraEvent, metadata: Dict[str, Any]) -> List[str]:
        """Handle ticket deletion event"""
        self.logger.debug(f"Processing ticket deletion: {event.ticket.key}")

        # Option 1: Delete the item
        # return ["delete_item"]

        # Option 2: Move to done column and mark as archived (preferred)
        jira_config = self.config_service.get_jira_config()
        done_column = jira_config.status_mapping.get("Done", "done")
        metadata["target_column"] = done_column
        metadata["archived"] = True

        return ["move_item", "update_item_metadata"]

    def _map_jira_status_to_column(self, jira_status: str) -> str:
        """Map Jira status to MKanban column"""
        jira_config = self.config_service.get_jira_config()

        # Use configured status mapping
        for jira_stat, column_id in jira_config.status_mapping.items():
            if jira_stat.lower() == jira_status.lower():
                return column_id

        # Default mapping if not found in config
        status_lower = jira_status.lower()
        if status_lower in ["backlog"]:
            return "backlog"
        elif status_lower in ["to do", "open", "new"]:
            return "to-do"
        elif status_lower in ["in progress", "in-progress", "doing", "active"]:
            return "in-progress"
        elif status_lower in ["done", "closed", "resolved", "complete"]:
            return "done"
        elif status_lower in ["review", "in review", "code review"]:
            return "review"
        else:
            # Default to backlog for unknown statuses
            return "backlog"

    def create_ticket_event(self, ticket: JiraTicket, event_type: str, changes: Dict[str, Any] = None) -> JiraEvent:
        """Create a JiraEvent from a ticket and event type"""
        return JiraEvent(
            event_type=event_type,
            ticket=ticket,
            timestamp=datetime.now(timezone.utc),
            changes=changes or {},
            metadata={}
        )

    def detect_status_change(self, old_ticket: JiraTicket, new_ticket: JiraTicket) -> Optional[JiraEvent]:
        """Detect if ticket status changed and create appropriate event"""
        if old_ticket.status != new_ticket.status:
            changes = {
                "status": {
                    "from": old_ticket.status,
                    "to": new_ticket.status
                }
            }
            return self.create_ticket_event(new_ticket, "status_changed", changes)
        return None

    def detect_changes(self, old_ticket: JiraTicket, new_ticket: JiraTicket) -> Optional[JiraEvent]:
        """Detect changes between two ticket versions"""
        changes = {}

        # Check various fields for changes
        if old_ticket.summary != new_ticket.summary:
            changes["summary"] = {"from": old_ticket.summary, "to": new_ticket.summary}

        if old_ticket.description != new_ticket.description:
            changes["description"] = {"from": old_ticket.description, "to": new_ticket.description}

        if old_ticket.status != new_ticket.status:
            changes["status"] = {"from": old_ticket.status, "to": new_ticket.status}

        if old_ticket.assignee != new_ticket.assignee:
            changes["assignee"] = {"from": old_ticket.assignee, "to": new_ticket.assignee}

        if old_ticket.priority != new_ticket.priority:
            changes["priority"] = {"from": old_ticket.priority, "to": new_ticket.priority}

        if old_ticket.labels != new_ticket.labels:
            changes["labels"] = {"from": old_ticket.labels, "to": new_ticket.labels}

        if changes:
            # Determine event type based on changes
            if "status" in changes:
                event_type = "status_changed"
            else:
                event_type = "updated"

            return self.create_ticket_event(new_ticket, event_type, changes)

        return None

    async def process_ticket_comparison(self, old_tickets: List[JiraTicket], new_tickets: List[JiraTicket]) -> List[ProcessedJiraEvent]:
        """Compare two sets of tickets and generate events for changes"""
        events = []

        # Create lookup dictionaries
        old_by_key = {ticket.key: ticket for ticket in old_tickets}
        new_by_key = {ticket.key: ticket for ticket in new_tickets}

        # Find new tickets
        for ticket_key, ticket in new_by_key.items():
            if ticket_key not in old_by_key:
                event = self.create_ticket_event(ticket, "created")
                events.append(event)

        # Find updated tickets
        for ticket_key, new_ticket in new_by_key.items():
            if ticket_key in old_by_key:
                old_ticket = old_by_key[ticket_key]
                change_event = self.detect_changes(old_ticket, new_ticket)
                if change_event:
                    events.append(change_event)

        # Find deleted tickets
        for ticket_key, ticket in old_by_key.items():
            if ticket_key not in new_by_key:
                event = self.create_ticket_event(ticket, "deleted")
                events.append(event)

        # Process all events
        return await self.process_events(events)