/**
 * ActionsConfig - Configuration for actions/reminders system
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface NotificationConfig {
  system: {
    enabled: boolean;
    sound: boolean;
    vibration: boolean;
    led: boolean;
  };
  mobilePush: {
    enabled: boolean;
    provider: string;
    ntfyServer?: string;
    ntfyTopic?: string;
    ntfyToken?: string;
  };
}

export interface ActionsConfiguration {
  enabled: boolean;
  pollingInterval: number; // Seconds
  defaultSnoozeOptions: string[];
  maxConcurrentExecutions: number;
  executionTimeout: number; // Seconds
  orphanCheckInterval: number; // Seconds
  orphanAction: 'auto_disable' | 'auto_delete' | 'warn_only';
  missedActionsRetention: number; // Days
  notifications: NotificationConfig;
}

const DEFAULT_CONFIG: ActionsConfiguration = {
  enabled: true,
  pollingInterval: 30,
  defaultSnoozeOptions: ['10m', '30m', '1h', '3h', 'tomorrow', 'next_week'],
  maxConcurrentExecutions: 5,
  executionTimeout: 300,
  orphanCheckInterval: 3600,
  orphanAction: 'auto_disable',
  missedActionsRetention: 7,
  notifications: {
    system: {
      enabled: true,
      sound: true,
      vibration: true,
      led: true,
    },
    mobilePush: {
      enabled: false,
      provider: 'ntfy',
    },
  },
};

const CONFIG_KEY = '@mkanban:actions_config';

export class ActionsConfig {
  private config: ActionsConfiguration = DEFAULT_CONFIG;
  private initialized = false;

  /**
   * Initialize configuration (load from storage)
   */
  async initialize(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(CONFIG_KEY);
      if (stored) {
        this.config = { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
      }
      this.initialized = true;
    } catch (error) {
      console.error('Error loading actions config:', error);
      this.config = DEFAULT_CONFIG;
      this.initialized = true;
    }
  }

  /**
   * Get full configuration
   */
  getConfig(): ActionsConfiguration {
    if (!this.initialized) {
      throw new Error('ActionsConfig not initialized. Call initialize() first.');
    }
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  async updateConfig(updates: Partial<ActionsConfiguration>): Promise<void> {
    this.config = { ...this.config, ...updates };
    try {
      await AsyncStorage.setItem(CONFIG_KEY, JSON.stringify(this.config));
    } catch (error) {
      console.error('Error saving actions config:', error);
    }
  }

  /**
   * Reset to defaults
   */
  async reset(): Promise<void> {
    this.config = DEFAULT_CONFIG;
    try {
      await AsyncStorage.removeItem(CONFIG_KEY);
    } catch (error) {
      console.error('Error resetting actions config:', error);
    }
  }

  // Convenience getters

  isEnabled(): boolean {
    return this.config.enabled;
  }

  getPollingInterval(): number {
    return this.config.pollingInterval;
  }

  getMaxConcurrentExecutions(): number {
    return this.config.maxConcurrentExecutions;
  }

  getExecutionTimeout(): number {
    return this.config.executionTimeout;
  }

  getDefaultSnoozeOptions(): string[] {
    return [...this.config.defaultSnoozeOptions];
  }

  isSystemNotificationsEnabled(): boolean {
    return this.config.notifications.system.enabled;
  }

  isMobilePushEnabled(): boolean {
    return this.config.notifications.mobilePush.enabled;
  }

  getNotificationConfig(): NotificationConfig {
    return { ...this.config.notifications };
  }

  getMissedActionsRetention(): number {
    return this.config.missedActionsRetention;
  }

  getOrphanAction(): 'auto_disable' | 'auto_delete' | 'warn_only' {
    return this.config.orphanAction;
  }
}

// Singleton instance
let actionsConfigInstance: ActionsConfig | null = null;

export function getActionsConfig(): ActionsConfig {
  if (!actionsConfigInstance) {
    actionsConfigInstance = new ActionsConfig();
  }
  return actionsConfigInstance;
}
