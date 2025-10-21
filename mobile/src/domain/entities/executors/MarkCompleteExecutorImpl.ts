/**
 * MarkCompleteExecutorImpl - Mark task complete executor implementation
 */

import { MarkCompleteExecutor } from '../ActionExecutor';
import { Executor, ExecutionContext, ExecutionResult } from './BaseExecutor';
import { ItemService } from '../../../services/ItemService';

export class MarkCompleteExecutorImpl implements Executor {
  private doneColumnName = 'done'; // TODO: Make configurable

  constructor(
    private config: MarkCompleteExecutor,
    private itemService: ItemService
  ) {}

  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    try {
      if (!context.taskId || !context.boardId) {
        return {
          success: false,
          error: 'Missing taskId or boardId in context',
        };
      }

      const item = await this.itemService.getItem(
        context.boardId,
        context.columnId || '',
        context.taskId
      );

      if (!item) {
        return {
          success: false,
          error: `Task ${context.taskId} not found`,
        };
      }

      const success = await this.itemService.moveItem(
        context.boardId,
        item,
        context.columnId || '',
        this.doneColumnName
      );

      if (success) {
        return {
          success: true,
          message: `Marked task "${item.title}" as complete`,
        };
      } else {
        return {
          success: false,
          error: `Failed to mark task as complete`,
        };
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Error marking task complete: ${error.message}`,
      };
    }
  }

  async validate(): Promise<boolean> {
    return true; // No config to validate
  }
}
