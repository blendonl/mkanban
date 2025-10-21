/**
 * ActionEngine - Orchestrates trigger evaluation, condition checking, and execution
 */

import { Action } from '../domain/entities/Action';
import { Condition, ConditionType } from '../domain/entities/Condition';
import { ExecutorType, ActionExecutor } from '../domain/entities/ActionExecutor';
import { TriggerType } from '../domain/entities/Trigger';
import { ActionService } from './ActionService';
import { ItemService } from './ItemService';
import { BoardService } from './BoardService';
import { NotificationService } from './NotificationService';
import { TimeTriggerEvaluator } from './triggers/TimeTriggerEvaluator';
import { EventTriggerEvaluator } from './triggers/EventTriggerEvaluator';
import { InactivityTriggerEvaluator } from './triggers/InactivityTriggerEvaluator';
import { EventType, EventPayload } from '../core/EventBus';
import { ExecutionContext, ExecutionResult } from '../domain/entities/executors/BaseExecutor';
import { NotifyExecutorImpl } from '../domain/entities/executors/NotifyExecutorImpl';
import { MoveTaskExecutorImpl } from '../domain/entities/executors/MoveTaskExecutorImpl';
import { CreateTaskExecutorImpl } from '../domain/entities/executors/CreateTaskExecutorImpl';
import { MarkCompleteExecutorImpl } from '../domain/entities/executors/MarkCompleteExecutorImpl';

export interface ExecutionQueue {
  action: Action;
  context: ExecutionContext;
  retryCount: number;
}

export class ActionEngine {
  private timeTriggerEvaluator: TimeTriggerEvaluator;
  private eventTriggerEvaluator: EventTriggerEvaluator;
  private inactivityTriggerEvaluator: InactivityTriggerEvaluator;
  private executionQueue: ExecutionQueue[] = [];
  private executing = false;

  constructor(
    private actionService: ActionService,
    private itemService: ItemService,
    private boardService: BoardService,
    private notificationService: NotificationService
  ) {
    this.timeTriggerEvaluator = new TimeTriggerEvaluator();
    this.eventTriggerEvaluator = new EventTriggerEvaluator();
    this.inactivityTriggerEvaluator = new InactivityTriggerEvaluator();
  }

  /**
   * Evaluate all time-based triggers
   */
  async evaluateTimeTriggers(): Promise<void> {
    const actions = await this.actionService.getActiveActions();
    const now = new Date();

    for (const action of actions) {
      const hasTimeTrigger = action.triggers.some((t) => t.type === TriggerType.TIME);
      if (!hasTimeTrigger) {
        continue;
      }

      if (this.timeTriggerEvaluator.shouldTrigger(action, now)) {
        await this.queueExecution(action, {
          action,
          timestamp: now,
        });
      }
    }
  }

  /**
   * Evaluate event-based triggers
   */
  async evaluateEventTriggers(eventType: EventType, eventPayload: EventPayload): Promise<void> {
    const actions = await this.actionService.getActiveActions();

    for (const action of actions) {
      const hasEventTrigger = action.triggers.some(
        (t) =>
          t.type === TriggerType.BOARD_SWITCH ||
          t.type === TriggerType.TASK_STATE_CHANGE ||
          t.type === TriggerType.GIT_EVENT
      );

      if (!hasEventTrigger) {
        continue;
      }

      if (this.eventTriggerEvaluator.shouldTrigger(action, eventType, eventPayload)) {
        await this.queueExecution(action, this.buildContextFromEvent(action, eventPayload));
      }
    }
  }

  /**
   * Evaluate inactivity triggers
   */
  async evaluateInactivityTriggers(): Promise<void> {
    const actions = await this.actionService.getActiveActions();

    for (const action of actions) {
      const hasInactivityTrigger = action.triggers.some((t) => t.type === TriggerType.INACTIVITY);
      if (!hasInactivityTrigger) {
        continue;
      }

      // TODO: Get all tasks and check inactivity
      // This requires iterating through all boards and tasks
      // For now, skip implementation - can be added when needed
    }
  }

  /**
   * Queue an action for execution
   */
  private async queueExecution(action: Action, context: ExecutionContext): Promise<void> {
    // Check conditions
    if (!(await this.checkConditions(action, context))) {
      console.log(`Conditions not met for action ${action.id}`);
      return;
    }

    // Add to queue
    this.executionQueue.push({
      action,
      context,
      retryCount: 0,
    });

    // Process queue
    this.processQueue();
  }

  /**
   * Process execution queue
   */
  private async processQueue(): Promise<void> {
    if (this.executing || this.executionQueue.length === 0) {
      return;
    }

    this.executing = true;

    try {
      while (this.executionQueue.length > 0) {
        const item = this.executionQueue.shift();
        if (!item) break;

        await this.executeAction(item.action, item.context, item.retryCount);
      }
    } finally {
      this.executing = false;
    }
  }

