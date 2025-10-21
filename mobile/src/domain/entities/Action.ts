/**
 * Action - Main action entity
 */

import { ActionScope } from './ActionScope';
import { Trigger } from './Trigger';
import { Condition } from './Condition';
import { ActionExecutor } from './ActionExecutor';

export enum ActionType {
  REMINDER = 'reminder',
  AUTOMATION = 'automation',
  WATCHER = 'watcher',
  HOOK = 'hook',
  SCHEDULED_JOB = 'scheduled_job',
}

export interface Recurrence {
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  interval?: number;
  until?: string; // ISO string
  count?: number; // Number of occurrences
}

export interface SnoozeConfig {
  enabled: boolean;
  count: number;
  until: string | null; // ISO string
  options?: string[]; // e.g., ["10m", "30m", "1h", "tomorrow"]
}

export interface ExecutionHistory {
  lastTriggered: string | null; // ISO string
  lastSuccess: string | null; // ISO string
  lastFailure: string | null; // ISO string
  lastError: string | null;
  totalExecutions: number;
  successfulExecutions: number;
  consecutiveFailures: number;
}

export interface ActionMetadata {
  priority?: number; // Higher = more important
  maxRetries?: number;
  retryDelay?: number; // Seconds
  timeout?: number; // Seconds
  tags?: string[];
  custom?: Record<string, any>;
}

export interface Action {
  id: string;
  type: ActionType;
  name: string;
  description?: string;
  enabled: boolean;
  createdAt: string; // ISO string
  modifiedAt: string; // ISO string

  // Scope
  scope: ActionScope;

  // Triggers
  triggers: Trigger[];

  // Conditions (all must be true)
  conditions?: Condition[];

  // Actions to execute
  actions: ActionExecutor[];

  // Recurrence
  recurrence?: Recurrence | null;

  // Snooze
  snooze?: SnoozeConfig;

  // Execution history
  execution?: ExecutionHistory;

  // Metadata
  metadata?: ActionMetadata;

  // Chain actions
  onSuccess?: string[]; // Action IDs to trigger on success
  onFailure?: string[]; // Action IDs to trigger on failure
}

export function createDefaultAction(type: ActionType): Partial<Action> {
  const now = new Date().toISOString();

  return {
    type,
    enabled: true,
    createdAt: now,
    modifiedAt: now,
    triggers: [],
    actions: [],
    execution: {
      lastTriggered: null,
      lastSuccess: null,
      lastFailure: null,
      lastError: null,
      totalExecutions: 0,
      successfulExecutions: 0,
      consecutiveFailures: 0,
    },
    snooze: {
      enabled: true,
      count: 0,
      until: null,
      options: ['10m', '30m', '1h', '3h', 'tomorrow', 'next_week'],
    },
    metadata: {
      priority: 1,
      maxRetries: 3,
      retryDelay: 300,
      timeout: 30,
      tags: [],
      custom: {},
    },
  };
}

export function isActionSnoozed(action: Action): boolean {
  if (!action.snooze || !action.snooze.enabled) {
    return false;
  }

  if (action.snooze.until) {
    const snoozeUntil = new Date(action.snooze.until);
    return new Date() < snoozeUntil;
  }

  return false;
}

export function shouldExecuteAction(action: Action): boolean {
  return action.enabled && !isActionSnoozed(action);
}
