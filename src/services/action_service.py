from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from src.domain.entities.action import Action, ActionType
from src.domain.entities.action_scope import ActionScope, ScopeType
from src.domain.repositories.action_repository import ActionRepository
from src.domain.repositories.board_repository import BoardRepository
from src.utils.logger_factory import LoggerFactory
from src.utils.date_utils import now
from src.utils.string_utils import generate_id_from_name


class ActionService:
    """Service for managing actions - CRUD operations, validation, and business logic"""

    def __init__(
        self,
        action_repository: ActionRepository,
        board_repository: Optional[BoardRepository] = None,
        logger: Optional[Any] = None
    ):
        """
        Initialize the ActionService.

        Args:
            action_repository: Repository for action storage
            board_repository: Optional board repository for orphan detection
            logger: Logger instance (injected via dependency injection)
        """
        self.action_repository = action_repository
        self.board_repository = board_repository
        self.logger = logger

    def create_action(
        self,
        action_type: ActionType,
        name: str,
        scope: ActionScope,
        **kwargs
    ) -> Optional[Action]:
        """
        Create a new action.

        Args:
            action_type: Type of action to create
            name: Name of the action
            scope: Scope of the action
            **kwargs: Additional action parameters

        Returns:
            The created Action or None if creation failed
        """
        try:
            # Generate action ID
            action_id = self._generate_action_id(name, action_type, scope)

            # Check if action with this ID already exists
            if self.action_repository.exists(action_id):
                self.logger.error(f"Action with ID {action_id} already exists")
                return None

            # Create action entity
            action = Action(
                id=action_id,
                type=action_type,
                name=name,
                description=kwargs.get("description", ""),
                enabled=kwargs.get("enabled", True),
                scope=scope,
                triggers=kwargs.get("triggers", []),
                conditions=kwargs.get("conditions", []),
                actions=kwargs.get("actions", []),
                recurrence=kwargs.get("recurrence"),
                snooze=kwargs.get("snooze"),
                metadata=kwargs.get("metadata", {}),
                on_success=kwargs.get("on_success", []),
                on_failure=kwargs.get("on_failure", [])
            )

            # Validate action
            if not self._validate_action(action):
                self.logger.error(f"Action validation failed for {action_id}")
                return None

            # Save action
            if self.action_repository.save(action):
                self.logger.info(f"Created action {action_id}")
                return action
            else:
                self.logger.error(f"Failed to save action {action_id}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to create action: {e}", exc_info=True)
            return None

    def get_action(self, action_id: str) -> Optional[Action]:
        """Get an action by ID"""
        return self.action_repository.get_by_id(action_id)

    def get_all_actions(self) -> List[Action]:
        """Get all actions"""
        return self.action_repository.get_all()

    def get_enabled_actions(self) -> List[Action]:
        """Get all enabled actions"""
        return self.action_repository.get_enabled()

    def get_actions_by_scope(
        self,
        scope_type: ScopeType,
        target_id: Optional[str] = None
    ) -> List[Action]:
        """Get actions by scope"""
        return self.action_repository.get_by_scope(scope_type, target_id)

    def get_actions_by_type(self, action_type: ActionType) -> List[Action]:
        """Get actions by type"""
        return self.action_repository.get_by_type(action_type.value)

    def update_action(self, action: Action) -> bool:
        """
        Update an existing action.

        Args:
            action: The action with updated data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Validate action
            if not self._validate_action(action):
                self.logger.error(f"Action validation failed for {action.id}")
                return False

            # Update modified timestamp
            action.modified_at = now()

            # Save action
            if self.action_repository.save(action):
                self.logger.info(f"Updated action {action.id}")
                return True
            else:
                self.logger.error(f"Failed to update action {action.id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to update action: {e}", exc_info=True)
            return False

    def delete_action(self, action_id: str) -> bool:
        """Delete an action"""
        if self.action_repository.delete(action_id):
            self.logger.info(f"Deleted action {action_id}")
            return True
        return False

    def enable_action(self, action_id: str) -> bool:
        """Enable an action"""
        if self.action_repository.enable(action_id):
            self.logger.info(f"Enabled action {action_id}")
            return True
        return False

    def disable_action(self, action_id: str) -> bool:
        """Disable an action"""
        if self.action_repository.disable(action_id):
            self.logger.info(f"Disabled action {action_id}")
            return True
        return False

    def snooze_action(self, action_id: str, duration: str) -> bool:
        """
        Snooze an action for a specified duration.

        Args:
            action_id: ID of the action to snooze
            duration: Duration string (e.g., "10m", "1h", "tomorrow")

        Returns:
            True if snooze was successful, False otherwise
        """
        try:
            action = self.get_action(action_id)
            if not action:
                self.logger.error(f"Action {action_id} not found")
                return False

            # Calculate snooze timestamp
            snooze_until = self._parse_duration(duration)
            if not snooze_until:
                self.logger.error(f"Invalid duration: {duration}")
                return False

            # Snooze action
            action.snooze_until(snooze_until)

            # Save action
            if self.action_repository.save(action):
                self.logger.info(f"Snoozed action {action_id} until {snooze_until}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to snooze action: {e}", exc_info=True)
            return False

    def clear_snooze(self, action_id: str) -> bool:
        """Clear snooze on an action"""
        try:
            action = self.get_action(action_id)
            if not action:
                return False

            action.clear_snooze()

            if self.action_repository.save(action):
                self.logger.info(f"Cleared snooze on action {action_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to clear snooze: {e}", exc_info=True)
            return False

    def record_execution(
        self,
        action_id: str,
        success: bool,
        error: Optional[str] = None
    ) -> bool:
        """Record an action execution"""
        try:
            action = self.get_action(action_id)
            if not action:
                return False

            action.record_execution(success, error)

            return self.action_repository.update_execution_history(action)

        except Exception as e:
            self.logger.error(f"Failed to record execution: {e}", exc_info=True)
            return False

    def find_orphaned_actions(self) -> List[Action]:
        """
        Find actions that reference non-existent boards or tasks.

        Returns:
            List of orphaned actions
        """
        if not self.board_repository:
            self.logger.warning("BoardRepository not available for orphan detection")
            return []

        orphaned = []

        all_actions = self.get_all_actions()
        all_boards = self.board_repository.load_all_boards()

        for action in all_actions:
            if action.scope.is_board_scoped():
                # Check if board exists
                board_exists = any(
                    board.id == action.scope.target_id
                    for board in all_boards
                )
                if not board_exists:
                    orphaned.append(action)

            elif action.scope.is_task_scoped():
                # Check if task exists in any board
                task_exists = False
                for board in all_boards:
                    for column in board.columns:
                        if any(item.id == action.scope.target_id for item in column.items):
                            task_exists = True
                            break
                    if task_exists:
                        break

                if not task_exists:
                    orphaned.append(action)

        return orphaned

    def cleanup_orphaned_actions(self, auto_disable: bool = True) -> int:
        """
        Clean up orphaned actions.

        Args:
            auto_disable: If True, disable orphaned actions. If False, delete them.

        Returns:
            Number of actions cleaned up
        """
        orphaned = self.find_orphaned_actions()
        count = 0

        for action in orphaned:
            if auto_disable:
                if self.disable_action(action.id):
                    count += 1
            else:
                if self.delete_action(action.id):
                    count += 1

        self.logger.info(f"Cleaned up {count} orphaned actions")
        return count

    def _generate_action_id(
        self,
        name: str,
        action_type: ActionType,
        scope: ActionScope
    ) -> str:
        """Generate a unique action ID"""
        # Create base ID from name
        base_id = generate_id_from_name(name)

        # Add type prefix
        type_prefix = action_type.value[:3]  # e.g., "rem" for reminder

        # Add timestamp suffix for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        return f"action-{type_prefix}-{base_id}-{timestamp}"

    def _validate_action(self, action: Action) -> bool:
        """Validate an action configuration"""
        # Check required fields
        if not action.id or not action.name:
            self.logger.error("Action must have ID and name")
            return False

        # Check that action has at least one trigger
        if not action.triggers:
            self.logger.error("Action must have at least one trigger")
            return False

        # Check that action has at least one executor
        if not action.actions:
            self.logger.error("Action must have at least one action executor")
            return False

        # Validate scope target_id
        if action.scope.is_board_scoped() or action.scope.is_task_scoped():
            if not action.scope.target_id:
                self.logger.error("Board/task scoped actions must have target_id")
                return False

        return True

    def _parse_duration(self, duration: str) -> Optional[str]:
        """
        Parse a duration string into an ISO timestamp.

        Args:
            duration: Duration string (e.g., "10m", "1h", "tomorrow", "next_week")

        Returns:
            ISO timestamp string or None if parsing failed
        """
        try:
            now_dt = datetime.now()

            if duration.endswith('m'):
                # Minutes
                minutes = int(duration[:-1])
                target_dt = now_dt + timedelta(minutes=minutes)
            elif duration.endswith('h'):
                # Hours
                hours = int(duration[:-1])
                target_dt = now_dt + timedelta(hours=hours)
            elif duration.endswith('d'):
                # Days
                days = int(duration[:-1])
                target_dt = now_dt + timedelta(days=days)
            elif duration == 'tomorrow':
                target_dt = now_dt + timedelta(days=1)
                target_dt = target_dt.replace(hour=9, minute=0, second=0, microsecond=0)
            elif duration == 'next_week':
                target_dt = now_dt + timedelta(weeks=1)
                target_dt = target_dt.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                return None

            return target_dt.isoformat()

        except Exception as e:
            self.logger.error(f"Failed to parse duration {duration}: {e}")
            return None
