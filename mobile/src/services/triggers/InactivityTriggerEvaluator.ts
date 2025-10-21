/**
 * InactivityTriggerEvaluator - Evaluates inactivity-based triggers
 */

import { TriggerType, InactivityTrigger } from '../../domain/entities/Trigger';
import { Action } from '../../domain/entities/Action';
import { Item } from '../../domain/entities/Item';

export interface InactivityState {
  taskId: string;
  lastActivity: Date;
  lastCheck: Date;
}

export class InactivityTriggerEvaluator {
  private inactivityState: Map<string, InactivityState> = new Map();

  /**
   * Check if an action should be triggered based on task inactivity
   */
  shouldTrigger(action: Action, task: Item, now: Date = new Date()): boolean {
    const inactivityTriggers = action.triggers.filter(
      (t) => t.type === TriggerType.INACTIVITY
    ) as InactivityTrigger[];

    if (inactivityTriggers.length === 0) {
      return false;
    }

    for (const trigger of inactivityTriggers) {
      if (this.evaluateTrigger(trigger, task, now)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Evaluate a single inactivity trigger
   */
  private evaluateTrigger(trigger: InactivityTrigger, task: Item, now: Date): boolean {
    const state = this.getInactivityState(task.id);

    // Should we check now?
    const timeSinceLastCheck = (now.getTime() - state.lastCheck.getTime()) / 1000;
    if (timeSinceLastCheck < trigger.checkInterval) {
      return false; // Not time to check yet
    }

    // Update last check time
    state.lastCheck = now;

    // Calculate inactivity duration
    const inactiveDuration = (now.getTime() - state.lastActivity.getTime()) / 1000;

    // Trigger if inactive for longer than threshold
    return inactiveDuration >= trigger.inactiveDuration;
  }

  /**
   * Record task activity
   */
  recordActivity(taskId: string, timestamp: Date = new Date()): void {
    const state = this.getInactivityState(taskId);
    state.lastActivity = timestamp;
  }

  /**
   * Get inactivity state for a task
   */
  private getInactivityState(taskId: string): InactivityState {
    if (!this.inactivityState.has(taskId)) {
      const now = new Date();
      this.inactivityState.set(taskId, {
        taskId,
        lastActivity: now,
        lastCheck: now,
      });
    }

    return this.inactivityState.get(taskId)!;
  }

  /**
   * Get inactivity duration for a task (in seconds)
   */
  getInactivityDuration(taskId: string, now: Date = new Date()): number {
    const state = this.getInactivityState(taskId);
    return (now.getTime() - state.lastActivity.getTime()) / 1000;
  }

  /**
   * Clear state for a task
   */
  clearState(taskId: string): void {
    this.inactivityState.delete(taskId);
  }

  /**
   * Clear all state
   */
  clearAllState(): void {
    this.inactivityState.clear();
  }

  /**
   * Get tasks that are inactive (for monitoring)
   */
  getInactiveTasks(thresholdSeconds: number, now: Date = new Date()): string[] {
    const inactiveTasks: string[] = [];

    for (const [taskId, state] of this.inactivityState.entries()) {
      const duration = (now.getTime() - state.lastActivity.getTime()) / 1000;
      if (duration >= thresholdSeconds) {
        inactiveTasks.push(taskId);
      }
    }

    return inactiveTasks;
  }
}
