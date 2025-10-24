# MKanban Actions/Reminders Examples

This directory contains example action files demonstrating the capabilities of the MKanban actions/reminders system.

## Example Files

### 1. daily-standup-reminder.yaml
A simple time-based reminder that notifies you about daily standup meetings every weekday at 9:00 AM.

**Features demonstrated:**
- Time-based trigger with daily schedule
- Day-of-week filtering (weekdays only)
- Multi-platform notifications (desktop + mobile)
- Snooze functionality
- Time range conditions

**Usage:**
```bash
# Copy to your actions directory
cp daily-standup-reminder.yaml ~/.mkanban/actions/global/reminders/
```

### 2. stale-task-watcher.yaml
An automation that monitors for inactive tasks and moves them back to to-do after 48 hours.

**Features demonstrated:**
- Inactivity-based trigger
- Task property conditions
- Column-based conditions
- Automatic task movement
- Low-priority notifications

**Usage:**
```bash
# Copy to your actions directory
cp stale-task-watcher.yaml ~/.mkanban/actions/global/watchers/
```

### 3. board-enter-notification.yaml
A hook that sends a welcome notification when you open a specific board.

**Features demonstrated:**
- Event-based trigger (board switch)
- Board-scoped action
- Simple notification hook

**Usage:**
```bash
# Copy to your actions directory (replace "my-project" with your board ID)
cp board-enter-notification.yaml ~/.mkanban/actions/boards/my-project/hooks/
```

## Action Types

The system supports several types of actions:

- **reminder**: Time-based notifications
- **automation**: Event-driven automatic actions
- **watcher**: Continuous monitoring with conditions
- **hook**: Event hooks (pre/post actions)
- **scheduled_job**: Recurring tasks

## Creating Your Own Actions

### Basic Structure

```yaml
id: action-<type-prefix>-<name>-<timestamp>
type: reminder|automation|watcher|hook|scheduled_job
name: "Human-readable name"
description: "Detailed description"
enabled: true

scope:
  type: global|board|task
  target_id: null  # board-id or task-id if scoped

triggers:
  - type: time|board_switch|task_state_change|git_event|jira_event|inactivity
    # ... trigger-specific config

conditions:
  - type: time_range|task_in_column|task_property|board_property|day_of_week
    # ... condition-specific config

actions:
  - type: notify|move_task|create_task|mark_complete|create_branch|jira_update|run_command
    # ... action-specific config
```

### Trigger Types

**Time Trigger:**
```yaml
triggers:
  - type: time
    schedule:
      type: once|daily|weekly|monthly|cron
      datetime: "2024-10-20T17:00:00"  # for 'once'
      time: "09:00"  # for daily/weekly/monthly
      days_of_week: [1, 2, 3, 4, 5]  # for weekly
      cron_expression: "0 9 * * 1-5"  # for cron
```

**Board Switch Trigger:**
```yaml
triggers:
  - type: board_switch
    event: enter|exit
    board_id: "my-board"
```

**Task State Change Trigger:**
```yaml
triggers:
  - type: task_state_change
    events: ["moved", "created", "deleted", "updated"]
```

**Git Event Trigger:**
```yaml
triggers:
  - type: git_event
    events: ["branch_created", "branch_deleted", "branch_merged", "commit_made"]
```

**Inactivity Trigger:**
```yaml
triggers:
  - type: inactivity
    check_interval: 3600  # check every hour
    inactive_duration: 172800  # 48 hours of inactivity
```

### Action Types

**Notification:**
```yaml
actions:
  - type: notify
    message: "Your message here (supports variables like {task_title})"
    title: "Notification Title"
    platforms: ["desktop", "mobile"]  # or ["both"]
    channels: ["system", "mobile_push", "email"]
    priority: low|normal|high|urgent
```

**Move Task:**
```yaml
actions:
  - type: move_task
    target_column: "column-id"
```

**Create Task:**
```yaml
actions:
  - type: create_task
    task_title: "New task title"
    task_description: "Description"
    task_column: "to-do"
    board_id: "my-board"
```

**Run Command:**
```yaml
actions:
  - type: run_command
    command: "echo 'Hello from MKanban'"
    working_dir: "/path/to/dir"
    environment:
      KEY: "value"
```

### Condition Types

**Time Range:**
```yaml
conditions:
  - type: time_range
    start_time: "09:00"
    end_time: "17:00"
```

**Day of Week:**
```yaml
conditions:
  - type: day_of_week
    days: [1, 2, 3, 4, 5]  # Monday=1, Sunday=7
```

**Task in Column:**
```yaml
conditions:
  - type: task_in_column
    column_ids: ["to-do", "in-progress"]
```

**Task Property:**
```yaml
conditions:
  - type: task_property
    field: "is_git_managed"
    operator: equals|not_equals|greater_than|less_than|contains|in|matches_regex
    value: true
```

## Variables

The following variables can be used in message strings:

- `{task_title}` - Title of the task
- `{task_id}` - ID of the task
- `{task_description}` - Description of the task
- `{board_name}` - Name of the board
- `{board_id}` - ID of the board

Example: `"Don't forget to work on {task_title} today!"`

## Tips

1. **Test with dry runs**: Set `enabled: false` initially and test your action logic
2. **Use appropriate priorities**: Reserve `urgent` for critical notifications
3. **Leverage conditions**: Use conditions to avoid unnecessary executions
4. **Chain actions**: Use `on_success` and `on_failure` for complex workflows
5. **Monitor execution**: Check `execution` fields to see how often actions fire

## Configuration

Actions are configured in `~/.mkanban/config.json`:

```json
{
  "actions": {
    "enabled": true,
    "polling_interval": 30,
    "notifications": {
      "system": {
        "enabled": true,
        "command": "notify-send"
      },
      "mobile_push": {
        "enabled": true,
        "provider": "ntfy",
        "ntfy_server": "https://ntfy.sh",
        "ntfy_topic": "mkanban-your-unique-id"
      }
    }
  }
}
```

## CLI Commands

```bash
# List all actions
mkanban action list

# Create action from template
mkanban action create --template daily-reminder --time "09:00"

# View action details
mkanban action show <action-id>

# Enable/disable action
mkanban action enable <action-id>
mkanban action disable <action-id>

# Snooze action
mkanban action snooze <action-id> --duration 1h

# Delete action
mkanban action delete <action-id>
```

## Need Help?

- Check the main documentation: `docs/actions-reminders.md`
- View action logs: `~/.mkanban/logs/actions/`
- Report issues: https://github.com/your-repo/issues
