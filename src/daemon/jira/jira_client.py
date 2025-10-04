"""Jira API Client

Handles all interactions with the Jira REST API, including authentication,
ticket fetching, status updates, and error handling.
"""

import logging
import re
from typing import List, Optional
from datetime import datetime
import aiohttp
import base64

from src.daemon.core.configuration_service import JiraConfig
from .exceptions import JiraAuthError, JiraAPIError
from .ticket import JiraTicket


class JiraClient:
    """Async Jira API client"""

    def __init__(self, config: JiraConfig):
        self.config = config
        self.logger = logging.getLogger("mkanban-daemon")
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_header = self._create_auth_header()

    def _create_auth_header(self) -> str:
        """Create Basic Auth header for Jira API"""
        if not self.config.username or not self.config.api_token:
            raise JiraAuthError("Jira username and API token are required")

        auth_string = f"{self.config.username}:{self.config.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        return f"Basic {auth_b64}"

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def test_connection(self) -> bool:
        """Test connection to Jira API"""
        try:
            url = f"{self.config.api_url}/rest/api/3/myself"
            async with self.session.get(url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    self.logger.info(f"Successfully connected to Jira as {user_data.get('displayName', 'Unknown')}")
                    return True
                else:
                    self.logger.error(f"Jira connection test failed with status {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"Jira connection test failed: {e}")
            return False

    async def search_tickets(self, jql: str = "", max_results: int = 50) -> List[JiraTicket]:
        """Search for tickets using JQL"""
        if not jql and self.config.project_keys:
            # Default JQL: get tickets from configured projects assigned to current user or unassigned
            projects = ",".join(self.config.project_keys)
            jql = f"project in ({projects}) AND (assignee = currentUser() OR assignee is EMPTY) ORDER BY updated DESC"
        elif not jql:
            # No JQL and no projects configured - get tickets assigned to current user or unassigned
            jql = "(assignee = currentUser() OR assignee is EMPTY) ORDER BY updated DESC"

        # Apply backlog limit if configured and reasonable
        effective_max = max_results
        if self.config.backlog_limit > 0:
            effective_max = min(max_results, self.config.backlog_limit)
        elif self.config.backlog_limit == -1:
            effective_max = max_results  # Use provided max_results, no additional limit

        # Apply custom JQL filter if configured
        if self.config.jql_filter:
            if jql and "ORDER BY" in jql:
                # Insert filter before ORDER BY
                parts = jql.split("ORDER BY")
                jql = f"{parts[0].strip()} AND {self.config.jql_filter} ORDER BY {parts[1].strip()}"
            else:
                jql = f"{jql} AND {self.config.jql_filter}" if jql else self.config.jql_filter

        try:
            url = f"{self.config.api_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": effective_max,
                "fields": "id,key,summary,description,status,issuetype,priority,assignee,reporter,project,labels,components,created,updated,subtasks,parent,issuelinks,customfield_10014,customfield_10016,customfield_10020,customfield_10026,customfield_10002,sprint,fixVersions,versions"
            }

            self.logger.debug(f"Searching Jira tickets with JQL: {jql}")

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tickets = [JiraTicket(issue) for issue in data.get("issues", [])]
                    self.logger.debug(f"Found {len(tickets)} Jira tickets")
                    return tickets
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to search Jira tickets: {response.status} - {error_text}")
                    raise JiraAPIError(f"Search failed: {response.status}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error searching Jira tickets: {e}")
            raise JiraAPIError(f"Network error: {e}")

    async def get_ticket(self, ticket_key: str) -> Optional[JiraTicket]:
        """Get a specific ticket by key"""
        try:
            url = f"{self.config.api_url}/rest/api/3/issue/{ticket_key}"
            params = {
                "fields": "id,key,summary,description,status,issuetype,priority,assignee,reporter,project,labels,components,created,updated,subtasks,parent,issuelinks,customfield_10014,customfield_10016,customfield_10020,customfield_10026,customfield_10002,sprint,fixVersions,versions"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return JiraTicket(data)
                elif response.status == 404:
                    self.logger.warning(f"Jira ticket {ticket_key} not found")
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to get Jira ticket {ticket_key}: {response.status} - {error_text}")
                    return None

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error getting Jira ticket {ticket_key}: {e}")
            return None

    async def update_ticket_status(self, ticket_key: str, status_name: str) -> bool:
        """Update ticket status"""
        if not self.config.bidirectional_sync:
            self.logger.debug(f"Bidirectional sync disabled, skipping status update for {ticket_key}")
            return True

        try:
            # First, get available transitions for the ticket
            transitions_url = f"{self.config.api_url}/rest/api/3/issue/{ticket_key}/transitions"

            async with self.session.get(transitions_url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to get transitions for {ticket_key}: {response.status}")
                    return False

                transitions_data = await response.json()
                transitions = transitions_data.get("transitions", [])

                # Find transition that moves to the desired status
                target_transition = None
                for transition in transitions:
                    if transition.get("to", {}).get("name", "").lower() == status_name.lower():
                        target_transition = transition
                        break

                if not target_transition:
                    self.logger.warning(f"No transition found to status '{status_name}' for ticket {ticket_key}")
                    return False

                # Execute the transition
                transition_url = f"{self.config.api_url}/rest/api/3/issue/{ticket_key}/transitions"
                transition_data = {
                    "transition": {
                        "id": target_transition["id"]
                    }
                }

                async with self.session.post(transition_url, json=transition_data) as response:
                    if response.status == 204:
                        self.logger.info(f"Successfully updated {ticket_key} status to '{status_name}'")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to update {ticket_key} status: {response.status} - {error_text}")
                        return False

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error updating {ticket_key} status: {e}")
            return False

    async def add_comment(self, ticket_key: str, comment: str) -> bool:
        """Add a comment to a ticket"""
        if not self.config.bidirectional_sync:
            self.logger.debug(f"Bidirectional sync disabled, skipping comment for {ticket_key}")
            return True

        try:
            url = f"{self.config.api_url}/rest/api/3/issue/{ticket_key}/comment"
            comment_data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }

            async with self.session.post(url, json=comment_data) as response:
                if response.status == 201:
                    self.logger.debug(f"Successfully added comment to {ticket_key}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to add comment to {ticket_key}: {response.status} - {error_text}")
                    return False

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error adding comment to {ticket_key}: {e}")
            return False

    def extract_ticket_keys_from_text(self, text: str) -> List[str]:
        """Extract Jira ticket keys from text (branch names, commit messages, etc.)"""
        # Pattern to match Jira ticket keys (PROJECT-123 format)
        pattern = r'\b[A-Z][A-Z0-9]*-\d+\b'
        matches = re.findall(pattern, text.upper())

        # Filter by configured project keys if specified
        if self.config.project_keys:
            filtered_matches = []
            for match in matches:
                project_key = match.split("-")[0]
                if project_key in self.config.project_keys:
                    filtered_matches.append(match)
            return list(set(filtered_matches))  # Remove duplicates

        return list(set(matches))  # Remove duplicates

    async def get_tickets_updated_since(self, since: datetime) -> List[JiraTicket]:
        """Get tickets updated since a specific datetime"""
        # Format datetime for JQL (Jira expects YYYY-MM-DD HH:mm format)
        since_str = since.strftime("%Y-%m-%d %H:%M")

        jql = f"updated >= '{since_str}' AND (assignee = currentUser() OR assignee is EMPTY)"

        # Add project filter if configured
        if self.config.project_keys:
            projects = ",".join(self.config.project_keys)
            jql = f"project in ({projects}) AND {jql}"

        jql += " ORDER BY updated DESC"

        # Use configured backlog limit for incremental sync as well
        max_results = 100
        if self.config.backlog_limit > 0:
            max_results = min(100, self.config.backlog_limit)
        elif self.config.backlog_limit == -1:
            max_results = 500  # Reasonable limit for incremental sync even if backlog is unlimited

        return await self.search_tickets(jql, max_results=max_results)

    async def get_backlog_tickets(self) -> List[JiraTicket]:
        """Get tickets specifically from backlog"""
        # Build JQL for backlog tickets
        jql_parts = []

        # Project filter
        if self.config.project_keys:
            projects = ",".join(self.config.project_keys)
            jql_parts.append(f"project in ({projects})")

        # Assignee filter
        jql_parts.append("(assignee = currentUser() OR assignee is EMPTY)")

        # Backlog status filter
        jql_parts.append("status = 'Backlog'")

        jql = " AND ".join(jql_parts) + " ORDER BY created DESC"

        # Apply backlog limit
        max_results = 50  # Default reasonable limit
        if self.config.backlog_limit > 0:
            max_results = self.config.backlog_limit
        elif self.config.backlog_limit == -1:
            max_results = 1000  # Large but reasonable limit for unlimited

        return await self.search_tickets(jql, max_results=max_results)

    async def get_subtasks(self, ticket_key: str, recursive: bool = False) -> List[JiraTicket]:
        """Get all subtasks for a ticket, optionally recursively"""
        ticket = await self.get_ticket(ticket_key)
        if not ticket or not ticket.subtasks:
            return []

        subtasks = []
        for subtask_key in ticket.subtasks:
            subtask = await self.get_ticket(subtask_key)
            if subtask:
                subtasks.append(subtask)
                # Recursively get subtasks of subtasks if requested
                if recursive and subtask.subtasks:
                    nested_subtasks = await self.get_subtasks(subtask_key, recursive=True)
                    subtasks.extend(nested_subtasks)

        return subtasks

    async def get_epic_children(self, epic_key: str, max_results: int = 100) -> List[JiraTicket]:
        """Get all issues that belong to an epic"""
        try:
            # Use JQL to find all issues linked to this epic
            # The epic link field varies by JIRA instance
            jql = f'"Epic Link" = {epic_key} OR parent = {epic_key} ORDER BY rank ASC, created DESC'

            return await self.search_tickets(jql, max_results=max_results)

        except Exception as e:
            self.logger.error(f"Failed to get epic children for {epic_key}: {e}")
            return []

    async def get_tickets_with_hierarchy(
        self,
        base_jql: str = "",
        include_subtasks: bool = True,
        include_epic_children: bool = True,
        max_depth: int = 2
    ) -> List[JiraTicket]:
        """
        Fetch tickets with their full hierarchy (subtasks, epic children)

        Args:
            base_jql: Base JQL query for parent tickets
            include_subtasks: Whether to fetch subtasks
            include_epic_children: Whether to fetch epic children
            max_depth: Maximum depth of hierarchy to fetch (1 = no children, 2 = children only, 3+ = nested)

        Returns:
            List of all tickets including parents and children
        """
        if max_depth < 1:
            return []

        # Fetch base tickets
        base_tickets = await self.search_tickets(base_jql)
        if not base_tickets or max_depth == 1:
            return base_tickets

        all_tickets = list(base_tickets)
        seen_keys = {ticket.key for ticket in base_tickets}

        # Fetch children for each base ticket
        for ticket in base_tickets:
            # Fetch subtasks
            if include_subtasks and ticket.subtasks:
                for subtask_key in ticket.subtasks:
                    if subtask_key not in seen_keys:
                        subtask = await self.get_ticket(subtask_key)
                        if subtask:
                            all_tickets.append(subtask)
                            seen_keys.add(subtask_key)

                            # Recursively fetch nested subtasks if depth allows
                            if max_depth > 2 and subtask.subtasks:
                                nested = await self.get_subtasks(subtask_key, recursive=(max_depth > 3))
                                for nested_task in nested:
                                    if nested_task.key not in seen_keys:
                                        all_tickets.append(nested_task)
                                        seen_keys.add(nested_task.key)

            # Fetch epic children
            if include_epic_children and ticket.issue_type.lower() == "epic":
                epic_children = await self.get_epic_children(ticket.key)
                for child in epic_children:
                    if child.key not in seen_keys:
                        all_tickets.append(child)
                        seen_keys.add(child.key)

                        # Fetch subtasks of epic children if depth allows
                        if include_subtasks and max_depth > 2 and child.subtasks:
                            for subtask_key in child.subtasks:
                                if subtask_key not in seen_keys:
                                    subtask = await self.get_ticket(subtask_key)
                                    if subtask:
                                        all_tickets.append(subtask)
                                        seen_keys.add(subtask_key)

        self.logger.debug(f"Fetched {len(all_tickets)} tickets including hierarchy (base: {len(base_tickets)})")
        return all_tickets