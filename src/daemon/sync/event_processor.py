"""Event Processor

Handles processing of git events and determines appropriate actions
for kanban task synchronization.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.daemon.git_monitor import GitEvent, GitEventType
from src.daemon.core.configuration_service import ConfigurationService
from src.infrastructure.git.repository import GitOperations


@dataclass
class ProcessedEvent:
    """Represents a processed git event with determined actions"""

    original_event: GitEvent
    actions: List[str]  # List of actions to take (e.g., ["create_task", "move_to_progress"])
    metadata: Dict[str, Any]

    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}


class EventProcessor:
    """Processes git events and determines synchronization actions"""

    def __init__(self, config_service: ConfigurationService):
        self.config_service = config_service
        self.logger = logging.getLogger("mkanban-daemon")

    async def process_events(self, events: List[GitEvent]) -> List[ProcessedEvent]:
        """Process a list of git events and return processed events with actions"""
        processed_events = []

        for event in events:
            try:
                processed_event = await self._process_single_event(event)
                if processed_event:
                    processed_events.append(processed_event)
            except Exception as e:
                self.logger.error(
                    f"Failed to process git event {event.event_type.value}: {e}",
                    exc_info=True
                )

        return processed_events

    async def _process_single_event(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process a single git event"""
        board_name = self.config_service.get_board_name()

        self.logger.debug(
            f"[{board_name}] Processing event: {event.event_type.value} "
            f"for branch '{event.branch_name}' in {event.repository_path.name}"
        )

        if event.event_type == GitEventType.BRANCH_CREATED:
            return await self._process_branch_created(event)
        elif event.event_type == GitEventType.BRANCH_DELETED:
            return await self._process_branch_deleted(event)
        elif event.event_type == GitEventType.BRANCH_SWITCHED:
            return await self._process_branch_switched(event)
        elif event.event_type == GitEventType.REPOSITORY_ADDED:
            return await self._process_repository_added(event)
        elif event.event_type == GitEventType.REPOSITORY_REMOVED:
            return await self._process_repository_removed(event)

        return None

    async def _process_branch_created(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process branch creation event"""
        if not self._should_track_branch(event.branch_name):
            self.logger.debug(f"Skipping branch {event.branch_name} (filtered out)")
            return None

        # Get branch information
        try:
            git_ops = GitOperations(event.repository_path)
            branch_info = git_ops.get_branch_info(event.branch_name)

            if not branch_info:
                self.logger.warning(
                    f"Could not get info for branch {event.branch_name}"
                )
                return None

            actions = ["create_task"]
            metadata = {
                "repository_name": event.repository_path.name,
                "branch_info": branch_info,
                "should_auto_activate": branch_info.is_current,
            }

            # If this is the current branch, it should go to in-progress
            if branch_info.is_current:
                actions.append("move_to_progress")

            return ProcessedEvent(
                original_event=event,
                actions=actions,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Error getting branch info for {event.branch_name}: {e}")
            return None

    async def _process_branch_deleted(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process branch deletion event"""
        return ProcessedEvent(
            original_event=event,
            actions=["mark_deleted", "move_to_done"],
            metadata={"repository_name": event.repository_path.name}
        )

    async def _process_branch_switched(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process branch switch event"""
        board_name = self.config_service.get_board_name()
        repo_name = event.repository_path.name

        self.logger.info(
            f"[{board_name}] Processing branch switch in {repo_name}: "
            f"{event.previous_branch} -> {event.branch_name}"
        )

        actions = []
        metadata = {
            "repository_name": repo_name,
            "previous_branch": event.previous_branch,
            "current_branch": event.branch_name,
        }

        # Handle previous branch (if exists)
        if event.previous_branch:
            actions.append("deactivate_previous_branch")
            metadata["should_complete_previous"] = True

        # Handle current branch (if trackable)
        if event.branch_name and self._should_track_branch(event.branch_name):
            actions.append("activate_current_branch")
            metadata["should_activate_current"] = True
        else:
            metadata["should_activate_current"] = False

        return ProcessedEvent(
            original_event=event,
            actions=actions,
            metadata=metadata
        )

    async def _process_repository_added(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process repository addition event"""
        return ProcessedEvent(
            original_event=event,
            actions=["initialize_repository_tasks"],
            metadata={"repository_name": event.repository_path.name}
        )

    async def _process_repository_removed(self, event: GitEvent) -> Optional[ProcessedEvent]:
        """Process repository removal event"""
        return ProcessedEvent(
            original_event=event,
            actions=["cleanup_repository_tasks"],
            metadata={"repository_name": event.repository_path.name}
        )

    def _should_track_branch(self, branch_name: str) -> bool:
        """Check if a branch should be tracked based on configuration"""
        return self.config_service.should_track_branch(branch_name)