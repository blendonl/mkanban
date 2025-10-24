"""CLI commands for managing actions/reminders"""

import click
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from src.core.dependency_container import get_action_service
from src.domain.entities.action import ActionType
from src.domain.entities.action_scope import ActionScope, ScopeType
from src.domain.entities.trigger import Trigger, TriggerType, TimeSchedule, ScheduleType
from src.domain.entities.action_executor import ActionExecutor, ActionExecutorType, NotificationPriority
from src.utils.string_utils import generate_id_from_name


@click.group("action")
def action_command():
    """Manage actions and reminders"""
    pass


@action_command.command("list")
@click.option("--scope", type=click.Choice(["global", "board", "task"]), help="Filter by scope type")
@click.option("--target-id", help="Target board or task ID for scoped actions")
@click.option("--type", "action_type", type=click.Choice(["reminder", "automation", "watcher", "hook", "scheduled_job"]), help="Filter by action type")
@click.option("--enabled-only", is_flag=True, help="Show only enabled actions")
def list_actions(scope: Optional[str], target_id: Optional[str], action_type: Optional[str], enabled_only: bool):
    """List all actions"""
    try:
        service = get_action_service()

        # Get actions based on filters
        if scope:
            scope_type = ScopeType(scope)
            actions = service.get_actions_by_scope(scope_type, target_id)
        elif action_type:
            actions = service.get_actions_by_type(ActionType(action_type))
        elif enabled_only:
            actions = service.get_enabled_actions()
        else:
            actions = service.get_all_actions()

        if not actions:
            click.echo("No actions found.")
            return

        # Display actions
        click.echo(f"\nFound {len(actions)} action(s):\n")
        for action in actions:
            enabled_str = "✓" if action.enabled else "✗"
            scope_str = f"{action.scope.type.value}"
            if action.scope.target_id:
                scope_str += f":{action.scope.target_id}"

            click.echo(f"  [{enabled_str}] {action.id}")
            click.echo(f"      Name: {action.name}")
            click.echo(f"      Type: {action.type.value}")
            click.echo(f"      Scope: {scope_str}")
            click.echo(f"      Triggers: {len(action.triggers)}")
            click.echo(f"      Actions: {len(action.actions)}")
            if action.execution.total_executions > 0:
                click.echo(f"      Executions: {action.execution.successful_executions}/{action.execution.total_executions}")
            click.echo()

    except Exception as e:
        click.echo(f"Error listing actions: {e}", err=True)
        sys.exit(1)


@action_command.command("show")
@click.argument("action_id")
def show_action(action_id: str):
    """Show detailed information about an action"""
    try:
        service = get_action_service()
        action = service.get_action(action_id)

        if not action:
            click.echo(f"Action not found: {action_id}", err=True)
            sys.exit(1)

        # Display detailed information
        click.echo(f"\n=== Action: {action.name} ===\n")
        click.echo(f"ID: {action.id}")
        click.echo(f"Type: {action.type.value}")
        click.echo(f"Enabled: {'Yes' if action.enabled else 'No'}")
        click.echo(f"Description: {action.description or 'N/A'}")
        click.echo(f"\nScope:")
        click.echo(f"  Type: {action.scope.type.value}")
        if action.scope.target_id:
            click.echo(f"  Target ID: {action.scope.target_id}")

        click.echo(f"\nTriggers ({len(action.triggers)}):")
        for i, trigger in enumerate(action.triggers, 1):
            click.echo(f"  {i}. Type: {trigger.type.value}")
            if trigger.schedule:
                click.echo(f"     Schedule: {trigger.schedule.type.value}")
                if trigger.schedule.time:
                    click.echo(f"     Time: {trigger.schedule.time}")
                if trigger.schedule.days_of_week:
                    click.echo(f"     Days: {trigger.schedule.days_of_week}")

        click.echo(f"\nConditions ({len(action.conditions)}):")
        if action.conditions:
            for i, condition in enumerate(action.conditions, 1):
                click.echo(f"  {i}. Type: {condition.type.value}")
        else:
            click.echo("  None")

        click.echo(f"\nActions ({len(action.actions)}):")
        for i, executor in enumerate(action.actions, 1):
            click.echo(f"  {i}. Type: {executor.type.value}")
            if executor.message:
                click.echo(f"     Message: {executor.message[:50]}...")

        click.echo(f"\nExecution History:")
        click.echo(f"  Total: {action.execution.total_executions}")
        click.echo(f"  Successful: {action.execution.successful_executions}")
        click.echo(f"  Consecutive Failures: {action.execution.consecutive_failures}")
        if action.execution.last_triggered:
            click.echo(f"  Last Triggered: {action.execution.last_triggered}")
        if action.execution.last_error:
            click.echo(f"  Last Error: {action.execution.last_error}")

        if action.snooze and action.snooze.is_snoozed():
            click.echo(f"\n⏸️  Snoozed until: {action.snooze.until}")

        click.echo()

    except Exception as e:
        click.echo(f"Error showing action: {e}", err=True)
        sys.exit(1)


