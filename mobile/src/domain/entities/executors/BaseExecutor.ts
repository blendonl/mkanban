/**
 * BaseExecutor - Base interface for all executors
 */

import { Action } from '../Action';

export interface ExecutionContext {
  action: Action;
  taskId?: string;
  taskTitle?: string;
  boardId?: string;
  boardName?: string;
  columnId?: string;
  [key: string]: any;
}

export interface ExecutionResult {
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
}

export interface Executor {
  /**
   * Execute the action
   */
  execute(context: ExecutionContext): Promise<ExecutionResult>;

  /**
   * Validate executor configuration
   */
  validate(): Promise<boolean>;
}

/**
 * Replace variables in a string with context values
 */
export function replaceVariables(template: string, context: ExecutionContext): string {
  let result = template;

  const variables: Record<string, any> = {
    task_title: context.taskTitle || '',
    task_id: context.taskId || '',
    board_name: context.boardName || '',
    board_id: context.boardId || '',
    column_id: context.columnId || '',
    action_name: context.action.name || '',
    ...context,
  };

  for (const [key, value] of Object.entries(variables)) {
    const regex = new RegExp(`\\{${key}\\}`, 'g');
    result = result.replace(regex, String(value));
  }

  return result;
}
