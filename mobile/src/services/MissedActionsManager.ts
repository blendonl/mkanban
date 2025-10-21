/**
 * MissedActionsManager - Tracks and manages actions missed while app was closed
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Action } from '../domain/entities/Action';
import { ActionService } from './ActionService';
import { ActionsConfig } from '../core/ActionsConfig';
import { TimeTriggerEvaluator } from './triggers/TimeTriggerEvaluator';

export interface MissedAction {
  actionId: string;
  actionName: string;
  actionType: string;
  scheduledTime: string; // ISO string
  missedAt: string; // ISO string
  message?: string;
}

const MISSED_ACTIONS_KEY = '@mkanban:missed_actions';
const LAST_CHECK_KEY = '@mkanban:last_actions_check';

export class MissedActionsManager {
  private timeTriggerEvaluator: TimeTriggerEvaluator;

  constructor(
    private actionService: ActionService,
    private actionsConfig: ActionsConfig
  ) {
    this.timeTriggerEvaluator = new TimeTriggerEvaluator();
  }

  /**
   * Check for missed actions since last app close
   */
  async checkForMissedActions(): Promise<MissedAction[]> {
    try {
      const lastCheck = await this.getLastCheckTime();
      const now = new Date();

      if (!lastCheck) {
        // First run, no missed actions
        await this.updateLastCheckTime();
        return [];
      }

      // Get all time-based actions
      const actions = await this.actionService.getEnabledActions();
      const missedActions: MissedAction[] = [];

      for (const action of actions) {
        const missed = await this.checkActionForMisses(action, lastCheck, now);
        if (missed) {
          missedActions.push(missed);
        }
      }

      // Store missed actions
      if (missedActions.length > 0) {
        await this.storeMissedActions(missedActions);
      }

      // Update last check time
      await this.updateLastCheckTime();

      return missedActions;
    } catch (error) {
      console.error('Error checking for missed actions:', error);
      return [];
    }
  }

  /**
   * Check if a specific action was missed
   */
  private async checkActionForMisses(
    action: Action,
    lastCheck: Date,
    now: Date
  ): Promise<MissedAction | null> {
    const nextTriggerTime = this.timeTriggerEvaluator.getNextTriggerTime(action);

    if (!nextTriggerTime) {
      return null;
    }

    // Was the trigger time between last check and now?
    if (nextTriggerTime > lastCheck && nextTriggerTime <= now) {
      // Check if it was already executed
      if (action.execution?.lastTriggered) {
        const lastTriggered = new Date(action.execution.lastTriggered);
        if (lastTriggered >= nextTriggerTime) {
          return null; // Already executed
        }
      }

      // This action was missed
      return {
        actionId: action.id,
        actionName: action.name,
        actionType: action.type,
        scheduledTime: nextTriggerTime.toISOString(),
        missedAt: now.toISOString(),
        message: this.getActionMessage(action),
      };
    }

    return null;
  }

  /**
   * Get a user-friendly message for an action
   */
  private getActionMessage(action: Action): string {
    if (action.description) {
      return action.description;
    }

    // Try to extract message from notify executor
    const notifyExecutor = action.actions.find((a) => a.type === 'notify');
    if (notifyExecutor && 'message' in notifyExecutor) {
      return (notifyExecutor as any).message;
    }

    return action.name;
  }

  /**
   * Get all missed actions
   */
  async getMissedActions(): Promise<MissedAction[]> {
    try {
      const stored = await AsyncStorage.getItem(MISSED_ACTIONS_KEY);
      if (!stored) {
        return [];
      }

      const missed: MissedAction[] = JSON.parse(stored);

      // Filter out old missed actions (beyond retention period)
      const retentionDays = this.actionsConfig.getMissedActionsRetention();
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

      return missed.filter((m) => new Date(m.missedAt) >= cutoffDate);
    } catch (error) {
      console.error('Error getting missed actions:', error);
      return [];
    }
  }

  /**
   * Store missed actions
   */
  private async storeMissedActions(newMissed: MissedAction[]): Promise<void> {
    try {
      const existing = await this.getMissedActions();
      const combined = [...existing, ...newMissed];

      await AsyncStorage.setItem(MISSED_ACTIONS_KEY, JSON.stringify(combined));
    } catch (error) {
      console.error('Error storing missed actions:', error);
    }
  }

  /**
   * Clear a specific missed action
   */
  async clearMissedAction(actionId: string): Promise<void> {
    try {
      const missed = await this.getMissedActions();
      const filtered = missed.filter((m) => m.actionId !== actionId);

      await AsyncStorage.setItem(MISSED_ACTIONS_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error clearing missed action:', error);
    }
  }

  /**
   * Clear all missed actions
   */
  async clearAllMissedActions(): Promise<void> {
    try {
      await AsyncStorage.removeItem(MISSED_ACTIONS_KEY);
    } catch (error) {
      console.error('Error clearing all missed actions:', error);
    }
  }

  /**
   * Execute a missed action now
   */
  async executeMissedAction(actionId: string): Promise<boolean> {
    try {
      const action = await this.actionService.getActionById(actionId);
      if (!action) {
        console.error(`Action ${actionId} not found`);
        return false;
      }

      // TODO: Execute action through ActionEngine
      // For now, just clear it
      await this.clearMissedAction(actionId);
      return true;
    } catch (error) {
      console.error('Error executing missed action:', error);
      return false;
    }
  }

  /**
   * Get last check time
   */
  private async getLastCheckTime(): Promise<Date | null> {
    try {
      const stored = await AsyncStorage.getItem(LAST_CHECK_KEY);
      return stored ? new Date(stored) : null;
    } catch (error) {
      console.error('Error getting last check time:', error);
      return null;
    }
  }

  /**
   * Update last check time
   */
  private async updateLastCheckTime(): Promise<void> {
    try {
      await AsyncStorage.setItem(LAST_CHECK_KEY, new Date().toISOString());
    } catch (error) {
      console.error('Error updating last check time:', error);
    }
  }

  /**
   * Get count of missed actions
   */
  async getMissedActionsCount(): Promise<number> {
    const missed = await this.getMissedActions();
    return missed.length;
  }
}
