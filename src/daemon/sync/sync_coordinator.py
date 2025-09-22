"""Sync Coordinator

Orchestrates the synchronization process between git events and kanban tasks,
coordinating between EventProcessor and TaskManager.
"""

import logging
from typing import List

from daemon.git_monitor import GitEvent
from daemon.core.configuration_service import ConfigurationService
from daemon.core.session_context_manager import SessionContext
from daemon.sync.event_processor import EventProcessor
from daemon.sync.task_manager import TaskManager
from daemon.sync.session_task_coordinator import SessionTaskCoordinator


class SyncCoordinator:
    """Coordinates git-to-kanban synchronization"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")

        # Initialize components
        self.event_processor = EventProcessor(config_service)
        self.task_manager = TaskManager(config_service)
        self.session_task_coordinator = SessionTaskCoordinator(config_service, self.task_manager)

    async def process_events(self, events: List[GitEvent]) -> None:
        """Process a list of git events and synchronize with kanban tasks"""
        if not events:
            return

        board_name = self.config_service.get_board_name()
        event_types = [e.event_type.value for e in events]

        self.logger.debug(
            f"[{board_name}] Processing {len(events)} events: {event_types}"
        )

        # Process events to determine actions
        processed_events = await self.event_processor.process_events(events)

        # Execute actions via TaskManager
        for processed_event in processed_events:
            await self._execute_actions(processed_event)

        # Process branch-ticket linking if Jira is enabled
        if self.config_service.is_jira_enabled():
            await self._process_jira_linking(events)

        self.logger.debug(
            f"[{board_name}] Finished processing {len(events)} events"
        )

    async def _execute_actions(self, processed_event) -> None:
        """Execute the actions for a processed event"""
        event = processed_event.original_event
        actions = processed_event.actions
        metadata = processed_event.metadata

        board_name = self.config_service.get_board_name()

        self.logger.debug(
            f"[{board_name}] Executing actions {actions} for event "
            f"{event.event_type.value} on branch '{event.branch_name}'"
        )

        try:
            for action in actions:
                success = await self._execute_single_action(
                    action, event, metadata
                )
                if not success:
                    self.logger.warning(
                        f"[{board_name}] Action '{action}' failed for event "
                        f"{event.event_type.value} on branch '{event.branch_name}'"
                    )

        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to execute actions for event "
                f"{event.event_type.value}: {e}",
                exc_info=True
            )

    async def _execute_single_action(self, action: str, event: GitEvent, metadata: dict) -> bool:
        """Execute a single action"""
        repo_path = event.repository_path
        branch_name = event.branch_name

        if action == "create_task":
            task = await self.task_manager.create_task(repo_path, branch_name, metadata)
            return task is not None

        elif action == "move_to_progress":
            return await self.task_manager.move_task_to_progress(repo_path, branch_name)

        elif action == "move_to_done":
            return await self.task_manager.move_task_to_done(repo_path, branch_name)

        elif action == "mark_deleted":
            return await self.task_manager.mark_task_deleted(repo_path, branch_name)

        elif action == "deactivate_previous_branch":
            previous_branch = metadata.get("previous_branch")
            if previous_branch:
                return await self.task_manager.deactivate_task(repo_path, previous_branch)
            return True

        elif action == "activate_current_branch":
            if metadata.get("should_activate_current", False):
                return await self.task_manager.activate_task(repo_path, branch_name)
            return True

        elif action == "initialize_repository_tasks":
            tasks = await self.task_manager.initialize_repository_tasks(repo_path)
            return len(tasks) >= 0  # Success even if no tasks created

        elif action == "cleanup_repository_tasks":
            # For now, we don't actively clean up tasks when repository is removed
            # They'll remain in the board for historical reference
            return True

        else:
            self.logger.warning(f"Unknown action: {action}")
            return False

    async def _process_jira_linking(self, events: List[GitEvent]) -> None:
        """Process Jira branch-ticket linking for git events"""
        try:
            from daemon.jira.branch_ticket_linker import BranchTicketLinker
            from src.infrastructure.storage.markdown_storage_impl import MarkdownStorageImpl

            linker = BranchTicketLinker(self.config_service)
            storage = MarkdownStorageImpl(self.config_service.get_data_path())

            # Get both boards
            git_board_name = self.config_service.get_board_name()
            jira_board_name = self.config_service.get_jira_config().board_name

            git_board = storage.load_board_by_name(git_board_name)
            jira_board = storage.load_board_by_name(jira_board_name)

            if not git_board or not jira_board:
                self.logger.debug("Git or Jira board not available for linking")
                return

            for event in events:
                if event.event_type.value in ["branch_created", "branch_switched"]:
                    # Try to link branch to tickets
                    await linker.link_branch_to_tickets(
                        event.repository_path,
                        event.branch_name,
                        git_board,
                        jira_board,
                        storage
                    )

                if event.event_type.value == "branch_switched":
                    # Update linked item status
                    await linker.update_linked_items_status(
                        event.repository_path,
                        event.branch_name,
                        True,  # is_current_branch
                        storage
                    )

        except Exception as e:
            self.logger.error(f"Error processing Jira linking: {e}")

    async def handle_session_change(self, old_context: SessionContext, new_context: SessionContext) -> None:
        """Handle session context change"""
        self.logger.info(
            f"SyncCoordinator handling session change: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )

        # Update configuration for new session
        config_changed = self.config_service.update_session_context(new_context.session_name)

        if config_changed:
            # Reinitialize TaskManager for new session
            await self.task_manager.reinitialize_for_session(new_context.session_name)
            self.logger.info(f"SyncCoordinator reinitialized for session: {new_context.session_name}")
        else:
            self.logger.debug("No configuration change needed for session")

    async def handle_session_switch(self, old_context: SessionContext, new_context: SessionContext) -> None:
        """Handle tmux session switch with task status management"""
        board_name = self.config_service.get_board_name()

        self.logger.info(
            f"[{board_name}] Handling tmux session switch: "
            f"'{old_context.session_name}' -> '{new_context.session_name}'"
        )

        try:
            # Use the session task coordinator to handle the session switch
            await self.session_task_coordinator.handle_session_switch(old_context, new_context)

            self.logger.info(
                f"[{board_name}] Successfully handled session switch to {new_context.session_name}"
            )
        except Exception as e:
            self.logger.error(
                f"[{board_name}] Failed to handle session switch: {e}",
                exc_info=True
            )

    def get_current_board_name(self) -> str:
        """Get the current board name being managed"""
        return self.config_service.get_board_name()

    async def force_sync_repository(self, repository_path) -> int:
        """Force synchronization of a specific repository"""
        board_name = self.config_service.get_board_name()
        self.logger.info(f"[{board_name}] Force syncing repository: {repository_path}")

        try:
            tasks = await self.task_manager.initialize_repository_tasks(repository_path)
            self.logger.info(f"[{board_name}] Force sync created/updated {len(tasks)} tasks")
            return len(tasks)
        except Exception as e:
            self.logger.error(f"[{board_name}] Force sync failed: {e}")
            return 0