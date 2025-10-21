/**
 * ActionService - CRUD operations and action management
 */

import { Action, ActionType, createDefaultAction, isActionSnoozed } from '../domain/entities/Action';
import { ActionScope, ScopeType } from '../domain/entities/ActionScope';
import { ActionRepository, ActionFilter } from '../domain/repositories/ActionRepository';
import { BoardRepository } from '../domain/repositories/BoardRepository';
import { ActionsConfig } from '../core/ActionsConfig';

export interface SnoozeOptions {
  duration: string; // e.g., "10m", "30m", "1h", "tomorrow", "next_week"
}

export class ActionService {
  constructor(
    private actionRepository: ActionRepository,
    private boardRepository: BoardRepository,
    private actionsConfig: ActionsConfig
  ) {}

  /**
   * Get all actions
   */
  async getAllActions(filter?: ActionFilter): Promise<Action[]> {
    return this.actionRepository.getAll(filter);
  }

  /**
   * Get action by ID
   */
  async getActionById(id: string): Promise<Action | null> {
    return this.actionRepository.getById(id);
  }

  /**
   * Get actions by scope
   */
  async getActionsByScope(scopeType: ScopeType, targetId?: string): Promise<Action[]> {
    return this.actionRepository.getByScope(scopeType, targetId);
  }

  /**
   * Get enabled actions
   */
  async getEnabledActions(): Promise<Action[]> {
    return this.actionRepository.getEnabled();
  }

  /**
   * Get actions by type
   */
  async getActionsByType(type: ActionType): Promise<Action[]> {
    return this.actionRepository.getByType(type);
  }

  /**
   * Create a new action
   */
  async createAction(actionData: Partial<Action>): Promise<Action> {
    // Generate ID
    const id = this.generateActionId(actionData.type!, actionData.name!);

    // Create action with defaults
    const action: Action = {
      ...createDefaultAction(actionData.type!),
      ...actionData,
      id,
      createdAt: new Date().toISOString(),
      modifiedAt: new Date().toISOString(),
    } as Action;

    // Validate
    this.validateAction(action);

    // Save
    return this.actionRepository.create(action);
  }

  /**
   * Update an existing action
   */
  async updateAction(id: string, updates: Partial<Action>): Promise<Action> {
    const existing = await this.actionRepository.getById(id);
    if (!existing) {
      throw new Error(`Action ${id} not found`);
    }

    const updated: Action = {
      ...existing,
      ...updates,
      id: existing.id, // Preserve ID
      createdAt: existing.createdAt, // Preserve creation date
      modifiedAt: new Date().toISOString(),
    };

    this.validateAction(updated);

    return this.actionRepository.update(updated);
  }

  /**
   * Delete an action
   */
  async deleteAction(id: string): Promise<boolean> {
    return this.actionRepository.delete(id);
  }

  /**
   * Enable an action
   */
  async enableAction(id: string): Promise<Action> {
    return this.updateAction(id, { enabled: true });
  }

  /**
   * Disable an action
   */
  async disableAction(id: string): Promise<Action> {
    return this.updateAction(id, { enabled: false });
  }

  /**
   * Snooze an action
   */
  async snoozeAction(id: string, duration: string): Promise<Action> {
    const action = await this.actionRepository.getById(id);
    if (!action) {
      throw new Error(`Action ${id} not found`);
    }

    const snoozeUntil = this.calculateSnoozeTime(duration);

    const updated: Action = {
      ...action,
      snooze: {
        ...action.snooze,
        enabled: true,
        until: snoozeUntil.toISOString(),
        count: (action.snooze?.count || 0) + 1,
      },
      modifiedAt: new Date().toISOString(),
    };

    return this.actionRepository.update(updated);
  }

  /**
   * Unsnooze an action
   */
  async unsnoozeAction(id: string): Promise<Action> {
    const action = await this.actionRepository.getById(id);
    if (!action) {
      throw new Error(`Action ${id} not found`);
    }

    const updated: Action = {
      ...action,
      snooze: {
        ...action.snooze,
        enabled: false,
        until: null,
      },
      modifiedAt: new Date().toISOString(),
    };

    return this.actionRepository.update(updated);
  }

