/**
 * NotifyExecutorImpl - Notification executor implementation
 */

import { NotifyExecutor } from '../ActionExecutor';
import { Executor, ExecutionContext, ExecutionResult, replaceVariables } from './BaseExecutor';

export class NotifyExecutorImpl implements Executor {
  constructor(
    private config: NotifyExecutor,
    private notificationService: any // Will be NotificationService once implemented
  ) {}

  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    try {
      const message = replaceVariables(this.config.message, context);
      const title = this.config.title
        ? replaceVariables(this.config.title, context)
        : 'MKanban';

      await this.notificationService.sendNotification({
        title,
        message,
        priority: this.config.priority || 'normal',
        platforms: this.config.platforms || ['mobile'],
        channels: this.config.channels || ['system'],
      });

      return {
        success: true,
        message: `Notification sent: ${message}`,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to send notification: ${error.message}`,
      };
    }
  }

  async validate(): Promise<boolean> {
    return !!this.config.message && this.config.message.length > 0;
  }
}
