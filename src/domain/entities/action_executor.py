from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ActionExecutorType(str, Enum):
    """Types of actions that can be executed"""
    NOTIFY = "notify"
    MOVE_TASK = "move_task"
    CREATE_TASK = "create_task"
    MARK_COMPLETE = "mark_complete"
    CREATE_BRANCH = "create_branch"
    JIRA_UPDATE = "jira_update"
    RUN_COMMAND = "run_command"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Platform(str, Enum):
    """Platforms where actions can be executed"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    BOTH = "both"


class NotificationChannel(str, Enum):
    """Channels for sending notifications"""
    SYSTEM = "system"
    MOBILE_PUSH = "mobile_push"
    EMAIL = "email"


class ActionExecutor(BaseModel):
    """Defines an action to be executed"""
    type: ActionExecutorType = Field(description="The type of action to execute")

    # Notification action config
    message: Optional[str] = Field(
        default=None,
        description="Message for NOTIFY action. Supports variables like {task_title}, {board_name}"
    )
    title: Optional[str] = Field(
        default=None,
        description="Title for NOTIFY action"
    )
    platforms: List[str] = Field(
        default_factory=lambda: ["desktop"],
        description="Platforms to send notification to"
    )
    channels: List[str] = Field(
        default_factory=lambda: ["system"],
        description="Channels to use for notification"
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        description="Priority level for notification"
    )

    # Move task action config
    target_column: Optional[str] = Field(
        default=None,
        description="Target column ID for MOVE_TASK action"
    )

    # Create task action config
    task_title: Optional[str] = Field(
        default=None,
        description="Title for CREATE_TASK action"
    )
    task_description: Optional[str] = Field(
        default=None,
        description="Description for CREATE_TASK action"
    )
    task_column: Optional[str] = Field(
        default=None,
        description="Column ID for CREATE_TASK action"
    )
    board_id: Optional[str] = Field(
        default=None,
        description="Board ID for CREATE_TASK action"
    )

    # Create branch action config
    branch_name: Optional[str] = Field(
        default=None,
        description="Branch name for CREATE_BRANCH action"
    )

    # JIRA update action config
    field: Optional[str] = Field(
        default=None,
        description="Field name for JIRA_UPDATE action (status, assignee, etc.)"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Value for JIRA_UPDATE action"
    )
    value_from: Optional[str] = Field(
        default=None,
        description="Source for value (e.g., 'column_name_mapping')"
    )

    # Run command action config
    command: Optional[str] = Field(
        default=None,
        description="Shell command for RUN_COMMAND action"
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="Working directory for RUN_COMMAND action"
    )
    environment: Optional[Dict[str, str]] = Field(
        default=None,
        description="Environment variables for RUN_COMMAND action"
    )

    # Additional custom data
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional action-specific data"
    )

    def is_notification(self) -> bool:
        """Check if this is a notification action"""
        return self.type == ActionExecutorType.NOTIFY

    def is_task_action(self) -> bool:
        """Check if this is a task-related action"""
        return self.type in [
            ActionExecutorType.MOVE_TASK,
            ActionExecutorType.CREATE_TASK,
            ActionExecutorType.MARK_COMPLETE
        ]

    def is_git_action(self) -> bool:
        """Check if this is a git-related action"""
        return self.type == ActionExecutorType.CREATE_BRANCH

    def is_jira_action(self) -> bool:
        """Check if this is a JIRA-related action"""
        return self.type == ActionExecutorType.JIRA_UPDATE

    def is_command_action(self) -> bool:
        """Check if this is a command execution action"""
        return self.type == ActionExecutorType.RUN_COMMAND

    def supports_platform(self, platform: str) -> bool:
        """Check if this action supports the given platform"""
        return "both" in self.platforms or platform in self.platforms
