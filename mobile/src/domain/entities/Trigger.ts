/**
 * Trigger - Defines when an action should be triggered
 */

export enum TriggerType {
  TIME = 'time',
  BOARD_SWITCH = 'board_switch',
  TASK_STATE_CHANGE = 'task_state_change',
  GIT_EVENT = 'git_event',
  JIRA_EVENT = 'jira_event',
  INACTIVITY = 'inactivity',
}

export enum ScheduleType {
  ONCE = 'once',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  CRON = 'cron',
}

export enum BoardSwitchEvent {
  ENTER = 'enter',
  EXIT = 'exit',
}

export type TaskStateChangeEvent =
  | 'created'
  | 'updated'
  | 'deleted'
  | 'moved';

export type GitEvent =
  | 'branch_created'
  | 'branch_deleted'
  | 'branch_merged'
  | 'commit_made';

export interface TimeSchedule {
  type: ScheduleType;
  datetime?: string; // ISO string for ONCE
  time?: string; // "HH:MM" for DAILY/WEEKLY/MONTHLY
  daysOfWeek?: number[]; // 1=Monday, 7=Sunday
  dayOfMonth?: number; // 1-31
  cronExpression?: string; // For CRON type
  timezone?: string; // e.g., "America/New_York"
}

export interface TimeTrigger {
  type: TriggerType.TIME;
  schedule: TimeSchedule;
}

export interface BoardSwitchTrigger {
  type: TriggerType.BOARD_SWITCH;
  event: BoardSwitchEvent;
  boardId?: string; // Optional: specific board, or any board if null
}

export interface TaskStateChangeTrigger {
  type: TriggerType.TASK_STATE_CHANGE;
  events: TaskStateChangeEvent[];
}

export interface GitEventTrigger {
  type: TriggerType.GIT_EVENT;
  events: GitEvent[];
}

export interface JiraEventTrigger {
  type: TriggerType.JIRA_EVENT;
  events: string[];
}

export interface InactivityTrigger {
  type: TriggerType.INACTIVITY;
  checkInterval: number; // Seconds
  inactiveDuration: number; // Seconds
}

export type Trigger =
  | TimeTrigger
  | BoardSwitchTrigger
  | TaskStateChangeTrigger
  | GitEventTrigger
  | JiraEventTrigger
  | InactivityTrigger;