@action_command.command("create")
@click.option("--name", required=True, help="Name of the action")
@click.option("--type", "action_type", type=click.Choice(["reminder", "automation", "watcher", "hook"]), default="reminder", help="Type of action")
@click.option("--scope", type=click.Choice(["global", "board", "task"]), default="global", help="Scope of action")
@click.option("--target-id", help="Target board or task ID (required for board/task scope)")
@click.option("--time", help="Time for daily reminder (HH:MM format)")
@click.option("--message", help="Notification message")
@click.option("--platforms", default="desktop", help="Notification platforms (desktop/mobile/both)")
def create_action(
    name: str,
    action_type: str,
    scope: str,
    target_id: Optional[str],
    time: Optional[str],
    message: Optional[str],
    platforms: str
):
    """Create a new action"""
    try:
        service = get_action_service()

        # Validate scope
        scope_type = ScopeType(scope)
        if scope_type in [ScopeType.BOARD, ScopeType.TASK] and not target_id:
            click.echo("Error: --target-id is required for board/task scope", err=True)
            sys.exit(1)

        # Create action scope
        action_scope = ActionScope(type=scope_type, target_id=target_id)

        # Create trigger
        triggers = []
        if time:
            # Parse time
            try:
                hour, minute = map(int, time.split(":"))
                schedule = TimeSchedule(
                    type=ScheduleType.DAILY,
                    time=time,
                    days_of_week=[1, 2, 3, 4, 5],  # Weekdays by default
                    timezone="UTC"
                )
                triggers.append(Trigger(type=TriggerType.TIME, schedule=schedule))
            except ValueError:
                click.echo("Error: Invalid time format. Use HH:MM", err=True)
                sys.exit(1)
        else:
            click.echo("Warning: No trigger specified. Action will not execute.", err=True)

        # Create action executor
        executors = []
        if message:
            executor = ActionExecutor(
                type=ActionExecutorType.NOTIFY,
                message=message,
                title="MKanban",
                platforms=platforms.split(","),
                channels=["system"],
                priority=NotificationPriority.NORMAL
            )
            executors.append(executor)
        else:
            click.echo("Warning: No action specified. Nothing will happen when triggered.", err=True)

        # Create action
        action = service.create_action(
            action_type=ActionType(action_type),
            name=name,
            scope=action_scope,
            triggers=triggers,
            actions=executors
        )

        if action:
            click.echo(f"✓ Created action: {action.id}")
            click.echo(f"  Name: {action.name}")
            click.echo(f"  Type: {action.type.value}")
            click.echo(f"  Scope: {action.scope.type.value}")
            if time:
                click.echo(f"  Schedule: Daily at {time}")
        else:
            click.echo("Error: Failed to create action", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error creating action: {e}", err=True)
        sys.exit(1)


@action_command.command("enable")
@click.argument("action_id")
def enable_action(action_id: str):
    """Enable an action"""
    try:
        service = get_action_service()

        if service.enable_action(action_id):
            click.echo(f"✓ Enabled action: {action_id}")
        else:
            click.echo(f"Error: Action not found: {action_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error enabling action: {e}", err=True)
        sys.exit(1)


@action_command.command("disable")
@click.argument("action_id")
def disable_action(action_id: str):
    """Disable an action"""
    try:
        service = get_action_service()

        if service.disable_action(action_id):
            click.echo(f"✓ Disabled action: {action_id}")
        else:
            click.echo(f"Error: Action not found: {action_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error disabling action: {e}", err=True)
        sys.exit(1)


@action_command.command("delete")
@click.argument("action_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete_action(action_id: str, yes: bool):
    """Delete an action"""
    try:
        service = get_action_service()

        # Confirm deletion
        if not yes:
            action = service.get_action(action_id)
            if action:
                click.echo(f"About to delete: {action.name}")
                if not click.confirm("Are you sure?"):
                    click.echo("Cancelled.")
                    return
            else:
                click.echo(f"Error: Action not found: {action_id}", err=True)
                sys.exit(1)

        if service.delete_action(action_id):
            click.echo(f"✓ Deleted action: {action_id}")
        else:
            click.echo(f"Error: Failed to delete action: {action_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error deleting action: {e}", err=True)
        sys.exit(1)


@action_command.command("snooze")
@click.argument("action_id")
@click.option("--duration", default="1h", help="Snooze duration (e.g., 10m, 1h, tomorrow)")
def snooze_action(action_id: str, duration: str):
    """Snooze an action"""
    try:
        service = get_action_service()

        if service.snooze_action(action_id, duration):
            click.echo(f"✓ Snoozed action {action_id} for {duration}")
        else:
            click.echo(f"Error: Failed to snooze action: {action_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error snoozing action: {e}", err=True)
        sys.exit(1)


@action_command.command("unsnooze")
@click.argument("action_id")
def unsnooze_action(action_id: str):
    """Clear snooze on an action"""
    try:
        service = get_action_service()

        if service.clear_snooze(action_id):
            click.echo(f"✓ Cleared snooze on action: {action_id}")
        else:
            click.echo(f"Error: Failed to clear snooze: {action_id}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error clearing snooze: {e}", err=True)
        sys.exit(1)


@action_command.command("clean-orphaned")
@click.option("--delete", is_flag=True, help="Delete orphaned actions instead of disabling")
def clean_orphaned(delete: bool):
    """Clean up orphaned actions (actions referencing non-existent boards/tasks)"""
    try:
        service = get_action_service()

        count = service.cleanup_orphaned_actions(auto_disable=not delete)

        if count > 0:
            action_str = "deleted" if delete else "disabled"
            click.echo(f"✓ {action_str.capitalize()} {count} orphaned action(s)")
        else:
            click.echo("No orphaned actions found.")

    except Exception as e:
        click.echo(f"Error cleaning orphaned actions: {e}", err=True)
        sys.exit(1)


@action_command.command("history")
@click.argument("action_id")
@click.option("--limit", default=10, help="Number of recent executions to show")
def action_history(action_id: str, limit: int):
    """Show execution history for an action"""
    try:
        service = get_action_service()
        action = service.get_action(action_id)

        if not action:
            click.echo(f"Error: Action not found: {action_id}", err=True)
            sys.exit(1)

        click.echo(f"\n=== Execution History: {action.name} ===\n")
        click.echo(f"Total Executions: {action.execution.total_executions}")
        click.echo(f"Successful: {action.execution.successful_executions}")
        click.echo(f"Failed: {action.execution.total_executions - action.execution.successful_executions}")
        click.echo(f"Consecutive Failures: {action.execution.consecutive_failures}")

        if action.execution.last_triggered:
            click.echo(f"\nLast Triggered: {action.execution.last_triggered}")

        if action.execution.last_success:
            click.echo(f"Last Success: {action.execution.last_success}")

        if action.execution.last_failure:
            click.echo(f"Last Failure: {action.execution.last_failure}")
            if action.execution.last_error:
                click.echo(f"  Error: {action.execution.last_error}")

        click.echo()

    except Exception as e:
        click.echo(f"Error showing history: {e}", err=True)
        sys.exit(1)
