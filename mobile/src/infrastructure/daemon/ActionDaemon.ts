/**
 * ActionDaemon - Background service for polling and executing actions
 */

import { AppState, AppStateStatus } from 'react-native';
import { ActionEngine } from '../../services/ActionEngine';
import { ActionService } from '../../services/ActionService';
import { ActionsConfig } from '../../core/ActionsConfig';
import { getEventBus, EventType, EventPayload, EventSubscription } from '../../core/EventBus';

export class ActionDaemon {
  private pollingInterval: NodeJS.Timeout | null = null;
  private orphanCheckInterval: NodeJS.Timeout | null = null;
  private eventSubscriptions: EventSubscription[] = [];
  private isRunning = false;
  private appStateSubscription: any = null;

  constructor(
    private actionEngine: ActionEngine,
    private actionService: ActionService,
    private actionsConfig: ActionsConfig
  ) {}

  /**
   * Start the daemon
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log('ActionDaemon already running');
      return;
    }

    console.log('Starting ActionDaemon...');
    this.isRunning = true;

    // Start time-based polling
    this.startPolling();

    // Start orphan checking
    this.startOrphanCheck();

    // Subscribe to events
    this.subscribeToEvents();

    // Monitor app state
    this.monitorAppState();

    console.log('ActionDaemon started');
  }

  /**
   * Stop the daemon
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      console.log('ActionDaemon not running');
      return;
    }

    console.log('Stopping ActionDaemon...');
    this.isRunning = false;

    // Stop polling
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }

    // Stop orphan check
    if (this.orphanCheckInterval) {
      clearInterval(this.orphanCheckInterval);
      this.orphanCheckInterval = null;
    }

    // Unsubscribe from events
    this.eventSubscriptions.forEach((sub) => sub.unsubscribe());
    this.eventSubscriptions = [];

    // Remove app state listener
    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    console.log('ActionDaemon stopped');
  }

  /**
   * Restart the daemon
   */
  async restart(): Promise<void> {
    await this.stop();
    await this.start();
  }

  /**
   * Check if daemon is running
   */
  isActive(): boolean {
    return this.isRunning;
  }

  /**
   * Start time-based polling
   */
  private startPolling(): void {
    const interval = this.actionsConfig.getPollingInterval() * 1000;

    this.pollingInterval = setInterval(async () => {
      try {
        await this.actionEngine.evaluateTimeTriggers();
      } catch (error) {
        console.error('Error evaluating time triggers:', error);
      }
    }, interval);

    // Run immediately on start
    this.actionEngine.evaluateTimeTriggers().catch((error) => {
      console.error('Error on initial time trigger evaluation:', error);
    });
  }

  /**
   * Start orphan check polling
   */
  private startOrphanCheck(): void {
    const interval = this.actionsConfig.getConfig().orphanCheckInterval * 1000;

    this.orphanCheckInterval = setInterval(async () => {
      try {
        const count = await this.actionService.cleanOrphanedActions();
        if (count > 0) {
          console.log(`Cleaned ${count} orphaned actions`);
        }
      } catch (error) {
        console.error('Error cleaning orphaned actions:', error);
      }
    }, interval);
  }

  /**
   * Subscribe to application events
   */
  private subscribeToEvents(): void {
    const eventBus = getEventBus();

    // Subscribe to all event types that could trigger actions
    const eventTypes: EventType[] = [
      'task_created',
      'task_updated',
      'task_deleted',
      'task_moved',
      'board_created',
      'board_loaded',
      'board_updated',
      'board_deleted',
      'board_switched',
      'board_enter',
      'board_exit',
      'column_created',
      'column_updated',
      'column_deleted',
      'git_branch_created',
      'git_branch_deleted',
      'git_branch_merged',
      'git_commit_made',
    ];

    for (const eventType of eventTypes) {
      const subscription = eventBus.subscribe(eventType, async (payload: EventPayload) => {
        try {
          await this.actionEngine.evaluateEventTriggers(eventType, payload);
        } catch (error) {
          console.error(`Error evaluating event triggers for ${eventType}:`, error);
        }
      });

      this.eventSubscriptions.push(subscription);
    }

    console.log(`Subscribed to ${eventTypes.length} event types`);
  }

  /**
   * Monitor app state changes
   */
  private monitorAppState(): void {
    this.appStateSubscription = AppState.addEventListener(
      'change',
      this.handleAppStateChange.bind(this)
    );
  }

  /**
   * Handle app state changes
   */
  private async handleAppStateChange(nextAppState: AppStateStatus): Promise<void> {
    const eventBus = getEventBus();

    if (nextAppState === 'active') {
      console.log('App came to foreground');
      await eventBus.publish('app_foreground', {
        timestamp: new Date(),
      });

      // Resume polling if it was stopped
      if (this.isRunning && !this.pollingInterval) {
        this.startPolling();
      }
    } else if (nextAppState === 'background') {
      console.log('App went to background');
      await eventBus.publish('app_background', {
        timestamp: new Date(),
      });

      // Continue polling in background (if supported by foreground service)
      // Otherwise, polling will stop when app is suspended
    }
  }

  /**
   * Force evaluation of all triggers
   */
  async forceEvaluation(): Promise<void> {
    console.log('Force evaluating all triggers...');

    try {
      await this.actionEngine.evaluateTimeTriggers();
      console.log('Time triggers evaluated');
    } catch (error) {
      console.error('Error evaluating time triggers:', error);
    }

    // Inactivity triggers (if needed)
    try {
      await this.actionEngine.evaluateInactivityTriggers();
      console.log('Inactivity triggers evaluated');
    } catch (error) {
      console.error('Error evaluating inactivity triggers:', error);
    }
  }

  /**
   * Get daemon status
   */
  getStatus(): {
    running: boolean;
    pollingInterval: number;
    eventSubscriptions: number;
    actionsEnabled: boolean;
  } {
    return {
      running: this.isRunning,
      pollingInterval: this.actionsConfig.getPollingInterval(),
      eventSubscriptions: this.eventSubscriptions.length,
      actionsEnabled: this.actionsConfig.isEnabled(),
    };
  }
}
