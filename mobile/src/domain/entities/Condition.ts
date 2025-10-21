/**
 * Condition - Defines conditions that must be met for an action to execute
 */

export enum ConditionType {
  TIME_RANGE = 'time_range',
  DAY_OF_WEEK = 'day_of_week',
  TASK_IN_COLUMN = 'task_in_column',
  TASK_PROPERTY = 'task_property',
  BOARD_ACTIVE = 'board_active',
}

export enum PropertyOperator {
  EQUALS = 'equals',
  NOT_EQUALS = 'not_equals',
  GREATER_THAN = 'greater_than',
  LESS_THAN = 'less_than',
  CONTAINS = 'contains',
  IN = 'in',
  MATCHES_REGEX = 'matches_regex',
}

export interface TimeRangeCondition {
  type: ConditionType.TIME_RANGE;
  startTime: string; // "HH:MM"
  endTime: string; // "HH:MM"
}

export interface DayOfWeekCondition {
  type: ConditionType.DAY_OF_WEEK;
  days: number[]; // 1=Monday, 7=Sunday
}

export interface TaskInColumnCondition {
  type: ConditionType.TASK_IN_COLUMN;
  columnIds: string[];
}

export interface TaskPropertyCondition {
  type: ConditionType.TASK_PROPERTY;
  field: string; // e.g., "is_git_managed", "priority", "status"
  operator: PropertyOperator;
  value: any;
}

export interface BoardActiveCondition {
  type: ConditionType.BOARD_ACTIVE;
  boardIds: string[];
}

export type Condition =
  | TimeRangeCondition
  | DayOfWeekCondition
  | TaskInColumnCondition
  | TaskPropertyCondition
  | BoardActiveCondition;