  /**
   * Record action execution
   */
  async recordExecution(id: string, success: boolean, error?: string): Promise<Action> {
    const action = await this.actionRepository.getById(id);
    if (!action) {
      throw new Error(`Action ${id} not found`);
    }

    const now = new Date().toISOString();

    const updated: Action = {
      ...action,
      execution: {
        ...action.execution!,
        lastTriggered: now,
        lastSuccess: success ? now : action.execution?.lastSuccess || null,
        lastFailure: success ? action.execution?.lastFailure || null : now,
        lastError: success ? null : error || null,
        totalExecutions: (action.execution?.totalExecutions || 0) + 1,
        successfulExecutions: success
          ? (action.execution?.successfulExecutions || 0) + 1
          : action.execution?.successfulExecutions || 0,
        consecutiveFailures: success ? 0 : (action.execution?.consecutiveFailures || 0) + 1,
      },
      modifiedAt: new Date().toISOString(),
    };

    return this.actionRepository.update(updated);
  }

  /**
   * Get orphaned actions (actions whose target board/task no longer exists)
   */
  async getOrphanedActions(): Promise<Action[]> {
    const allActions = await this.actionRepository.getAll();
    const orphaned: Action[] = [];

    for (const action of allActions) {
      if (await this.isOrphaned(action)) {
        orphaned.push(action);
      }
    }

    return orphaned;
  }

  /**
   * Clean orphaned actions based on configuration
   */
  async cleanOrphanedActions(): Promise<number> {
    const orphaned = await this.getOrphanedActions();
    const orphanAction = this.actionsConfig.getOrphanAction();

    let count = 0;

    for (const action of orphaned) {
      if (orphanAction === 'auto_delete') {
        await this.deleteAction(action.id);
        count++;
      } else if (orphanAction === 'auto_disable') {
        await this.disableAction(action.id);
        count++;
      }
      // 'warn_only' doesn't take action
    }

    return count;
  }

  /**
   * Check if an action is orphaned
   */
  private async isOrphaned(action: Action): Promise<boolean> {
    if (action.scope.type === ScopeType.GLOBAL) {
      return false; // Global actions can't be orphaned
    }

    if (action.scope.type === ScopeType.BOARD) {
      // Check if board exists
      try {
        const board = await this.boardRepository.getBoard(action.scope.targetId!);
        return !board;
      } catch (error) {
        return true;
      }
    }

    if (action.scope.type === ScopeType.TASK) {
      // TODO: Check if task exists (requires ItemService)
      // For now, assume task-scoped actions are not orphaned
      return false;
    }

    return false;
  }

  /**
   * Validate an action
   */
  private validateAction(action: Action): void {
    if (!action.id || action.id.length === 0) {
      throw new Error('Action ID is required');
    }

    if (!action.name || action.name.length === 0) {
      throw new Error('Action name is required');
    }

    if (!action.type) {
      throw new Error('Action type is required');
    }

    if (!action.scope || !action.scope.type) {
      throw new Error('Action scope is required');
    }

    if (action.scope.type !== ScopeType.GLOBAL && !action.scope.targetId) {
      throw new Error('Target ID is required for non-global scope');
    }

    if (!action.triggers || action.triggers.length === 0) {
      throw new Error('At least one trigger is required');
    }

    if (!action.actions || action.actions.length === 0) {
      throw new Error('At least one action executor is required');
    }
  }

  /**
   * Generate action ID
   */
  private generateActionId(type: ActionType, name: string): string {
    const typePrefix = type.substring(0, 3);
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').substring(0, 15);
    const namePart = name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .substring(0, 20);

    return `action-${typePrefix}-${namePart}-${timestamp}`;
  }

  /**
   * Calculate snooze time from duration string
   */
  private calculateSnoozeTime(duration: string): Date {
    const now = new Date();

    // Parse duration
    if (duration.endsWith('m')) {
      const minutes = parseInt(duration);
      now.setMinutes(now.getMinutes() + minutes);
    } else if (duration.endsWith('h')) {
      const hours = parseInt(duration);
      now.setHours(now.getHours() + hours);
    } else if (duration === 'tomorrow') {
      now.setDate(now.getDate() + 1);
      now.setHours(9, 0, 0, 0);
    } else if (duration === 'next_week') {
      now.setDate(now.getDate() + 7);
      now.setHours(9, 0, 0, 0);
    } else {
      // Default to 1 hour
      now.setHours(now.getHours() + 1);
    }

    return now;
  }

  /**
   * Get actions that should be executed now
   */
  async getActiveActions(): Promise<Action[]> {
    const enabled = await this.getEnabledActions();
    return enabled.filter((action) => !isActionSnoozed(action));
  }
}
