/**
 * ActionRepository - Abstract interface for action storage
 */

import { Action, ActionType } from '../entities/Action';
import { ScopeType } from '../entities/ActionScope';

export interface ActionFilter {
  type?: ActionType;
  scopeType?: ScopeType;
  targetId?: string;
  enabled?: boolean;
  tags?: string[];
}

export interface ActionRepository {
  /**
   * Get all actions
   */
  getAll(filter?: ActionFilter): Promise<Action[]>;

  /**
   * Get action by ID
   */
  getById(id: string): Promise<Action | null>;

  /**
   * Get actions by scope
   */
  getByScope(scopeType: ScopeType, targetId?: string): Promise<Action[]>;

  /**
   * Get actions by type
   */
  getByType(type: ActionType): Promise<Action[]>;

  /**
   * Get enabled actions only
   */
  getEnabled(): Promise<Action[]>;

  /**
   * Create a new action
   */
  create(action: Action): Promise<Action>;

  /**
   * Update an existing action
   */
  update(action: Action): Promise<Action>;

  /**
   * Delete an action
   */
  delete(id: string): Promise<boolean>;

  /**
   * Check if action exists
   */
  exists(id: string): Promise<boolean>;

  /**
   * Get orphaned actions (actions whose target board/task no longer exists)
   */
  getOrphaned(): Promise<Action[]>;

  /**
   * Delete orphaned actions
   */
  deleteOrphaned(): Promise<number>;
}
