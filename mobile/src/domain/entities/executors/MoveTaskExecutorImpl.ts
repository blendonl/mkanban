/**
 * MoveTaskExecutorImpl - Move task executor implementation
 */

import { MoveTaskExecutor } from '../ActionExecutor';
import { Executor, ExecutionContext, ExecutionResult } from './BaseExecutor';
import { ItemService } from '../../../services/ItemService';

export class MoveTaskExecutorImpl implements Executor {
  constructor(
    private config: MoveTaskExecutor,
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
        this.config.targetColumn
      );

      if (success) {
        return {
          success: true,
          message: `Moved task "${item.title}" to column "${this.config.targetColumn}"`,
        };
      } else {
        return {
          success: false,
          error: `Failed to move task to ${this.config.targetColumn}`,
        };
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Error moving task: ${error.message}`,
      };
    }
  }

  async validate(): Promise<boolean> {
    return !!this.config.targetColumn && this.config.targetColumn.length > 0;
  }
}
