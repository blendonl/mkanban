from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ScopeType(str, Enum):
    """Defines the scope level of an action"""
    GLOBAL = "global"
    BOARD = "board"
    TASK = "task"


class ActionScope(BaseModel):
    """Defines the scope of an action - global, board-specific, or task-specific"""
    type: ScopeType = Field(description="The scope type of the action")
    target_id: Optional[str] = Field(
        default=None,
        description="The target board ID or task ID. None for global scope"
    )

    def is_global(self) -> bool:
        """Check if this is a global scope"""
        return self.type == ScopeType.GLOBAL

    def is_board_scoped(self) -> bool:
        """Check if this is a board-specific scope"""
        return self.type == ScopeType.BOARD

    def is_task_scoped(self) -> bool:
        """Check if this is a task-specific scope"""
        return self.type == ScopeType.TASK

    def matches(self, scope_type: ScopeType, target_id: Optional[str] = None) -> bool:
        """Check if this scope matches the given parameters"""
        if self.type != scope_type:
            return False
        if scope_type == ScopeType.GLOBAL:
            return True
        return self.target_id == target_id
