/**
 * EventBus - Simple pub/sub system for cross-service communication
 * Used to trigger actions based on application events
 */

export type EventType =
  // Task events
  | 'task_created'
  | 'task_updated'
  | 'task_deleted'
  | 'task_moved'
  | 'task_state_change'
  // Board events
  | 'board_created'
  | 'board_loaded'
  | 'board_updated'
  | 'board_deleted'
  | 'board_switched'
  | 'board_enter'
  | 'board_exit'
  // Column events
  | 'column_created'
  | 'column_updated'
  | 'column_deleted'
  // Git events (for future expansion)
  | 'git_branch_created'
  | 'git_branch_deleted'
  | 'git_branch_merged'
  | 'git_commit_made'
  // System events
  | 'app_startup'
  | 'app_shutdown'
  | 'app_foreground'
  | 'app_background';

export interface BaseEventPayload {
  timestamp: Date;
  source?: string;
}

export interface TaskEventPayload extends BaseEventPayload {
  taskId: string;
  taskTitle: string;
  boardId: string;
  columnId: string;
  previousColumnId?: string; // For task_moved events
}

export interface BoardEventPayload extends BaseEventPayload {
  boardId: string;
  boardName: string;
  previousBoardId?: string; // For board_switched events
}

export interface ColumnEventPayload extends BaseEventPayload {
  columnId: string;
  columnName: string;
  boardId: string;
}

export interface GitEventPayload extends BaseEventPayload {
  branchName: string;
  repositoryPath?: string;
  commitHash?: string;
}

export interface SystemEventPayload extends BaseEventPayload {
  metadata?: Record<string, any>;
}

export type EventPayload =
  | TaskEventPayload
  | BoardEventPayload
  | ColumnEventPayload
  | GitEventPayload
  | SystemEventPayload;

export type EventHandler<T extends EventPayload = EventPayload> = (
  payload: T
) => void | Promise<void>;

export interface EventSubscription {
  unsubscribe: () => void;
}

/**
 * Simple event bus implementation for pub/sub pattern
 */
class EventBus {
  private listeners: Map<EventType, Set<EventHandler>> = new Map();
  private eventHistory: Array<{ type: EventType; payload: EventPayload; timestamp: Date }> = [];
  private maxHistorySize = 100;

  /**
   * Subscribe to an event type
   */
  subscribe<T extends EventPayload = EventPayload>(
    eventType: EventType,
    handler: EventHandler<T>
  ): EventSubscription {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    this.listeners.get(eventType)!.add(handler as EventHandler);

    return {
      unsubscribe: () => {
        const handlers = this.listeners.get(eventType);
        if (handlers) {
          handlers.delete(handler as EventHandler);
          if (handlers.size === 0) {
            this.listeners.delete(eventType);
          }
        }
      },
    };
  }

  /**
   * Publish an event to all subscribers
   */
  async publish<T extends EventPayload>(eventType: EventType, payload: T): Promise<void> {
    // Add timestamp if not present
    if (!payload.timestamp) {
      payload.timestamp = new Date();
    }

    // Add to history
    this.addToHistory(eventType, payload);

    const handlers = this.listeners.get(eventType);
    if (!handlers || handlers.size === 0) {
      return;
    }

    // Execute all handlers (async handlers are awaited)
    const promises = Array.from(handlers).map(async (handler) => {
      try {
        await handler(payload);
      } catch (error) {
        console.error(`Error in event handler for ${eventType}:`, error);
      }
    });

    await Promise.all(promises);
  }

  /**
   * Publish an event without waiting for handlers to complete
   */
  publishSync<T extends EventPayload>(eventType: EventType, payload: T): void {
    // Add timestamp if not present
    if (!payload.timestamp) {
      payload.timestamp = new Date();
    }

    // Add to history
    this.addToHistory(eventType, payload);

    const handlers = this.listeners.get(eventType);
    if (!handlers || handlers.size === 0) {
      return;
    }

    // Execute all handlers without waiting
    handlers.forEach((handler) => {
      try {
        handler(payload);
      } catch (error) {
        console.error(`Error in event handler for ${eventType}:`, error);
      }
    });
  }

  /**
   * Subscribe to multiple event types with the same handler
   */
  subscribeMany<T extends EventPayload = EventPayload>(
    eventTypes: EventType[],
    handler: EventHandler<T>
  ): EventSubscription {
    const subscriptions = eventTypes.map((eventType) =>
      this.subscribe(eventType, handler)
    );

    return {
      unsubscribe: () => {
        subscriptions.forEach((sub) => sub.unsubscribe());
      },
    };
  }

  /**
   * Unsubscribe all handlers for an event type
   */
  unsubscribeAll(eventType: EventType): void {
    this.listeners.delete(eventType);
  }

  /**
   * Clear all subscriptions
   */
  clearAll(): void {
    this.listeners.clear();
  }

  /**
   * Get number of listeners for an event type
   */
  listenerCount(eventType: EventType): number {
    return this.listeners.get(eventType)?.size ?? 0;
  }

  /**
   * Get all event types that have listeners
   */
  getActiveEventTypes(): EventType[] {
    return Array.from(this.listeners.keys());
  }

  /**
   * Get event history
   */
  getHistory(eventType?: EventType, limit?: number): Array<{ type: EventType; payload: EventPayload; timestamp: Date }> {
    let history = eventType
      ? this.eventHistory.filter((e) => e.type === eventType)
      : this.eventHistory;

    if (limit) {
      history = history.slice(-limit);
    }

    return history;
  }

  /**
   * Clear event history
   */
  clearHistory(): void {
    this.eventHistory = [];
  }

  /**
   * Add event to history (internal)
   */
  private addToHistory(type: EventType, payload: EventPayload): void {
    this.eventHistory.push({
      type,
      payload,
      timestamp: new Date(),
    });

    // Keep history size under limit
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory = this.eventHistory.slice(-this.maxHistorySize);
    }
  }
}

// Singleton instance
let eventBusInstance: EventBus | null = null;

/**
 * Get the singleton EventBus instance
 */
export function getEventBus(): EventBus {
  if (!eventBusInstance) {
    eventBusInstance = new EventBus();
  }
  return eventBusInstance;
}

/**
 * Reset the EventBus instance (for testing)
 */
export function resetEventBus(): void {
  eventBusInstance = null;
}

export default EventBus;
