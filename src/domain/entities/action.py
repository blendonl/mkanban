from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from src.utils.date_utils import now
from src.core.types import Timestamp
from .action_scope import ActionScope, ScopeType
from .trigger import Trigger
from .condition import Condition
from .action_executor import ActionExecutor


class ActionType(str, Enum):
    """Types of actions in the system"""
    REMINDER = "reminder"
    AUTOMATION = "automation"
    WATCHER = "watcher"
    HOOK = "hook"
    SCHEDULED_JOB = "scheduled_job"


class RecurrenceConfig(BaseModel):
    """Configuration for recurring actions"""
    enabled: bool = Field(default=True, description="Whether recurrence is enabled")
    max_occurrences: Optional[int] = Field(
        default=None,
        description="Maximum number of times to execute. None for unlimited"
    )
    end_date: Optional[Timestamp] = Field(
        default=None,
        description="End date for recurrence"
    )


class SnoozeConfig(BaseModel):
    """Configuration for snoozing actions"""
    enabled: bool = Field(default=True, description="Whether snoozing is enabled")
    count: int = Field(default=0, description="Number of times snoozed")
    until: Optional[Timestamp] = Field(
        default=None,
        description="Snoozed until this timestamp"
    )
    options: List[str] = Field(
        default_factory=lambda: ["10m", "1h", "tomorrow", "next_week"],
        description="Available snooze duration options"
    )

    def is_snoozed(self) -> bool:
        """Check if action is currently snoozed"""
        if not self.enabled or not self.until:
            return False
        from datetime import datetime
        snoozed_until = datetime.fromisoformat(self.until) if isinstance(self.until, str) else self.until
        return snoozed_until > datetime.now()


class ExecutionHistory(BaseModel):
    """Tracks action execution history"""
    last_triggered: Optional[Timestamp] = Field(
        default=None,
        description="Last time the action was triggered"
    )
    last_success: Optional[Timestamp] = Field(
        default=None,
        description="Last successful execution"
    )
    last_failure: Optional[Timestamp] = Field(
        default=None,
        description="Last failed execution"
    )
    last_error: Optional[str] = Field(
        default=None,
        description="Last error message"
    )
    total_executions: int = Field(
        default=0,
        description="Total number of executions"
    )
    successful_executions: int = Field(
        default=0,
        description="Number of successful executions"
    )
    consecutive_failures: int = Field(
        default=0,
        description="Number of consecutive failures"
    )

    def record_success(self) -> None:
        """Record a successful execution"""
        timestamp = now()
        self.last_triggered = timestamp
        self.last_success = timestamp
        self.total_executions += 1
        self.successful_executions += 1
        self.consecutive_failures = 0

    def record_failure(self, error: str) -> None:
        """Record a failed execution"""
        timestamp = now()
        self.last_triggered = timestamp
        self.last_failure = timestamp
        self.last_error = error
        self.total_executions += 1
        self.consecutive_failures += 1


class ActionMetadata(BaseModel):
    """Metadata for action configuration"""
    priority: int = Field(
        default=1,
        description="Execution priority (higher = executed first)"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts on failure"
    )
    retry_delay: int = Field(
        default=300,
        description="Delay in seconds between retry attempts"
    )
    timeout: int = Field(
        default=30,
        description="Timeout in seconds for action execution"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for organizing actions"
    )
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata fields"
    )


class Action(BaseModel):
    """Main Action entity representing an action/reminder in the system"""
    id: str = Field(description="Unique identifier for the action")
    type: ActionType = Field(description="Type of action")
    name: str = Field(description="Human-readable name for the action")
    description: str = Field(default="", description="Detailed description of the action")
    enabled: bool = Field(default=True, description="Whether the action is enabled")

    created_at: Timestamp = Field(default_factory=now)
    modified_at: Timestamp = Field(default_factory=now)

    scope: ActionScope = Field(description="Scope of the action")
    triggers: List[Trigger] = Field(
        default_factory=list,
        description="Triggers that activate this action"
    )
    conditions: List[Condition] = Field(
        default_factory=list,
        description="Conditions that must be met for execution"
    )
    actions: List[ActionExecutor] = Field(
        default_factory=list,
        description="Actions to execute when triggered"
    )

    recurrence: Optional[RecurrenceConfig] = Field(
        default=None,
        description="Recurrence configuration"
    )
    snooze: Optional[SnoozeConfig] = Field(
        default=None,
        description="Snooze configuration"
    )

    execution: ExecutionHistory = Field(
        default_factory=ExecutionHistory,
        description="Execution history"
    )
    metadata: ActionMetadata = Field(
        default_factory=ActionMetadata,
        description="Action metadata"
    )

    # Action chaining
    on_success: List[str] = Field(
        default_factory=list,
        description="Action IDs to trigger on success"
    )
    on_failure: List[str] = Field(
        default_factory=list,
        description="Action IDs to trigger on failure"
    )

    def is_enabled(self) -> bool:
        """Check if action is enabled"""
        return self.enabled

    def is_snoozed(self) -> bool:
        """Check if action is currently snoozed"""
        return self.snooze is not None and self.snooze.is_snoozed()

    def can_execute(self) -> bool:
        """Check if action can be executed"""
        if not self.enabled:
            return False
        if self.is_snoozed():
            return False
        if self.metadata.max_retries > 0 and self.execution.consecutive_failures >= self.metadata.max_retries:
            return False
        return True

    def has_time_triggers(self) -> bool:
        """Check if action has any time-based triggers"""
        return any(trigger.is_time_based() for trigger in self.triggers)

    def has_event_triggers(self) -> bool:
        """Check if action has any event-based triggers"""
        return any(trigger.is_event_based() for trigger in self.triggers)

    def is_global(self) -> bool:
        """Check if this is a global action"""
        return self.scope.is_global()

    def is_board_scoped(self) -> bool:
        """Check if this is a board-scoped action"""
        return self.scope.is_board_scoped()

    def is_task_scoped(self) -> bool:
        """Check if this is a task-scoped action"""
        return self.scope.is_task_scoped()

    def snooze_until(self, until: Timestamp) -> None:
        """Snooze the action until the specified timestamp"""
        if self.snooze is None:
            self.snooze = SnoozeConfig()
        self.snooze.until = until
        self.snooze.count += 1
        self.modified_at = now()

    def clear_snooze(self) -> None:
        """Clear the snooze on this action"""
        if self.snooze:
            self.snooze.until = None
        self.modified_at = now()

    def record_execution(self, success: bool, error: Optional[str] = None) -> None:
        """Record an execution result"""
        if success:
            self.execution.record_success()
        else:
            self.execution.record_failure(error or "Unknown error")
        self.modified_at = now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "scope": {
                "type": self.scope.type.value,
                "target_id": self.scope.target_id
            },
            "triggers": [trigger.model_dump(mode='python') for trigger in self.triggers],
            "conditions": [condition.model_dump(mode='python') for condition in self.conditions],
            "actions": [action.model_dump(mode='python') for action in self.actions],
            "recurrence": self.recurrence.model_dump(mode='python') if self.recurrence else None,
            "snooze": self.snooze.model_dump(mode='python') if self.snooze else None,
            "execution": self.execution.model_dump(mode='python'),
            "metadata": self.metadata.model_dump(mode='python'),
            "on_success": self.on_success,
            "on_failure": self.on_failure
        }
