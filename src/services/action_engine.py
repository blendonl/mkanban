from typing import List, Optional, Dict, Any
from datetime import datetime, time as datetime_time
import re
from croniter import croniter
from src.domain.entities.action import Action
from src.domain.entities.trigger import Trigger, TriggerType, ScheduleType
from src.domain.entities.condition import Condition, ConditionType, Operator
from src.domain.entities.action_executor import ActionExecutor, ActionExecutorType
from src.domain.entities.item import Item
from src.domain.entities.board import Board
from src.services.action_service import ActionService
from src.utils.logger_factory import LoggerFactory


class ActionEngine:
    """Engine for evaluating triggers, checking conditions, and executing actions"""

    def __init__(
        self,
        action_service: Any,
        notification_service: Optional[Any] = None,
        board_service: Optional[Any] = None,
        item_service: Optional[Any] = None,
        logger: Optional[Any] = None
    ):
        """
        Initialize the ActionEngine.

        Args:
            action_service: Service for managing actions
            notification_service: Service for sending notifications
            board_service: Service for board operations
            item_service: Service for item/task operations
            logger: Logger instance (injected via dependency injection)
        """
        self.action_service = action_service
        self.notification_service = notification_service
        self.board_service = board_service
        self.item_service = item_service
        self.logger = logger

    def evaluate_time_triggers(self) -> List[Action]:
        """
        Evaluate all time-based triggers and return actions that should execute.

        Returns:
            List of actions whose time triggers have fired
        """
        actions_to_execute = []
        enabled_actions = self.action_service.get_enabled_actions()

        for action in enabled_actions:
            if not action.can_execute():
                continue

            if action.has_time_triggers():
                if self._should_execute_time_trigger(action):
                    actions_to_execute.append(action)

        return actions_to_execute

    def evaluate_event_trigger(
        self,
        trigger_type: TriggerType,
        event_data: Dict[str, Any]
    ) -> List[Action]:
        """
        Evaluate event-based triggers and return actions that should execute.

        Args:
            trigger_type: The type of trigger event
            event_data: Data associated with the event

        Returns:
            List of actions whose triggers match the event
        """
        actions_to_execute = []
        enabled_actions = self.action_service.get_enabled_actions()

        for action in enabled_actions:
            if not action.can_execute():
                continue

            for trigger in action.triggers:
                if trigger.type == trigger_type:
                    if self._matches_event_trigger(trigger, event_data):
                        actions_to_execute.append(action)
                        break  # Don't add same action multiple times

        return actions_to_execute

    def execute_action(
        self,
        action: Action,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute an action if all conditions are met.

        Args:
            action: The action to execute
            context: Optional context data (task, board, etc.)

        Returns:
            True if execution was successful, False otherwise
        """
        try:
            # Check if action can execute
            if not action.can_execute():
                self.logger.info(f"Action {action.id} cannot execute (disabled or snoozed)")
                return False

            # Check conditions
            if not self._check_conditions(action, context):
                self.logger.info(f"Action {action.id} conditions not met")
                return False

            # Execute all action executors
            all_success = True
            for executor in action.actions:
                success = self._execute_action_executor(executor, context)
                if not success:
                    all_success = False

            # Record execution
            self.action_service.record_execution(
                action.id,
                all_success,
                None if all_success else "One or more executors failed"
            )

            # Execute chained actions
            if all_success and action.on_success:
                self._execute_chained_actions(action.on_success, context)
            elif not all_success and action.on_failure:
                self._execute_chained_actions(action.on_failure, context)

            return all_success

        except Exception as e:
            self.logger.error(f"Failed to execute action {action.id}: {e}", exc_info=True)
            self.action_service.record_execution(action.id, False, str(e))
            return False

    def _should_execute_time_trigger(self, action: Action) -> bool:
        """Check if any time-based trigger should fire now"""
        now = datetime.now()

        for trigger in action.triggers:
            if trigger.type != TriggerType.TIME or not trigger.schedule:
                continue

            schedule = trigger.schedule

            if schedule.type == ScheduleType.ONCE:
                # One-time trigger
                if schedule.datetime:
                    trigger_time = datetime.fromisoformat(schedule.datetime)
                    # Check if it's time (within 1 minute window)
                    if abs((trigger_time - now).total_seconds()) < 60:
                        return True

            elif schedule.type == ScheduleType.DAILY:
                # Daily recurring
                if schedule.time:
                    trigger_time = datetime.strptime(schedule.time, "%H:%M").time()
                    current_time = now.time()

                    # Check if current time matches (within 1 minute)
                    if self._times_match(current_time, trigger_time):
                        # Check day of week if specified
                        if schedule.days_of_week:
                            if now.isoweekday() not in schedule.days_of_week:
                                continue
                        return True

            elif schedule.type == ScheduleType.WEEKLY:
                # Weekly recurring
                if schedule.time and schedule.days_of_week:
                    trigger_time = datetime.strptime(schedule.time, "%H:%M").time()
                    current_time = now.time()

                    if now.isoweekday() in schedule.days_of_week:
                        if self._times_match(current_time, trigger_time):
                            return True

            elif schedule.type == ScheduleType.MONTHLY:
                # Monthly recurring
                if schedule.time and schedule.day_of_month:
                    if now.day == schedule.day_of_month:
                        trigger_time = datetime.strptime(schedule.time, "%H:%M").time()
                        current_time = now.time()
                        if self._times_match(current_time, trigger_time):
                            return True

            elif schedule.type == ScheduleType.CRON:
                # Cron expression
                if schedule.cron_expression:
                    try:
                        cron = croniter(schedule.cron_expression, now)
                        next_run = cron.get_next(datetime)
                        # Check if next run is within the next minute
                        if (next_run - now).total_seconds() < 60:
                            return True
                    except Exception as e:
                        self.logger.error(f"Invalid cron expression: {e}")

        return False

    def _matches_event_trigger(
        self,
        trigger: Trigger,
        event_data: Dict[str, Any]
    ) -> bool:
        """Check if a trigger matches the given event data"""
        if trigger.event:
            # Single event type
            if event_data.get("event") != trigger.event:
                return False

        if trigger.events:
            # Multiple event types
            if event_data.get("event") not in trigger.events:
                return False

        # Check board_id if specified
        if trigger.board_id:
            if event_data.get("board_id") != trigger.board_id:
                return False

        # Check additional trigger data
        for key, value in trigger.data.items():
            if event_data.get(key) != value:
                return False

        return True

    def _check_conditions(
        self,
        action: Action,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if all conditions are met for action execution"""
        if not action.conditions:
            return True  # No conditions means always execute

        context = context or {}
        now = datetime.now()

        for condition in action.conditions:
            if condition.type == ConditionType.TIME_RANGE:
                # Check if current time is within range
                if condition.start_time and condition.end_time:
                    start_time = datetime.strptime(condition.start_time, "%H:%M").time()
                    end_time = datetime.strptime(condition.end_time, "%H:%M").time()
                    current_time = now.time()

                    if not (start_time <= current_time <= end_time):
                        return False

            elif condition.type == ConditionType.DAY_OF_WEEK:
                # Check if today is in allowed days
                if condition.days:
                    if now.isoweekday() not in condition.days:
                        return False

            elif condition.type == ConditionType.TASK_IN_COLUMN:
                # Check if task is in specified columns
                task = context.get("task")
                if task and condition.column_ids:
                    if task.column_id not in condition.column_ids:
                        return False

            elif condition.type == ConditionType.TASK_PROPERTY:
                # Check task property
                task = context.get("task")
                if task and condition.field and condition.operator:
                    if not self._check_property_condition(
                        task,
                        condition.field,
                        condition.operator,
                        condition.value
                    ):
                        return False

            elif condition.type == ConditionType.BOARD_PROPERTY:
                # Check board property
                board = context.get("board")
                if board and condition.field and condition.operator:
                    if not self._check_property_condition(
                        board,
                        condition.field,
                        condition.operator,
                        condition.value
                    ):
                        return False

        return True

    def _check_property_condition(
        self,
        obj: Any,
        field: str,
        operator: Operator,
        value: Any
    ) -> bool:
        """Check a property condition against an object"""
        # Get field value
        if hasattr(obj, field):
            field_value = getattr(obj, field)
        else:
            return False

        # Apply operator
        if operator == Operator.EQUALS:
            return field_value == value
        elif operator == Operator.NOT_EQUALS:
            return field_value != value
        elif operator == Operator.GREATER_THAN:
            return field_value > value
        elif operator == Operator.LESS_THAN:
            return field_value < value
        elif operator == Operator.GREATER_THAN_OR_EQUAL:
            return field_value >= value
        elif operator == Operator.LESS_THAN_OR_EQUAL:
            return field_value <= value
        elif operator == Operator.CONTAINS:
            return value in field_value
        elif operator == Operator.NOT_CONTAINS:
            return value not in field_value
        elif operator == Operator.IN:
            return field_value in value
        elif operator == Operator.NOT_IN:
            return field_value not in value
        elif operator == Operator.MATCHES_REGEX:
            return re.match(value, str(field_value)) is not None

        return False

    def _execute_action_executor(
        self,
        executor: ActionExecutor,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Execute a single action executor"""
        context = context or {}

        try:
            if executor.type == ActionExecutorType.NOTIFY:
                return self._execute_notify(executor, context)

            elif executor.type == ActionExecutorType.MOVE_TASK:
                return self._execute_move_task(executor, context)

            elif executor.type == ActionExecutorType.CREATE_TASK:
                return self._execute_create_task(executor, context)

            elif executor.type == ActionExecutorType.MARK_COMPLETE:
                return self._execute_mark_complete(executor, context)

            elif executor.type == ActionExecutorType.CREATE_BRANCH:
                return self._execute_create_branch(executor, context)

            elif executor.type == ActionExecutorType.JIRA_UPDATE:
                return self._execute_jira_update(executor, context)

            elif executor.type == ActionExecutorType.RUN_COMMAND:
                return self._execute_run_command(executor, context)

            else:
                self.logger.error(f"Unknown executor type: {executor.type}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to execute {executor.type}: {e}", exc_info=True)
            return False

    def _execute_notify(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a notification action"""
        if not self.notification_service:
            self.logger.warning("NotificationService not available")
            return False

        # Interpolate variables in message
        message = self._interpolate_message(executor.message or "", context)
        title = self._interpolate_message(executor.title or "MKanban", context)

        return self.notification_service.send_notification(
            message=message,
            title=title,
            platforms=executor.platforms,
            channels=executor.channels,
            priority=executor.priority
        )

    def _execute_move_task(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a move task action"""
        if not self.item_service:
            self.logger.warning("ItemService not available")
            return False

        task = context.get("task")
        if not task or not executor.target_column:
            return False

        return self.item_service.move_item(
            task.id,
            executor.target_column
        )

    def _execute_create_task(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a create task action"""
        if not self.item_service:
            self.logger.warning("ItemService not available")
            return False

        title = self._interpolate_message(executor.task_title or "", context)
        description = self._interpolate_message(executor.task_description or "", context)

        return self.item_service.create_item(
            board_id=executor.board_id,
            column_id=executor.task_column,
            title=title,
            description=description
        ) is not None

    def _execute_mark_complete(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a mark complete action"""
        if not self.item_service:
            self.logger.warning("ItemService not available")
            return False

        task = context.get("task")
        if not task:
            return False

        # Move to done column
        return self.item_service.move_item(task.id, "done")

    def _execute_create_branch(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a create branch action"""
        # This would integrate with git service
        # Placeholder implementation
        self.logger.info(f"Would create branch: {executor.branch_name}")
        return True

    def _execute_jira_update(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a JIRA update action"""
        # This would integrate with JIRA service
        # Placeholder implementation
        self.logger.info(f"Would update JIRA field {executor.field} to {executor.value}")
        return True

    def _execute_run_command(
        self,
        executor: ActionExecutor,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a shell command action"""
        import subprocess

        try:
            command = self._interpolate_message(executor.command or "", context)

            result = subprocess.run(
                command,
                shell=True,
                cwd=executor.working_dir,
                env=executor.environment,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info(f"Command executed successfully: {command}")
                return True
            else:
                self.logger.error(f"Command failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to run command: {e}", exc_info=True)
            return False

    def _execute_chained_actions(
        self,
        action_ids: List[str],
        context: Dict[str, Any]
    ) -> None:
        """Execute chained actions"""
        for action_id in action_ids:
            action = self.action_service.get_action(action_id)
            if action:
                self.execute_action(action, context)

    def _interpolate_message(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """Interpolate variables in a message string"""
        task = context.get("task")
        board = context.get("board")

        replacements = {}
        if task:
            replacements["task_title"] = task.title
            replacements["task_id"] = task.id
            replacements["task_description"] = task.description
        if board:
            replacements["board_name"] = board.name
            replacements["board_id"] = board.id

        # Replace variables
        for key, value in replacements.items():
            message = message.replace(f"{{{key}}}", str(value))

        return message

    def _times_match(self, time1: datetime_time, time2: datetime_time, tolerance_minutes: int = 1) -> bool:
        """Check if two times match within a tolerance"""
        # Convert to minutes since midnight
        minutes1 = time1.hour * 60 + time1.minute
        minutes2 = time2.hour * 60 + time2.minute

        return abs(minutes1 - minutes2) < tolerance_minutes
