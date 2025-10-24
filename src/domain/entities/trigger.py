from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    """Types of triggers that can activate an action"""
    TIME = "time"
    BOARD_SWITCH = "board_switch"
    TASK_SWITCH = "task_switch"
    TASK_STATE_CHANGE = "task_state_change"
    GIT_EVENT = "git_event"
    JIRA_EVENT = "jira_event"
    INACTIVITY = "inactivity"


class ScheduleType(str, Enum):
    """Types of time-based schedules"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class TimeSchedule(BaseModel):
    """Configuration for time-based triggers"""
    type: ScheduleType = Field(description="Type of schedule")
    datetime: Optional[str] = Field(
        default=None,
        description="ISO datetime for ONCE type"
    )
    time: Optional[str] = Field(
        default=None,
        description="Time in HH:MM format for recurring schedules"
    )
    days_of_week: Optional[List[int]] = Field(
        default=None,
        description="Days of week (1=Monday, 7=Sunday) for weekly schedules"
    )
    day_of_month: Optional[int] = Field(
        default=None,
        description="Day of month (1-31) for monthly schedules"
    )
    cron_expression: Optional[str] = Field(
        default=None,
        description="Cron expression for complex schedules"
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for time-based triggers"
    )


class BoardSwitchEvent(str, Enum):
    """Events related to board switching"""
    ENTER = "enter"
    EXIT = "exit"


class TaskStateChangeEvent(str, Enum):
    """Events related to task state changes"""
    MOVED = "moved"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"


class GitEvent(str, Enum):
    """Git-related events"""
    BRANCH_CREATED = "branch_created"
    BRANCH_DELETED = "branch_deleted"
    BRANCH_MERGED = "branch_merged"
    BRANCH_SWITCHED = "branch_switched"
    COMMIT_MADE = "commit_made"


class JiraEvent(str, Enum):
    """JIRA-related events"""
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    COMMENTED = "commented"
    UPDATED = "updated"


class Trigger(BaseModel):
    """Defines a trigger condition for an action"""
    type: TriggerType = Field(description="The type of trigger")

    # Time-based trigger config
    schedule: Optional[TimeSchedule] = Field(
        default=None,
        description="Schedule configuration for TIME triggers"
    )

    # Board switch trigger config
    event: Optional[str] = Field(
        default=None,
        description="Event type for BOARD_SWITCH, TASK_STATE_CHANGE, etc."
    )
    board_id: Optional[str] = Field(
        default=None,
        description="Board ID for board-specific triggers"
    )

    # Task state change trigger config
    events: Optional[List[str]] = Field(
        default=None,
        description="List of events for multi-event triggers (GIT_EVENT, JIRA_EVENT)"
    )

    # Inactivity trigger config
    check_interval: Optional[int] = Field(
        default=None,
        description="Interval in seconds to check for inactivity"
    )
    inactive_duration: Optional[int] = Field(
        default=None,
        description="Duration in seconds of inactivity before triggering"
    )

    # Operator for combining with other triggers
    operator: str = Field(
        default="or",
        description="Logic operator when multiple triggers exist (and/or)"
    )

    # Additional custom data
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional trigger-specific data"
    )

    def is_time_based(self) -> bool:
        """Check if this is a time-based trigger"""
        return self.type == TriggerType.TIME

    def is_event_based(self) -> bool:
        """Check if this is an event-based trigger"""
        return self.type in [
            TriggerType.BOARD_SWITCH,
            TriggerType.TASK_SWITCH,
            TriggerType.TASK_STATE_CHANGE,
            TriggerType.GIT_EVENT,
            TriggerType.JIRA_EVENT
        ]

    def is_inactivity_based(self) -> bool:
        """Check if this is an inactivity-based trigger"""
        return self.type == TriggerType.INACTIVITY
