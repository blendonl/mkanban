from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.action import Action
from src.domain.entities.action_scope import ScopeType


class ActionRepository(ABC):
    """Repository interface for managing Action entities"""

    @abstractmethod
    def save(self, action: Action) -> bool:
        """
        Save an action to storage.

        Args:
            action: The Action entity to save

        Returns:
            True if save was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_by_id(self, action_id: str) -> Optional[Action]:
        """
        Retrieve an action by its ID.

        Args:
            action_id: The unique identifier of the action

        Returns:
            The Action if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Action]:
        """
        Retrieve all actions from storage.

        Returns:
            List of all Action entities
        """
        pass

    @abstractmethod
    def get_by_scope(
        self,
        scope_type: ScopeType,
        target_id: Optional[str] = None
    ) -> List[Action]:
        """
        Retrieve actions filtered by scope.

        Args:
            scope_type: The type of scope (GLOBAL, BOARD, TASK)
            target_id: The target ID for board or task scopes

        Returns:
            List of Action entities matching the scope
        """
        pass

    @abstractmethod
    def get_by_type(self, action_type: str) -> List[Action]:
        """
        Retrieve actions filtered by type.

        Args:
            action_type: The type of action (reminder, automation, etc.)

        Returns:
            List of Action entities of the specified type
        """
        pass

    @abstractmethod
    def get_enabled(self) -> List[Action]:
        """
        Retrieve all enabled actions.

        Returns:
            List of enabled Action entities
        """
        pass

    @abstractmethod
    def delete(self, action_id: str) -> bool:
        """
        Delete an action from storage.

        Args:
            action_id: The unique identifier of the action to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def disable(self, action_id: str) -> bool:
        """
        Disable an action without deleting it.

        Args:
            action_id: The unique identifier of the action to disable

        Returns:
            True if action was disabled successfully, False otherwise
        """
        pass

    @abstractmethod
    def enable(self, action_id: str) -> bool:
        """
        Enable a previously disabled action.

        Args:
            action_id: The unique identifier of the action to enable

        Returns:
            True if action was enabled successfully, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, action_id: str) -> bool:
        """
        Check if an action exists in storage.

        Args:
            action_id: The unique identifier of the action

        Returns:
            True if action exists, False otherwise
        """
        pass

    @abstractmethod
    def find_orphaned(self) -> List[Action]:
        """
        Find actions that reference non-existent boards or tasks.

        Returns:
            List of orphaned Action entities
        """
        pass

    @abstractmethod
    def update_execution_history(self, action: Action) -> bool:
        """
        Update only the execution history of an action.

        Args:
            action: The Action with updated execution history

        Returns:
            True if update was successful, False otherwise
        """
        pass
