"""Branch-Ticket Linker

Handles linking git branches to Jira tickets by detecting ticket keys
in branch names and maintaining associations between git and Jira items.
"""

import logging
import re
from typing import List, Dict, Optional

from src.daemon.core.configuration_service import ConfigurationService
from src.daemon.jira.jira_client import JiraClient
from src.domain.entities.item import Item
from src.domain.entities.board import Board
from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl
from src.utils.date_utils import now


class BranchTicketLinker:
    """Links git branches to Jira tickets"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")

    def extract_ticket_keys_from_branch(self, branch_name: str) -> List[str]:
        """Extract first Jira ticket key from a branch name (simplified to single ticket)"""
        jira_config = self.config_service.get_jira_config()

        # Use the Jira client's extraction method for consistency
        # Create a temporary client just for the extraction
        if jira_config.enabled:
            try:
                client = JiraClient(jira_config)
                all_keys = client.extract_ticket_keys_from_text(branch_name)
                # Return only the first ticket key found
                if all_keys:
                    first_key = all_keys[0]
                    if len(all_keys) > 1:
                        self.logger.warning(f"Multiple ticket keys found in branch {branch_name}: {all_keys}. Using first: {first_key}")
                    return [first_key]
                return []
            except Exception as e:
                self.logger.debug(f"Could not use JiraClient for ticket extraction: {e}")

        # Fallback to manual extraction
        return self._extract_ticket_keys_fallback(branch_name)

    def _extract_ticket_keys_fallback(self, text: str) -> List[str]:
        """Fallback method for extracting the first ticket key"""
        # Pattern to match Jira ticket keys (PROJECT-123 format)
        pattern = r'\b[A-Z][A-Z0-9]*-\d+\b'
        matches = re.findall(pattern, text.upper())

        if not matches:
            return []

        # Filter by configured project keys if specified
        jira_config = self.config_service.get_jira_config()
        if jira_config.project_keys:
            for match in matches:
                project_key = match.split("-")[0]
                if project_key in jira_config.project_keys:
                    # Return first valid match
                    if len(matches) > 1:
                        self.logger.warning(f"Multiple ticket keys found in branch {text}: {matches}. Using first valid: {match}")
                    return [match]
            return []  # No valid project keys found

        # Return first match if no project filtering
        first_match = matches[0]
        if len(matches) > 1:
            self.logger.warning(f"Multiple ticket keys found in branch {text}: {matches}. Using first: {first_match}")
        return [first_match]

    async def link_branch_to_tickets(self, repository_path: str, branch_name: str,
                                   git_board: Board, jira_board: Board,
                                   storage: MarkdownStorageImpl) -> List[str]:
        """Link a git branch to Jira tickets"""
        ticket_keys = self.extract_ticket_keys_from_branch(branch_name)

        if not ticket_keys:
            self.logger.debug(f"No ticket keys found in branch name: {branch_name}")
            return []

        linked_tickets = []

        for ticket_key in ticket_keys:
            try:
                success = await self._link_single_ticket(
                    repository_path, branch_name, ticket_key,
                    git_board, jira_board, storage
                )
                if success:
                    linked_tickets.append(ticket_key)
            except Exception as e:
                self.logger.error(f"Failed to link branch {branch_name} to ticket {ticket_key}: {e}")

        if linked_tickets:
            self.logger.info(f"Linked branch {branch_name} to tickets: {linked_tickets}")

        return linked_tickets

    async def _link_single_ticket(self, repository_path: str, branch_name: str,
                                ticket_key: str, git_board: Board, jira_board: Board,
                                storage: MarkdownStorageImpl) -> bool:
        """Link a single ticket to a git branch"""
        # Find git item for this branch
        git_item = self._find_git_item_for_branch(git_board, repository_path, branch_name)
        if not git_item:
            self.logger.debug(f"No git item found for branch {branch_name}")
            return False

        # Find Jira item for this ticket
        jira_item = self._find_jira_item_for_ticket(jira_board, ticket_key)
        if not jira_item:
            self.logger.debug(f"No Jira item found for ticket {ticket_key}")
            return False

        # Link them together
        self._create_bidirectional_link(git_item, jira_item, git_board, jira_board, storage)

        return True

    def _find_git_item_for_branch(self, board: Board, repository_path: str, branch_name: str) -> Optional[Item]:
        """Find a git item for a specific branch"""
        for column in board.columns:
            for item in column.items:
                if (item.is_git_managed and
                    item.git_metadata and
                    item.git_metadata.repository_path == repository_path and
                    item.git_metadata.branch_name == branch_name):
                    return item
        return None

    def _find_jira_item_for_ticket(self, board: Board, ticket_key: str) -> Optional[Item]:
        """Find a Jira item for a specific ticket key"""
        for column in board.columns:
            for item in column.items:
                if (item.is_jira_managed and
                    item.metadata.get("ticket_key") == ticket_key):
                    return item
        return None

    def _create_bidirectional_link(self, git_item: Item, jira_item: Item,
                                 git_board: Board, jira_board: Board,
                                 storage: MarkdownStorageImpl) -> None:
        """Create bidirectional links between git and Jira items"""
        # Add ticket key to git item's linked tickets
        ticket_key = jira_item.metadata.get("ticket_key", "")
        git_item.add_linked_ticket(ticket_key)

        # Update git item description with ticket link if not already present
        if ticket_key not in git_item.description:
            if git_item.description:
                git_item.description += f"\n\nLinked to Jira: {ticket_key}"
            else:
                git_item.description = f"Linked to Jira: {ticket_key}"

        # Add git metadata reference to Jira item description if not already present
        if git_item.git_metadata:
            branch_ref = f"Branch: {git_item.git_metadata.branch_name}"
            if branch_ref not in jira_item.description:
                if jira_item.description:
                    jira_item.description += f"\n\nLinked to Git: {branch_ref}"
                else:
                    jira_item.description = f"Linked to Git: {branch_ref}"

        # Update timestamps
        git_item.updated_at = now()
        jira_item.updated_at = now()

        # Save both boards
        storage.save_board(git_board)
        if git_board.id != jira_board.id:  # Don't save twice if same board
            storage.save_board(jira_board)

        self.logger.debug(f"Created bidirectional link: {git_item.git_metadata.branch_name} <-> {ticket_key}")

    async def update_linked_items_status(self, repository_path: str, branch_name: str,
                                       is_current_branch: bool, storage: MarkdownStorageImpl) -> None:
        """Update status of linked items when branch status changes"""
        # Get both boards
        git_board_name = self.config_service.get_board_name()  # Git board name
        jira_board_name = self.config_service.get_jira_config().board_name

        git_board = storage.load_board_by_name(git_board_name)
        jira_board = storage.load_board_by_name(jira_board_name)

        if not git_board or not jira_board:
            self.logger.debug("Git or Jira board not found for status update")
            return

        # Find git item
        git_item = self._find_git_item_for_branch(git_board, repository_path, branch_name)
        if not git_item or not git_item.linked_tickets:
            return

        # Update linked Jira items based on git item status
        for ticket_key in git_item.linked_tickets:
            jira_item = self._find_jira_item_for_ticket(jira_board, ticket_key)
            if jira_item:
                await self._sync_git_status_to_jira(git_item, jira_item, is_current_branch,
                                                  git_board, jira_board, storage)

    async def _sync_git_status_to_jira(self, git_item: Item, jira_item: Item,
                                     is_current_branch: bool, git_board: Board,
                                     jira_board: Board, storage: MarkdownStorageImpl) -> None:
        """Sync git item status to linked Jira item"""
        jira_config = self.config_service.get_jira_config()

        # Only sync if bidirectional sync is enabled
        if not jira_config.bidirectional_sync:
            return

        # Determine target status based on git state
        if is_current_branch and git_item.git_metadata.is_current_branch:
            # Branch is currently checked out - move to in-progress
            target_column_id = "in-progress"
        elif git_item.should_auto_complete():
            # Branch is deleted/merged - move to done
            target_column_id = "done"
        else:
            # No change needed
            return

        # Find target column in Jira board
        target_column = None
        for column in jira_board.columns:
            if column.id == target_column_id:
                target_column = column
                break

        if not target_column:
            self.logger.warning(f"Target column {target_column_id} not found in Jira board")
            return

        # Move Jira item if it's not already in the target column
        if jira_item.column_id != target_column_id:
            # Remove from current column
            for column in jira_board.columns:
                if jira_item in column.items:
                    column.items.remove(jira_item)
                    break

            # Add to target column
            jira_item.column_id = target_column_id
            target_column.items.append(jira_item)
            jira_item.updated_at = now()

            # Save board
            storage.save_board(jira_board)

            self.logger.info(f"Synced Jira item {jira_item.metadata.get('ticket_key', '')} to column {target_column.name} based on git status")

    def get_linked_tickets_for_branch(self, board: Board, repository_path: str, branch_name: str) -> List[str]:
        """Get linked ticket keys for a git branch"""
        git_item = self._find_git_item_for_branch(board, repository_path, branch_name)
        if git_item:
            return git_item.linked_tickets.copy()
        return []

    def get_linked_branches_for_ticket(self, git_board: Board, ticket_key: str) -> List[Dict[str, str]]:
        """Get linked branches for a Jira ticket"""
        linked_branches = []

        for column in git_board.columns:
            for item in column.items:
                if (item.is_git_managed and
                    item.git_metadata and
                    ticket_key in item.linked_tickets):
                    linked_branches.append({
                        "repository_path": item.git_metadata.repository_path,
                        "branch_name": item.git_metadata.branch_name,
                        "is_current": item.git_metadata.is_current_branch,
                        "branch_full_name": item.git_metadata.branch_full_name
                    })

        return linked_branches

    async def cleanup_orphaned_links(self, storage: MarkdownStorageImpl) -> int:
        """Clean up orphaned links (git items with no corresponding Jira items or vice versa)"""
        # Get both boards
        git_board_name = self.config_service.get_board_name()
        jira_board_name = self.config_service.get_jira_config().board_name

        git_board = storage.load_board_by_name(git_board_name)
        jira_board = storage.load_board_by_name(jira_board_name)

        if not git_board or not jira_board:
            self.logger.debug("Git or Jira board not found for cleanup")
            return 0

        cleanup_count = 0

        # Check git items for orphaned ticket links
        for column in git_board.columns:
            for git_item in column.items:
                if git_item.is_git_managed and git_item.linked_tickets:
                    valid_tickets = []
                    for ticket_key in git_item.linked_tickets:
                        jira_item = self._find_jira_item_for_ticket(jira_board, ticket_key)
                        if jira_item:
                            valid_tickets.append(ticket_key)
                        else:
                            self.logger.info(f"Removing orphaned ticket link {ticket_key} from git item {git_item.title}")
                            cleanup_count += 1

                    # Update linked tickets to only valid ones
                    git_item.linked_tickets = valid_tickets
                    if cleanup_count > 0:
                        git_item.updated_at = now()

        # Save git board if changes were made
        if cleanup_count > 0:
            storage.save_board(git_board)
            self.logger.info(f"Cleaned up {cleanup_count} orphaned ticket links")

        return cleanup_count