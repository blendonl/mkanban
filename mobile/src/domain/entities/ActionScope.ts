/**
 * ActionScope - Defines the scope level of an action
 */

export enum ScopeType {
  GLOBAL = 'global',
  BOARD = 'board',
  TASK = 'task',
}

export interface ActionScope {
  type: ScopeType;
  targetId: string | null; // Board ID or Task ID, null for global
}

export function createGlobalScope(): ActionScope {
  return {
    type: ScopeType.GLOBAL,
    targetId: null,
  };
}

export function createBoardScope(boardId: string): ActionScope {
  return {
    type: ScopeType.BOARD,
    targetId: boardId,
  };
}

export function createTaskScope(taskId: string): ActionScope {
  return {
    type: ScopeType.TASK,
    targetId: taskId,
  };
}
