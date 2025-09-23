"""Jira Sync Coordinator

Orchestrates the synchronization between Jira tickets and MKanban board items.
Handles creating, updating, and moving items based on Jira events.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from src.daemon.core.configuration_service import ConfigurationService
from src.daemon.jira.jira_client import JiraClient, JiraTicket
from src.daemon.jira.jira_event_processor import JiraEventProcessor, ProcessedJiraEvent
from src.domain.entities.board import Board
from src.domain.entities.item import Item
from src.domain.entities.column import Column
# Note: Some imports moved to methods to avoid circular dependencies
from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from src.utils.date_utils import now


class JiraSyncCoordinator:
    """Coordinates synchronization between Jira and MKanban"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")
        self.event_processor = JiraEventProcessor(config_service)
        self._board_service = None
        self._board: Optional[Board] = None
        self._last_sync: Optional[datetime] = None

    def _get_board_service(self):
        """Get or create board service instance"""
        if not self._board_service:
            from src.core.dependency_container import get_container
            from src.services.board_service import BoardService
            container = get_container()
            self._board_service = container.get(BoardService)
        return self._board_service

    def _get_storage(self):
        """Compatibility method - returns MarkdownStorageImpl for legacy code"""
        from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
        data_path = self.config_service.get_data_path()
        return MarkdownStorageImpl(data_path)

    def _get_or_create_board(self) -> Board:
        """Get or create the Jira board"""
        if self._board:
            return self._board

        board_service = self._get_board_service()
        jira_config = self.config_service.get_jira_config()
        board_name = jira_config.board_name

        # Try to load existing board
        try:
            self._board = board_service.get_board_by_name(board_name)
        except Exception:
            self._board = None

        if not self._board:
            # Create new board using BoardService
            self.logger.info(f"Creating new Jira board: {board_name}")
            self._board = board_service.create_board(board_name, "Automatically managed Jira tickets")

            # Add custom columns based on status mapping if needed
            column_names = set(jira_config.status_mapping.values())
            existing_columns = {col.name.lower().replace(" ", "-") for col in self._board.columns}

            for mapped_col in column_names:
                if mapped_col not in existing_columns:
                    # Add missing columns for JIRA status mapping
                    display_name = mapped_col.replace("-", " ").title()
                    board_service.add_column_to_board(self._board.name, display_name)

            # Reload board to get updated columns
            self._board = board_service.get_board_by_name(board_name)

        return self._board

    async def sync_with_jira(self, jira_client: JiraClient) -> int:
        """Perform full synchronization with Jira"""
        self.logger.info("Starting Jira synchronization")

        try:
            # Get current tickets from Jira
            if self._last_sync:
                # Incremental sync - only get tickets updated since last sync
                new_tickets = await jira_client.get_tickets_updated_since(self._last_sync)
                self.logger.debug(f"Found {len(new_tickets)} tickets updated since last sync")
            else:
                # Full sync - get all tickets
                new_tickets = await jira_client.search_tickets()
                self.logger.debug(f"Found {len(new_tickets)} total tickets")

            if not new_tickets:
                self.logger.debug("No tickets to process")
                self._last_sync = datetime.now(timezone.utc)
                return 0

            # Get current items from board
            board = self._get_or_create_board()
            current_items = self._get_all_jira_items(board)

            # Convert current items to tickets for comparison
            current_tickets = []
            for item in current_items:
                if item.jira_metadata:
                    # Create a minimal ticket representation from stored metadata
                    ticket_data = {
                        "key": item.jira_metadata.ticket_key,
                        "id": item.jira_metadata.ticket_id,
                        "fields": {
                            "summary": item.title.split(": ", 1)[-1] if ": " in item.title else item.title,
                            "description": item.description,
                            "status": {"name": item.jira_metadata.jira_status},
                            "issuetype": {"name": item.jira_metadata.issue_type},
                            "priority": {"name": item.jira_metadata.priority} if item.jira_metadata.priority else None,
                            "project": {"key": item.jira_metadata.project_key},
                        },
                        "self": f"{jira_client.config.api_url}/rest/api/3/issue/{item.jira_metadata.ticket_id}"
                    }
                    current_tickets.append(JiraTicket(ticket_data))

            # Compare and generate events
            processed_events = await self.event_processor.process_ticket_comparison(
                current_tickets, new_tickets
            )

            # Execute actions
            actions_executed = 0
            for processed_event in processed_events:
                success = await self._execute_actions(processed_event)
                if success:
                    actions_executed += 1

            self._last_sync = datetime.now(timezone.utc)
            self.logger.info(f"Jira sync completed: {actions_executed} actions executed")

            return actions_executed

        except Exception as e:
            self.logger.error(f"Jira synchronization failed: {e}", exc_info=True)
            return 0

    async def _execute_actions(self, processed_event: ProcessedJiraEvent) -> bool:
        """Execute actions for a processed event"""
        event = processed_event.original_event
        actions = processed_event.actions
        metadata = processed_event.metadata

        board = self._get_or_create_board()
        storage = self._get_storage()

        try:
            for action in actions:
                if action == "create_item":
                    await self._create_item_from_ticket(event.ticket, metadata, board, storage)
                elif action == "update_item_metadata":
                    await self._update_item_metadata(event.ticket, metadata, board, storage)
                elif action == "move_item":
                    await self._move_item(event.ticket, metadata, board, storage)
                elif action == "delete_item":
                    await self._delete_item(event.ticket, board, storage)
                else:
                    self.logger.warning(f"Unknown action: {action}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to execute actions for {event.ticket.key}: {e}")
            return False

    async def _create_item_from_ticket(self, ticket: JiraTicket, metadata: Dict[str, Any],
                                     board: Board, storage: MarkdownStorageImpl) -> None:
        """Create a new item from a Jira ticket"""
        # Check if item already exists
        existing_item = self._find_item_by_ticket_key(board, ticket.key)
        if existing_item:
            self.logger.debug(f"Item for ticket {ticket.key} already exists, updating instead")
            await self._update_item_metadata(ticket, metadata, board, storage)
            return

        # Determine target column
        target_column_id = metadata.get("target_column", "to-do")
        target_column = self._get_or_create_column(board, target_column_id)

        # Create item from ticket
        item = Item.from_jira_ticket(ticket.key, ticket.to_dict(), target_column.id)

        # Add to column and save
        target_column.items.append(item)
        storage.save_board(board)

        self.logger.info(f"Created item for Jira ticket {ticket.key} in column {target_column.name}")

    async def _update_item_metadata(self, ticket: JiraTicket, metadata: Dict[str, Any],
                                  board: Board, storage: MarkdownStorageImpl) -> None:
        """Update an existing item's metadata with conflict resolution"""
        item = self._find_item_by_ticket_key(board, ticket.key)
        if not item:
            self.logger.warning(f"Cannot update metadata for {ticket.key}: item not found")
            return

        # Check for conflicts and resolve them
        conflict_resolved = self._resolve_conflicts(item, ticket)
        if not conflict_resolved:
            self.logger.debug(f"Skipping update for {ticket.key} due to conflict resolution")
            return

        # Update Jira metadata
        if item.jira_metadata:
            item.jira_metadata.jira_status = ticket.status
            item.jira_metadata.priority = ticket.priority
            item.jira_metadata.assignee = ticket.assignee
            item.jira_metadata.labels = ticket.labels
            item.jira_metadata.components = ticket.components
            item.jira_metadata.last_sync = now()

        # Update item fields
        item.title = f"{ticket.key}: {ticket.summary}"
        item.description = ticket.description
        item.updated_at = now()

        storage.save_board(board)

        self.logger.debug(f"Updated metadata for item {ticket.key}")

    def _resolve_conflicts(self, item: Item, ticket: JiraTicket) -> bool:
        """
        Resolve conflicts between local item and Jira ticket updates.
        Returns True if the update should proceed, False if it should be skipped.

        Conflict resolution strategy:
        - Most recent change wins
        - If timestamps are very close (<30 seconds), Jira takes precedence
        """
        from datetime import datetime, timezone, timedelta

        # Get last update times
        local_updated = item.updated_at
        if item.jira_metadata and item.jira_metadata.last_sync:
            pass
        else:
            datetime.fromtimestamp(0, tz=timezone.utc)  # Very old date

        # Parse Jira ticket updated time
        jira_updated = ticket.updated
        if not jira_updated:
            # If Jira has no update time, assume it's newer
            self.logger.debug(f"Jira ticket {ticket.key} has no updated timestamp, allowing update")
            return True

        # Convert to UTC if needed
        if local_updated.tzinfo is None:
            local_updated = local_updated.replace(tzinfo=timezone.utc)
        if jira_updated.tzinfo is None:
            jira_updated = jira_updated.replace(tzinfo=timezone.utc)

        # Calculate time differences
        time_since_local_update = datetime.now(timezone.utc) - local_updated
        datetime.now(timezone.utc) - jira_updated
        time_diff = abs(local_updated - jira_updated)

        # If local item was updated very recently (within last sync interval), check for conflicts
        if time_since_local_update < timedelta(minutes=10):  # 10 minutes threshold
            if time_diff < timedelta(seconds=30):
                # Timestamps are very close, Jira takes precedence
                self.logger.info(f"Conflict detected for {ticket.key}: timestamps close, Jira wins")
                return True
            elif jira_updated > local_updated:
                # Jira is newer
                self.logger.debug(f"Jira update for {ticket.key} is newer, proceeding")
                return True
            else:
                # Local is newer
                self.logger.info(f"Local item {ticket.key} is newer than Jira, skipping update")
                return False
        else:
            # Local item hasn't been updated recently, allow Jira update
            self.logger.debug(f"Local item {ticket.key} not recently updated, allowing Jira update")
            return True

    async def _move_item(self, ticket: JiraTicket, metadata: Dict[str, Any],
                        board: Board, storage: MarkdownStorageImpl) -> None:
        """Move an item to a different column"""
        item = self._find_item_by_ticket_key(board, ticket.key)
        if not item:
            self.logger.warning(f"Cannot move item for {ticket.key}: item not found")
            return

        target_column_id = metadata.get("target_column", "to-do")
        target_column = self._get_or_create_column(board, target_column_id)

        # Find current column
        current_column = None
        for column in board.columns:
            if item in column.items:
                current_column = column
                break

        if current_column and current_column.id == target_column.id:
            self.logger.debug(f"Item {ticket.key} already in target column {target_column.name}")
            return

        # Move item
        if current_column:
            current_column.items.remove(item)

        item.column_id = target_column.id
        target_column.items.append(item)

        # Update metadata
        await self._update_item_metadata(ticket, metadata, board, storage)

        self.logger.info(f"Moved item {ticket.key} to column {target_column.name}")

    async def _delete_item(self, ticket: JiraTicket, board: Board, storage: MarkdownStorageImpl) -> None:
        """Delete an item"""
        item = self._find_item_by_ticket_key(board, ticket.key)
        if not item:
            self.logger.warning(f"Cannot delete item for {ticket.key}: item not found")
            return

        # Find and remove from column
        for column in board.columns:
            if item in column.items:
                column.items.remove(item)
                break

        storage.save_board(board)

        self.logger.info(f"Deleted item for ticket {ticket.key}")

    def _find_item_by_ticket_key(self, board: Board, ticket_key: str) -> Optional[Item]:
        """Find an item by its Jira ticket key"""
        for column in board.columns:
            for item in column.items:
                if (item.is_jira_managed and
                    item.jira_metadata and
                    item.jira_metadata.ticket_key == ticket_key):
                    return item
        return None

    def _get_all_jira_items(self, board: Board) -> List[Item]:
        """Get all Jira-managed items from the board"""
        items = []
        for column in board.columns:
            for item in column.items:
                if item.is_jira_managed:
                    items.append(item)
        return items

    def _get_or_create_column(self, board: Board, column_id: str) -> Column:
        """Get or create a column by ID"""
        # Try to find existing column
        for column in board.columns:
            if column.id == column_id:
                return column

        # Create new column
        display_name = column_id.replace("-", " ").title()
        column = board.add_column(display_name, len(board.columns) + 1)

        # Save board with new column
        storage = self._get_storage()
        storage.save_board(board)

        self.logger.info(f"Created new column: {display_name}")
        return column

    async def sync_item_to_jira(self, item: Item, jira_client: JiraClient) -> bool:
        """Sync an item's status back to Jira"""
        if not item.should_sync_to_jira():
            return True

        jira_config = self.config_service.get_jira_config()
        if not jira_config.bidirectional_sync:
            self.logger.debug(f"Bidirectional sync disabled, skipping sync for {item.get_jira_ticket_key()}")
            return True

        ticket_key = item.get_jira_ticket_key()
        if not ticket_key:
            self.logger.warning("Cannot sync item to Jira: no ticket key")
            return False

        try:
            # Map column to Jira status
            jira_status = self._map_column_to_jira_status(item.column_id)
            if not jira_status:
                self.logger.warning(f"Cannot map column {item.column_id} to Jira status")
                return False

            # Update ticket status in Jira
            success = await jira_client.update_ticket_status(ticket_key, jira_status)

            if success:
                self.logger.info(f"Successfully synced item {ticket_key} to Jira status '{jira_status}'")
                # Update last sync timestamp
                if item.jira_metadata:
                    item.jira_metadata.last_sync = now()
            else:
                self.logger.warning(f"Failed to sync item {ticket_key} to Jira")

            return success

        except Exception as e:
            self.logger.error(f"Error syncing item {ticket_key} to Jira: {e}")
            return False

    def _map_column_to_jira_status(self, column_id: str) -> Optional[str]:
        """Map MKanban column ID to Jira status"""
        jira_config = self.config_service.get_jira_config()

        # Reverse lookup in status mapping
        for jira_status, mapped_column in jira_config.status_mapping.items():
            if mapped_column == column_id:
                return jira_status

        # Default mappings
        if column_id == "backlog":
            return "Backlog"
        elif column_id == "to-do":
            return "To Do"
        elif column_id == "in-progress":
            return "In Progress"
        elif column_id == "done":
            return "Done"
        elif column_id == "review":
            return "In Review"

        return None

    def get_board_name(self) -> str:
        """Get the name of the Jira board"""
        return self.config_service.get_jira_config().board_name