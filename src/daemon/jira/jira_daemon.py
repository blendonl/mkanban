"""Jira Daemon

Main daemon service for Jira integration. Manages the lifecycle of Jira
synchronization, including periodic polling, event processing, and
coordination with the MKanban board.
"""

import asyncio
import logging
import os
from typing import Optional

from daemon.core.configuration_service import ConfigurationService, JiraConfig
from daemon.jira.jira_client import JiraClient, JiraAuthError, JiraAPIError
from daemon.jira.jira_sync_coordinator import JiraSyncCoordinator
from src.core.exceptions import MKanbanError


class JiraDaemonError(MKanbanError):
    """Jira daemon specific error"""
    pass


class JiraDaemon:
    """Main Jira daemon service"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.jira_config = config_service.get_jira_config()
        self.logger = logging.getLogger("mkanban-daemon")
        self.sync_coordinator = JiraSyncCoordinator(config_service)
        self.running = False
        self._jira_client: Optional[JiraClient] = None
        self._last_error: Optional[Exception] = None

    async def start(self) -> None:
        """Start the Jira daemon"""
        if self.running:
            raise JiraDaemonError("Jira daemon is already running")

        if not self.jira_config.enabled:
            self.logger.info("Jira integration is disabled")
            return

        self.logger.info("Starting Jira daemon...")

        try:
            # Validate configuration
            await self._validate_config()

            # Test Jira connection
            await self._test_connection()

            self.running = True
            self.logger.info(f"Jira daemon started successfully for board '{self.jira_config.board_name}'")

            # Start main sync loop
            await self._run_sync_loop()

        except Exception as e:
            self.logger.error(f"Failed to start Jira daemon: {e}")
            self.running = False
            self._last_error = e
            raise

    async def stop(self) -> None:
        """Stop the Jira daemon"""
        if not self.running:
            return

        self.logger.info("Stopping Jira daemon...")
        self.running = False

        # Close Jira client connection
        if self._jira_client:
            await self._jira_client.__aexit__(None, None, None)
            self._jira_client = None

        self.logger.info("Jira daemon stopped")

    async def _validate_config(self) -> None:
        """Validate Jira configuration"""
        config = self.jira_config

        if not config.api_url:
            raise JiraDaemonError("Jira API URL is required")

        if not config.username:
            # Try to get from environment
            config.username = os.getenv("JIRA_USERNAME", "")
            if not config.username:
                raise JiraDaemonError("Jira username is required (set JIRA_USERNAME env var)")

        if not config.api_token:
            # Try to get from environment
            config.api_token = os.getenv("JIRA_API_TOKEN", "")
            if not config.api_token:
                raise JiraDaemonError("Jira API token is required (set JIRA_API_TOKEN env var)")

        if config.polling_interval < 60:
            self.logger.warning(f"Jira polling interval {config.polling_interval}s is very short, consider increasing")

        self.logger.debug(f"Jira configuration validated for {config.api_url}")

    async def _test_connection(self) -> None:
        """Test connection to Jira API"""
        try:
            self._jira_client = JiraClient(self.jira_config)
            async with self._jira_client:
                success = await self._jira_client.test_connection()
                if not success:
                    raise JiraDaemonError("Jira connection test failed")

        except JiraAuthError as e:
            raise JiraDaemonError(f"Jira authentication failed: {e}")
        except JiraAPIError as e:
            raise JiraDaemonError(f"Jira API error: {e}")

    async def _run_sync_loop(self) -> None:
        """Main synchronization loop"""
        self.logger.info(f"Starting Jira sync loop with {self.jira_config.polling_interval}s interval")

        loop_count = 0
        while self.running:
            try:
                loop_count += 1

                # Log status periodically
                if loop_count % max(1, 300 // self.jira_config.polling_interval) == 1:  # Every ~5 minutes
                    self.logger.debug(f"Jira sync loop iteration {loop_count}")

                # Perform synchronization
                await self._perform_sync()

                # Wait for next iteration
                await asyncio.sleep(self.jira_config.polling_interval)

            except asyncio.CancelledError:
                self.logger.info("Jira sync loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in Jira sync loop: {e}")
                self._last_error = e

                # Exponential backoff on errors
                error_delay = min(60, 5 * (loop_count % 10))  # 5s to 60s
                self.logger.debug(f"Waiting {error_delay}s before retry due to error")
                await asyncio.sleep(error_delay)

    async def _perform_sync(self) -> None:
        """Perform a single synchronization cycle"""
        if not self._jira_client:
            self._jira_client = JiraClient(self.jira_config)

        try:
            async with self._jira_client:
                # Test connection first
                if not await self._jira_client.test_connection():
                    self.logger.warning("Jira connection test failed, skipping sync")
                    return

                # Perform sync
                actions_executed = await self.sync_coordinator.sync_with_jira(self._jira_client)

                if actions_executed > 0:
                    self.logger.info(f"Jira sync completed: {actions_executed} actions executed")
                else:
                    self.logger.debug("Jira sync completed: no changes")

                # Clear any previous errors on successful sync
                self._last_error = None

        except JiraAuthError as e:
            self.logger.error(f"Jira authentication error during sync: {e}")
            self._last_error = e
        except JiraAPIError as e:
            self.logger.error(f"Jira API error during sync: {e}")
            self._last_error = e
        except Exception as e:
            self.logger.error(f"Unexpected error during Jira sync: {e}")
            self._last_error = e

    async def force_sync(self) -> int:
        """Force an immediate synchronization"""
        self.logger.info("Forcing Jira synchronization")

        if not self.running:
            raise JiraDaemonError("Jira daemon is not running")

        try:
            await self._perform_sync()
            return 1  # Success
        except Exception as e:
            self.logger.error(f"Force sync failed: {e}")
            return 0  # Failure

    def get_status(self) -> dict:
        """Get daemon status information"""
        return {
            "running": self.running,
            "board_name": self.jira_config.board_name,
            "api_url": self.jira_config.api_url,
            "polling_interval": self.jira_config.polling_interval,
            "project_keys": self.jira_config.project_keys,
            "bidirectional_sync": self.jira_config.bidirectional_sync,
            "last_error": str(self._last_error) if self._last_error else None,
        }

    def is_running(self) -> bool:
        """Check if daemon is running"""
        return self.running

    def get_last_error(self) -> Optional[Exception]:
        """Get the last error that occurred"""
        return self._last_error

    async def sync_item_to_jira(self, item) -> bool:
        """Sync a specific item back to Jira"""
        if not self.running:
            self.logger.warning("Cannot sync item to Jira: daemon not running")
            return False

        if not self._jira_client:
            self._jira_client = JiraClient(self.jira_config)

        try:
            async with self._jira_client:
                return await self.sync_coordinator.sync_item_to_jira(item, self._jira_client)
        except Exception as e:
            self.logger.error(f"Failed to sync item to Jira: {e}")
            return False

    def update_config(self, new_config: JiraConfig) -> None:
        """Update Jira configuration"""
        old_config = self.jira_config
        self.jira_config = new_config
        self.config_service.config.jira = new_config

        # Log configuration changes
        if old_config.api_url != new_config.api_url:
            self.logger.info(f"Jira API URL changed: {old_config.api_url} -> {new_config.api_url}")

        if old_config.project_keys != new_config.project_keys:
            self.logger.info(f"Jira project keys changed: {old_config.project_keys} -> {new_config.project_keys}")

        if old_config.polling_interval != new_config.polling_interval:
            self.logger.info(f"Jira polling interval changed: {old_config.polling_interval} -> {new_config.polling_interval}")

        # Force reconnection on next sync
        self._jira_client = None

    async def get_jira_tickets(self, jql: str = "", max_results: int = 50) -> list:
        """Get tickets from Jira (for debugging/testing)"""
        if not self._jira_client:
            self._jira_client = JiraClient(self.jira_config)

        try:
            async with self._jira_client:
                tickets = await self._jira_client.search_tickets(jql, max_results)
                return [ticket.to_dict() for ticket in tickets]
        except Exception as e:
            self.logger.error(f"Failed to get Jira tickets: {e}")
            return []