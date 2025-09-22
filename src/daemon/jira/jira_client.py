"""Jira API Client

Handles all interactions with the Jira REST API, including authentication,
ticket fetching, status updates, and error handling.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import aiohttp
import base64
import json

from daemon.core.configuration_service import JiraConfig
from src.core.exceptions import MKanbanError


class JiraError(MKanbanError):
    """Jira-specific error"""
    pass


class JiraAuthError(JiraError):
    """Jira authentication error"""
    pass


class JiraAPIError(JiraError):
    """Jira API error"""
    pass


class JiraTicket:
    """Represents a Jira ticket with relevant fields"""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.key = data.get("key", "")
        self.id = data.get("id", "")

        fields = data.get("fields", {})
        self.summary = fields.get("summary") or ""
        self.description = fields.get("description") or ""
        self.status = fields.get("status", {}).get("name", "")
        self.issue_type = fields.get("issuetype", {}).get("name", "")
        self.priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else None
        self.assignee = fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else None
        self.reporter = fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else None
        self.project_key = fields.get("project", {}).get("key", "")

        # Handle labels and components
        self.labels = fields.get("labels", [])
        self.components = [comp.get("name", "") for comp in fields.get("components", [])]

        # Parse timestamps
        self.created = self._parse_timestamp(fields.get("created"))
        self.updated = self._parse_timestamp(fields.get("updated"))

        # Construct URL
        self.url = f"{data.get('self', '').split('/rest/')[0]}/browse/{self.key}" if data.get('self') else ""

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira timestamp string to datetime"""
        if not timestamp_str:
            return None
        try:
            # Jira uses ISO format with timezone
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def get_project_key(self) -> str:
        """Extract project key from ticket key"""
        if "-" in self.key:
            return self.key.split("-")[0]
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "key": self.key,
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "project_key": self.project_key,
            "labels": self.labels,
            "components": self.components,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "url": self.url,
        }


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
                "fields": "id,key,summary,description,status,issuetype,priority,assignee,reporter,project,labels,components,created,updated"
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
                "fields": "id,key,summary,description,status,issuetype,priority,assignee,reporter,project,labels,components,created,updated"
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