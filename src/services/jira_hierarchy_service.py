"""Jira Hierarchy Service

Manages JIRA ticket hierarchies including epics, stories, and subtasks.
Handles parent-child relationships and syncs them to MKanban item structure.
"""

import logging
from typing import List, Optional, Dict
from src.domain.entities.board import Board
from src.domain.entities.item import Item
from src.daemon.jira.jira_client import JiraClient, JiraTicket
from src.utils.logger_factory import LoggerFactory


class JiraHierarchyService:
    """Service for managing JIRA ticket hierarchies"""

    def __init__(self):
        self.logger = LoggerFactory.get_logger(
            "mkanban-daemon",
            context_type="service",
            service_name="jira_hierarchy"
        )

    async def sync_epic_with_children(
        self,
        epic_key: str,
        jira_client: JiraClient,
        board: Board,
        target_column_id: str = "to-do"
    ) -> Dict[str, Item]:
        """
        Sync an epic and all its children to the board

        Args:
            epic_key: The epic ticket key
            jira_client: JIRA client instance
            board: Target board
            target_column_id: Default column for new items

        Returns:
            Dictionary mapping ticket keys to created/updated items
        """
        self.logger.info(f"Syncing epic {epic_key} with children")
        items = {}

        # Get epic ticket
        epic_ticket = await jira_client.get_ticket(epic_key)
        if not epic_ticket:
            self.logger.error(f"Epic {epic_key} not found")
            return items

        # Get or create epic item
        epic_item = self._find_item_by_ticket_key(board, epic_key)
        if not epic_item:
            column = self._find_column_by_id(board, target_column_id)
            if column:
                epic_item = Item.from_jira_ticket(epic_key, epic_ticket.to_dict(), column.id)
                column.items.append(epic_item)
                self.logger.info(f"Created epic item {epic_key}")

        if epic_item:
            items[epic_key] = epic_item

        # Get all children of the epic
        children = await jira_client.get_epic_children(epic_key)
        self.logger.debug(f"Found {len(children)} children for epic {epic_key}")

        for child_ticket in children:
            child_item = await self._sync_ticket_to_item(
                child_ticket,
                board,
                parent_item=epic_item,
                target_column_id=target_column_id
            )
            if child_item:
                items[child_ticket.key] = child_item

                # Sync subtasks if this child has any
                if child_ticket.subtasks:
                    subtask_items = await self.sync_subtasks(
                        child_ticket.key,
                        jira_client,
                        board,
                        parent_item=child_item,
                        target_column_id=target_column_id
                    )
                    items.update(subtask_items)

        self.logger.info(f"Synced epic {epic_key}: {len(items)} total items")
        return items

    async def sync_subtasks(
        self,
        parent_ticket_key: str,
        jira_client: JiraClient,
        board: Board,
        parent_item: Optional[Item] = None,
        target_column_id: str = "to-do"
    ) -> Dict[str, Item]:
        """
        Sync all subtasks for a parent ticket

        Args:
            parent_ticket_key: Parent ticket key
            jira_client: JIRA client instance
            board: Target board
            parent_item: Parent item (if already created)
            target_column_id: Default column for new items

        Returns:
            Dictionary mapping ticket keys to created/updated items
        """
        self.logger.debug(f"Syncing subtasks for {parent_ticket_key}")
        items = {}

        # Get parent ticket if parent_item not provided
        if not parent_item:
            parent_item = self._find_item_by_ticket_key(board, parent_ticket_key)
            if not parent_item:
                parent_ticket = await jira_client.get_ticket(parent_ticket_key)
                if parent_ticket:
                    column = self._find_column_by_id(board, target_column_id)
                    if column:
                        parent_item = Item.from_jira_ticket(
                            parent_ticket_key,
                            parent_ticket.to_dict(),
                            column.id
                        )
                        column.items.append(parent_item)

        if not parent_item:
            self.logger.warning(f"Cannot sync subtasks: parent item {parent_ticket_key} not found")
            return items

        # Get subtasks
        subtasks = await jira_client.get_subtasks(parent_ticket_key, recursive=False)
        self.logger.debug(f"Found {len(subtasks)} subtasks for {parent_ticket_key}")

        for subtask_ticket in subtasks:
            subtask_item = await self._sync_ticket_to_item(
                subtask_ticket,
                board,
                parent_item=parent_item,
                target_column_id=target_column_id
            )
            if subtask_item:
                items[subtask_ticket.key] = subtask_item

        return items

    async def link_parent_child_relationships(
        self,
        board: Board,
        jira_client: JiraClient
    ) -> int:
        """
        Link JIRA parent-child relationships in MKanban items

        Scans all JIRA-managed items and sets their parent_id based on
        JIRA hierarchy (epic links, parent tickets, etc.)

        Args:
            board: Board to process
            jira_client: JIRA client instance

        Returns:
            Number of relationships linked
        """
        self.logger.info("Linking parent-child relationships from JIRA")
        linked_count = 0

        # Build a map of ticket_key -> item
        ticket_to_item = {}
        for column in board.columns:
            for item in column.items:
                if item.is_jira_managed and item.jira_metadata:
                    ticket_to_item[item.jira_metadata.ticket_key] = item

        # Process each item and link to parent
        for ticket_key, item in ticket_to_item.items():
            if not item.jira_metadata:
                continue

            parent_key = None

            # Determine parent: could be parent ticket or epic
            if item.jira_metadata.parent_ticket_key:
                parent_key = item.jira_metadata.parent_ticket_key
            elif item.jira_metadata.epic_key:
                parent_key = item.jira_metadata.epic_key

            # Link to parent if it exists in our board
            if parent_key and parent_key in ticket_to_item:
                parent_item = ticket_to_item[parent_key]
                if item.parent_id != parent_item.id:
                    item.set_parent(parent_item.id)
                    linked_count += 1
                    self.logger.debug(f"Linked {ticket_key} to parent {parent_key}")

        self.logger.info(f"Linked {linked_count} parent-child relationships")
        return linked_count

    async def sync_issue_links(
        self,
        board: Board,
        jira_client: JiraClient
    ) -> int:
        """
        Sync issue links as cross-references between items

        Updates the linked_tickets field based on JIRA issue links

        Args:
            board: Board to process
            jira_client: JIRA client instance

        Returns:
            Number of links synced
        """
        self.logger.info("Syncing issue links from JIRA")
        links_synced = 0

        # Build a map of ticket_key -> item
        ticket_to_item = {}
        for column in board.columns:
            for item in column.items:
                if item.is_jira_managed and item.jira_metadata:
                    ticket_to_item[item.jira_metadata.ticket_key] = item

        # Process each item and sync its links
        for ticket_key, item in ticket_to_item.items():
            if not item.jira_metadata or not item.jira_metadata.issue_links:
                continue

            # Get all linked ticket keys from JIRA metadata
            linked_keys = [link.get("key") for link in item.jira_metadata.issue_links if link.get("key")]

            # Update the item's linked_tickets
            current_links = set(item.linked_tickets)
            new_links = set(linked_keys)

            # Add new links
            for link_key in new_links - current_links:
                item.add_linked_ticket(link_key)
                links_synced += 1
                self.logger.debug(f"Added link {ticket_key} -> {link_key}")

            # Remove old links that are no longer in JIRA
            for link_key in current_links - new_links:
                item.remove_linked_ticket(link_key)
                self.logger.debug(f"Removed link {ticket_key} -> {link_key}")

        self.logger.info(f"Synced {links_synced} issue links")
        return links_synced

    async def _sync_ticket_to_item(
        self,
        ticket: JiraTicket,
        board: Board,
        parent_item: Optional[Item] = None,
        target_column_id: str = "to-do"
    ) -> Optional[Item]:
        """
        Sync a JIRA ticket to a board item

        Creates or updates the item and sets parent relationship

        Args:
            ticket: JIRA ticket
            board: Target board
            parent_item: Parent item (if any)
            target_column_id: Default column for new items

        Returns:
            Created or updated item
        """
        # Check if item already exists
        existing_item = self._find_item_by_ticket_key(board, ticket.key)

        if existing_item:
            # Update existing item metadata
            if existing_item.jira_metadata:
                existing_item.jira_metadata.jira_status = ticket.status
                existing_item.jira_metadata.priority = ticket.priority
                existing_item.jira_metadata.assignee = ticket.assignee
                existing_item.jira_metadata.labels = ticket.labels
                existing_item.jira_metadata.components = ticket.components
                existing_item.jira_metadata.sprint_name = ticket.sprint
                existing_item.jira_metadata.story_points = ticket.story_points

            # Set parent if provided
            if parent_item and existing_item.parent_id != parent_item.id:
                existing_item.set_parent(parent_item.id)

            return existing_item

        # Create new item
        column = self._find_column_by_id(board, target_column_id)
        if not column:
            self.logger.warning(f"Column {target_column_id} not found, cannot create item for {ticket.key}")
            return None

        new_item = Item.from_jira_ticket(ticket.key, ticket.to_dict(), column.id)

        # Set parent if provided
        if parent_item:
            new_item.set_parent(parent_item.id)

        column.items.append(new_item)
        self.logger.debug(f"Created item for {ticket.key}")

        return new_item

    def _find_item_by_ticket_key(self, board: Board, ticket_key: str) -> Optional[Item]:
        """Find an item by its JIRA ticket key"""
        for column in board.columns:
            for item in column.items:
                if (item.is_jira_managed and
                    item.jira_metadata and
                    item.jira_metadata.ticket_key == ticket_key):
                    return item
        return None

    def _find_column_by_id(self, board: Board, column_id: str):
        """Find a column by ID"""
        for column in board.columns:
            if column.id == column_id:
                return column
        return None
