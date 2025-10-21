/**
 * EventTriggerEvaluator - Evaluates event-based triggers
 */

import {
  Trigger,
  TriggerType,
  BoardSwitchTrigger,
  TaskStateChangeTrigger,
  GitEventTrigger,
} from '../../domain/entities/Trigger';
import { Action } from '../../domain/entities/Action';
import { EventType, EventPayload } from '../../core/EventBus';

export class EventTriggerEvaluator {
  /**
   * Check if an action should be triggered by an event
   */
  shouldTrigger(action: Action, eventType: EventType, eventPayload: EventPayload): boolean {
    // Check each trigger in the action
    for (const trigger of action.triggers) {
      if (this.evaluateTrigger(trigger, eventType, eventPayload)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Evaluate a single trigger against an event
   */
  private evaluateTrigger(
    trigger: Trigger,
    eventType: EventType,
    eventPayload: EventPayload
  ): boolean {
    switch (trigger.type) {
      case TriggerType.BOARD_SWITCH:
        return this.evaluateBoardSwitch(
          trigger as BoardSwitchTrigger,
          eventType,
          eventPayload
        );

      case TriggerType.TASK_STATE_CHANGE:
        return this.evaluateTaskStateChange(
          trigger as TaskStateChangeTrigger,
          eventType,
          eventPayload
        );

      case TriggerType.GIT_EVENT:
        return this.evaluateGitEvent(
          trigger as GitEventTrigger,
          eventType,
          eventPayload
        );

      default:
        return false;
    }
  }

  /**
   * Evaluate board switch trigger
   */
  private evaluateBoardSwitch(
    trigger: BoardSwitchTrigger,
    eventType: EventType,
    eventPayload: EventPayload
  ): boolean {
    // Map trigger event to EventType
    const expectedEventType =
      trigger.event === 'enter' ? 'board_enter' : 'board_exit';

    if (eventType !== expectedEventType) {
      return false;
    }

    // If specific board ID is specified, check it matches
    if (trigger.boardId) {
      const payload = eventPayload as any;
      return payload.boardId === trigger.boardId;
    }

    return true;
  }

  /**
   * Evaluate task state change trigger
   */
  private evaluateTaskStateChange(
    trigger: TaskStateChangeTrigger,
    eventType: EventType,
    eventPayload: EventPayload
  ): boolean {
    // Map trigger events to EventTypes
    const eventMapping: Record<string, EventType> = {
      created: 'task_created',
      updated: 'task_updated',
      deleted: 'task_deleted',
      moved: 'task_moved',
    };

    for (const event of trigger.events) {
      const expectedEventType = eventMapping[event];
      if (eventType === expectedEventType) {
        return true;
      }
    }

    return false;
  }

  /**
   * Evaluate git event trigger
   */
  private evaluateGitEvent(
    trigger: GitEventTrigger,
    eventType: EventType,
    eventPayload: EventPayload
  ): boolean {
    // Map trigger events to EventTypes
    const eventMapping: Record<string, EventType> = {
      branch_created: 'git_branch_created',
      branch_deleted: 'git_branch_deleted',
      branch_merged: 'git_branch_merged',
      commit_made: 'git_commit_made',
    };

    for (const event of trigger.events) {
      const expectedEventType = eventMapping[event];
      if (eventType === expectedEventType) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get list of event types that could trigger an action
   */
  getWatchedEventTypes(action: Action): EventType[] {
    const eventTypes = new Set<EventType>();

    for (const trigger of action.triggers) {
      const types = this.getEventTypesForTrigger(trigger);
      types.forEach((type) => eventTypes.add(type));
    }

    return Array.from(eventTypes);
  }

  /**
   * Get event types for a specific trigger
   */
  private getEventTypesForTrigger(trigger: Trigger): EventType[] {
    switch (trigger.type) {
      case TriggerType.BOARD_SWITCH:
        const boardTrigger = trigger as BoardSwitchTrigger;
        return boardTrigger.event === 'enter'
          ? ['board_enter']
          : ['board_exit'];

      case TriggerType.TASK_STATE_CHANGE:
        const taskTrigger = trigger as TaskStateChangeTrigger;
        const mapping: Record<string, EventType> = {
          created: 'task_created',
          updated: 'task_updated',
          deleted: 'task_deleted',
          moved: 'task_moved',
        };
        return taskTrigger.events.map((e) => mapping[e]).filter(Boolean);

      case TriggerType.GIT_EVENT:
        const gitTrigger = trigger as GitEventTrigger;
        const gitMapping: Record<string, EventType> = {
          branch_created: 'git_branch_created',
          branch_deleted: 'git_branch_deleted',
          branch_merged: 'git_branch_merged',
          commit_made: 'git_commit_made',
        };
        return gitTrigger.events.map((e) => gitMapping[e]).filter(Boolean);

      default:
        return [];
    }
  }
}
