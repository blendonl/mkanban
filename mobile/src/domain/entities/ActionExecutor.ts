/**
 * ActionExecutor - Defines what action to execute
 */

export enum ExecutorType {
  NOTIFY = 'notify',
  MOVE_TASK = 'move_task',
  CREATE_TASK = 'create_task',
  MARK_COMPLETE = 'mark_complete',
  CREATE_BRANCH = 'create_branch',
  JIRA_UPDATE = 'jira_update',
  RUN_COMMAND = 'run_command',
}

export enum NotificationPlatform {
  DESKTOP = 'desktop',
  MOBILE = 'mobile',
  BOTH = 'both',
}

export enum NotificationChannel {
  SYSTEM = 'system',
  MOBILE_PUSH = 'mobile_push',
  EMAIL = 'email',
}

export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

export interface NotifyExecutor {
  type: ExecutorType.NOTIFY;
  message: string; // Supports variables: {task_title}, {board_name}, etc.
  title?: string;
  platforms?: NotificationPlatform[];
  channels?: NotificationChannel[];
  priority?: NotificationPriority;
}

export interface MoveTaskExecutor {
  type: ExecutorType.MOVE_TASK;
  targetColumn: string;
}

export interface CreateTaskExecutor {
  type: ExecutorType.CREATE_TASK;
  taskTitle: string;
  taskDescription?: string;
  taskColumn: string;
  boardId?: string;
}

export interface MarkCompleteExecutor {
  type: ExecutorType.MARK_COMPLETE;
}

export interface CreateBranchExecutor {
  type: ExecutorType.CREATE_BRANCH;
  branchName: string;
}

export interface JiraUpdateExecutor {
  type: ExecutorType.JIRA_UPDATE;
  updates: Record<string, any>;
}

export interface RunCommandExecutor {
  type: ExecutorType.RUN_COMMAND;
  command: string;
  workingDir?: string;
  environment?: Record<string, string>;
}

export type ActionExecutor =
  | NotifyExecutor
  | MoveTaskExecutor
  | CreateTaskExecutor
  | MarkCompleteExecutor
  | CreateBranchExecutor
  | JiraUpdateExecutor
  | RunCommandExecutor;