  /**
   * Execute an action
   */
  private async executeAction(
    action: Action,
    context: ExecutionContext,
    retryCount: number
  ): Promise<void> {
    console.log(`Executing action: ${action.name} (${action.id})`);

    try {
      // Execute all action executors
      const results: ExecutionResult[] = [];

      for (const executor of action.actions) {
        const result = await this.executeActionExecutor(executor, context);
        results.push(result);

        if (!result.success) {
          console.error(`Executor failed: ${result.error}`);
        }
      }

      // Check if all succeeded
      const allSucceeded = results.every((r) => r.success);

      // Record execution
      await this.actionService.recordExecution(
        action.id,
        allSucceeded,
        allSucceeded ? undefined : results.find((r) => !r.success)?.error
      );

      // Execute success/failure chain actions
      if (allSucceeded && action.onSuccess && action.onSuccess.length > 0) {
        await this.executeChainActions(action.onSuccess, context);
      } else if (!allSucceeded && action.onFailure && action.onFailure.length > 0) {
        await this.executeChainActions(action.onFailure, context);
      }

      // Retry on failure if configured
      if (!allSucceeded && retryCount < (action.metadata?.maxRetries || 0)) {
        const retryDelay = action.metadata?.retryDelay || 300;
        setTimeout(() => {
          this.executionQueue.push({
            action,
            context,
            retryCount: retryCount + 1,
          });
          this.processQueue();
        }, retryDelay * 1000);
      }
    } catch (error: any) {
      console.error(`Error executing action ${action.id}:`, error);
      await this.actionService.recordExecution(action.id, false, error.message);
    }
  }

  /**
   * Execute a single action executor
   */
  private async executeActionExecutor(
    executor: ActionExecutor,
    context: ExecutionContext
  ): Promise<ExecutionResult> {
    try {
      switch (executor.type) {
        case ExecutorType.NOTIFY:
          const notifyExecutor = new NotifyExecutorImpl(executor, this.notificationService);
          return await notifyExecutor.execute(context);

        case ExecutorType.MOVE_TASK:
          const moveExecutor = new MoveTaskExecutorImpl(executor, this.itemService);
          return await moveExecutor.execute(context);

        case ExecutorType.CREATE_TASK:
          const createExecutor = new CreateTaskExecutorImpl(executor, this.itemService);
          return await createExecutor.execute(context);

        case ExecutorType.MARK_COMPLETE:
          const completeExecutor = new MarkCompleteExecutorImpl(executor, this.itemService);
          return await completeExecutor.execute(context);

        default:
          return {
            success: false,
            error: `Unknown executor type: ${(executor as any).type}`,
          };
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Executor error: ${error.message}`,
      };
    }
  }

  /**
   * Execute chain actions
   */
  private async executeChainActions(actionIds: string[], context: ExecutionContext): Promise<void> {
    for (const actionId of actionIds) {
      const action = await this.actionService.getActionById(actionId);
      if (action && action.enabled) {
        await this.queueExecution(action, context);
      }
    }
  }

  /**
   * Check if all conditions are met
   */
  private async checkConditions(action: Action, context: ExecutionContext): Promise<boolean> {
    if (!action.conditions || action.conditions.length === 0) {
      return true; // No conditions, always pass
    }

    for (const condition of action.conditions) {
      if (!(await this.checkCondition(condition, context))) {
        return false;
      }
    }

    return true;
  }

  /**
   * Check a single condition
   */
  private async checkCondition(condition: Condition, context: ExecutionContext): Promise<boolean> {
    const now = new Date();

    switch (condition.type) {
      case ConditionType.TIME_RANGE:
        return this.checkTimeRange(condition as any, now);

      case ConditionType.DAY_OF_WEEK:
        return this.checkDayOfWeek(condition as any, now);

      case ConditionType.TASK_IN_COLUMN:
        return this.checkTaskInColumn(condition as any, context);

      case ConditionType.TASK_PROPERTY:
        return this.checkTaskProperty(condition as any, context);

      case ConditionType.BOARD_ACTIVE:
        return this.checkBoardActive(condition as any, context);

      default:
        return true;
    }
  }

  /**
   * Check time range condition
   */
  private checkTimeRange(condition: any, now: Date): boolean {
    const [startHour, startMin] = condition.startTime.split(':').map(Number);
    const [endHour, endMin] = condition.endTime.split(':').map(Number);

    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;

    return currentMinutes >= startMinutes && currentMinutes <= endMinutes;
  }

  /**
   * Check day of week condition
   */
  private checkDayOfWeek(condition: any, now: Date): boolean {
    const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();
    return condition.days.includes(dayOfWeek);
  }

  /**
   * Check task in column condition
   */
  private checkTaskInColumn(condition: any, context: ExecutionContext): boolean {
    if (!context.columnId) {
      return false;
    }
    return condition.columnIds.includes(context.columnId);
  }

  /**
   * Check task property condition
   */
  private checkTaskProperty(condition: any, context: ExecutionContext): boolean {
    // TODO: Implement property checking
    // This requires access to the full task object
    return true;
  }

  /**
   * Check board active condition
   */
  private checkBoardActive(condition: any, context: ExecutionContext): boolean {
    if (!context.boardId) {
      return false;
    }
    return condition.boardIds.includes(context.boardId);
  }

  /**
   * Build execution context from event payload
   */
  private buildContextFromEvent(action: Action, payload: EventPayload): ExecutionContext {
    const context: ExecutionContext = {
      action,
      timestamp: payload.timestamp,
    };

    // Extract common fields
    if ('taskId' in payload) {
      context.taskId = payload.taskId;
      context.taskTitle = payload.taskTitle;
    }

    if ('boardId' in payload) {
      context.boardId = payload.boardId;
      context.boardName = (payload as any).boardName;
    }

    if ('columnId' in payload) {
      context.columnId = payload.columnId;
    }

    return context;
  }

  /**
   * Get next trigger time for an action
   */
  getNextTriggerTime(action: Action): Date | null {
    return this.timeTriggerEvaluator.getNextTriggerTime(action);
  }

  /**
   * Get watched event types for an action
   */
  getWatchedEventTypes(action: Action): EventType[] {
    return this.eventTriggerEvaluator.getWatchedEventTypes(action);
  }
}
