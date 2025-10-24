import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum
from src.domain.entities.action import Action, ActionType
from src.domain.entities.action_scope import ActionScope, ScopeType
from src.domain.entities.trigger import Trigger
from src.domain.entities.condition import Condition
from src.domain.entities.action_executor import ActionExecutor
from src.domain.repositories.action_repository import ActionRepository
from src.utils.file_utils import ensure_directory_exists
from src.utils.logger_factory import LoggerFactory


def _serialize_value(obj: Any) -> Any:
    """Recursively serialize objects, converting Enums to their values"""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_value(item) for item in obj]
    else:
        return obj


class YamlActionRepository(ActionRepository):
    """YAML-based implementation of ActionRepository"""

    def __init__(self, actions_dir: Path, logger: Optional[Any] = None):
        """
        Initialize the YAML action repository.

        Args:
            actions_dir: Base directory for storing actions (~/.mkanban/actions/)
            logger: Logger instance (injected via dependency injection)
        """
        self.actions_dir = Path(actions_dir)
        ensure_directory_exists(self.actions_dir)

        # Create subdirectories for organization
        self.global_dir = self.actions_dir / "global"
        self.boards_dir = self.actions_dir / "boards"
        self.tasks_dir = self.actions_dir / "tasks"

        for directory in [self.global_dir, self.boards_dir, self.tasks_dir]:
            ensure_directory_exists(directory)

        self.logger = logger

    def _get_action_file_path(self, action: Action) -> Path:
        """
        Determine the file path for an action based on its scope and type.

        Args:
            action: The Action entity

        Returns:
            Path where the action file should be stored
        """
        # Determine scope directory
        if action.scope.is_global():
            base_dir = self.global_dir
        elif action.scope.is_board_scoped():
            base_dir = self.boards_dir / action.scope.target_id
            ensure_directory_exists(base_dir)
        else:  # task scoped
            base_dir = self.tasks_dir / action.scope.target_id
            ensure_directory_exists(base_dir)

        # Determine type subdirectory
        type_dir_map = {
            ActionType.REMINDER: "reminders",
            ActionType.AUTOMATION: "automations",
            ActionType.WATCHER: "watchers",
            ActionType.HOOK: "hooks",
            ActionType.SCHEDULED_JOB: "scheduled_jobs"
        }

        type_dir = base_dir / type_dir_map.get(action.type, "other")
        ensure_directory_exists(type_dir)

        return type_dir / f"{action.id}.yaml"

    def _find_action_file(self, action_id: str) -> Optional[Path]:
        """
        Find an action file by ID searching all directories.

        Args:
            action_id: The action ID to find

        Returns:
            Path to the action file if found, None otherwise
        """
        # Search in all possible locations
        search_dirs = [self.global_dir, self.boards_dir, self.tasks_dir]

        for base_dir in search_dirs:
            for yaml_file in base_dir.rglob(f"{action_id}.yaml"):
                return yaml_file

        return None

    def _action_to_dict(self, action: Action) -> Dict[str, Any]:
        """Convert Action entity to dictionary for YAML serialization"""
        return action.to_dict()

    def _dict_to_action(self, data: Dict[str, Any]) -> Optional[Action]:
        """Convert dictionary to Action entity"""
        try:
            # Parse scope
            scope_data = data.get("scope", {})
            scope = ActionScope(
                type=ScopeType(scope_data.get("type", "global")),
                target_id=scope_data.get("target_id")
            )

            # Parse triggers
            triggers = [Trigger(**trigger_data) for trigger_data in data.get("triggers", [])]

            # Parse conditions
            conditions = [Condition(**cond_data) for cond_data in data.get("conditions", [])]

            # Parse action executors
            action_executors = [ActionExecutor(**exec_data) for exec_data in data.get("actions", [])]

            # Create Action entity
            action = Action(
                id=data.get("id"),
                type=ActionType(data.get("type")),
                name=data.get("name"),
                description=data.get("description", ""),
                enabled=data.get("enabled", True),
                created_at=data.get("created_at"),
                modified_at=data.get("modified_at"),
                scope=scope,
                triggers=triggers,
                conditions=conditions,
                actions=action_executors,
                recurrence=data.get("recurrence"),
                snooze=data.get("snooze"),
                execution=data.get("execution", {}),
                metadata=data.get("metadata", {}),
                on_success=data.get("on_success", []),
                on_failure=data.get("on_failure", [])
            )

            return action

        except Exception as e:
            self.logger.error(f"Failed to parse action from dict: {e}", exc_info=True)
            return None

    def save(self, action: Action) -> bool:
        """Save an action to a YAML file"""
        try:
            file_path = self._get_action_file_path(action)
            data = self._action_to_dict(action)

            # Serialize all enum values recursively
            serialized_data = _serialize_value(data)

            with open(file_path, 'w') as f:
                yaml.dump(serialized_data, f, default_flow_style=False, sort_keys=False)

            self.logger.info(f"Saved action {action.id} to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save action {action.id}: {e}", exc_info=True)
            return False

    def get_by_id(self, action_id: str) -> Optional[Action]:
        """Retrieve an action by its ID"""
        try:
            file_path = self._find_action_file(action_id)
            if not file_path or not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            return self._dict_to_action(data)

        except Exception as e:
            self.logger.error(f"Failed to load action {action_id}: {e}", exc_info=True)
            return None

    def get_all(self) -> List[Action]:
        """Retrieve all actions from storage"""
        actions = []

        # Search all YAML files in the actions directory
        for yaml_file in self.actions_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                action = self._dict_to_action(data)
                if action:
                    actions.append(action)

            except Exception as e:
                self.logger.error(f"Failed to load action from {yaml_file}: {e}")
                continue

        return actions

    def get_by_scope(
        self,
        scope_type: ScopeType,
        target_id: Optional[str] = None
    ) -> List[Action]:
        """Retrieve actions filtered by scope"""
        # Determine search directory based on scope
        if scope_type == ScopeType.GLOBAL:
            search_dir = self.global_dir
        elif scope_type == ScopeType.BOARD:
            if not target_id:
                search_dir = self.boards_dir
            else:
                search_dir = self.boards_dir / target_id
        else:  # TASK
            if not target_id:
                search_dir = self.tasks_dir
            else:
                search_dir = self.tasks_dir / target_id

        if not search_dir.exists():
            return []

        actions = []
        for yaml_file in search_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                action = self._dict_to_action(data)
                if action and action.scope.matches(scope_type, target_id):
                    actions.append(action)

            except Exception as e:
                self.logger.error(f"Failed to load action from {yaml_file}: {e}")
                continue

        return actions

    def get_by_type(self, action_type: str) -> List[Action]:
        """Retrieve actions filtered by type"""
        all_actions = self.get_all()
        return [action for action in all_actions if action.type == action_type]

    def get_enabled(self) -> List[Action]:
        """Retrieve all enabled actions"""
        all_actions = self.get_all()
        return [action for action in all_actions if action.is_enabled()]

    def delete(self, action_id: str) -> bool:
        """Delete an action from storage"""
        try:
            file_path = self._find_action_file(action_id)
            if not file_path or not file_path.exists():
                self.logger.warning(f"Action {action_id} not found for deletion")
                return False

            file_path.unlink()
            self.logger.info(f"Deleted action {action_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete action {action_id}: {e}", exc_info=True)
            return False

    def disable(self, action_id: str) -> bool:
        """Disable an action without deleting it"""
        action = self.get_by_id(action_id)
        if not action:
            return False

        action.enabled = False
        return self.save(action)

    def enable(self, action_id: str) -> bool:
        """Enable a previously disabled action"""
        action = self.get_by_id(action_id)
        if not action:
            return False

        action.enabled = True
        return self.save(action)

    def exists(self, action_id: str) -> bool:
        """Check if an action exists in storage"""
        file_path = self._find_action_file(action_id)
        return file_path is not None and file_path.exists()

    def find_orphaned(self) -> List[Action]:
        """
        Find actions that reference non-existent boards or tasks.

        Note: This implementation returns an empty list as it requires
        access to BoardRepository to check existence. Should be implemented
        in the ActionService layer with proper dependencies.
        """
        # This requires board/task existence checking
        # Should be implemented in service layer
        self.logger.warning("find_orphaned() should be implemented in service layer")
        return []

    def update_execution_history(self, action: Action) -> bool:
        """Update only the execution history of an action"""
        return self.save(action)
