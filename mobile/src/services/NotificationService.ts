/**
 * NotificationService - Multi-channel notification dispatcher
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { ActionsConfig } from '../core/ActionsConfig';
import {
  ensureNotificationPermissions,
  setupNotificationChannels,
  getChannelForPriority,
} from '../utils/notificationPermissions';
import { NotificationPriority } from '../domain/entities/ActionExecutor';

export interface NotificationOptions {
  title: string;
  message: string;
  priority?: NotificationPriority;
  platforms?: string[];
  channels?: string[];
  sound?: boolean;
  vibrate?: boolean;
  badge?: number;
  data?: Record<string, any>;
}

export interface NotificationHandle {
  id: string;
  cancel: () => Promise<void>;
}

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export class NotificationService {
  private initialized = false;

  constructor(private actionsConfig: ActionsConfig) {}

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    // Setup notification channels (Android)
    await setupNotificationChannels();

    // Request permissions
    await ensureNotificationPermissions();

    this.initialized = true;
  }

  /**
   * Send a notification
   */
  async sendNotification(options: NotificationOptions): Promise<NotificationHandle | null> {
    if (!this.actionsConfig.isSystemNotificationsEnabled()) {
      console.log('System notifications disabled, skipping');
      return null;
    }

    try {
      // Ensure permissions
      const hasPermission = await ensureNotificationPermissions();
      if (!hasPermission) {
        console.warn('Notification permission not granted');
        return null;
      }

      const priority = options.priority || 'normal';
      const channel = getChannelForPriority(priority);

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: options.title,
          body: options.message,
          data: options.data || {},
          sound: options.sound !== false,
          badge: options.badge,
          priority: this.getPriorityValue(priority),
        },
        trigger: null, // Immediate delivery
      });

      return {
        id: notificationId,
        cancel: async () => {
          await Notifications.dismissNotificationAsync(notificationId);
        },
      };
    } catch (error) {
      console.error('Error sending notification:', error);
      return null;
    }
  }

  /**
   * Schedule a notification for later
   */
  async scheduleNotification(
    options: NotificationOptions,
    trigger: Date | { seconds: number }
  ): Promise<NotificationHandle | null> {
    if (!this.actionsConfig.isSystemNotificationsEnabled()) {
      console.log('System notifications disabled, skipping');
      return null;
    }

    try {
      const hasPermission = await ensureNotificationPermissions();
      if (!hasPermission) {
        console.warn('Notification permission not granted');
        return null;
      }

      const priority = options.priority || 'normal';
      const channel = getChannelForPriority(priority);

      let notificationTrigger: any;
      if (trigger instanceof Date) {
        notificationTrigger = trigger;
      } else {
        notificationTrigger = { seconds: trigger.seconds };
      }

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title: options.title,
          body: options.message,
          data: options.data || {},
          sound: options.sound !== false,
          badge: options.badge,
          priority: this.getPriorityValue(priority),
        },
        trigger: notificationTrigger,
      });

      return {
        id: notificationId,
        cancel: async () => {
          await Notifications.cancelScheduledNotificationAsync(notificationId);
        },
      };
    } catch (error) {
      console.error('Error scheduling notification:', error);
      return null;
    }
  }

  /**
   * Cancel a scheduled notification
   */
  async cancelNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
    } catch (error) {
      console.error('Error canceling notification:', error);
    }
  }

  /**
   * Cancel all notifications
   */
  async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Error canceling all notifications:', error);
    }
  }

  /**
   * Dismiss a displayed notification
   */
  async dismissNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.dismissNotificationAsync(notificationId);
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
  }

  /**
   * Dismiss all displayed notifications
   */
  async dismissAllNotifications(): Promise<void> {
    try {
      await Notifications.dismissAllNotificationsAsync();
    } catch (error) {
      console.error('Error dismissing all notifications:', error);
    }
  }

  /**
   * Get pending scheduled notifications
   */
  async getPendingNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      return await Notifications.getAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Error getting pending notifications:', error);
      return [];
    }
  }

  /**
   * Get priority value for platform
   */
  private getPriorityValue(priority: NotificationPriority): Notifications.AndroidNotificationPriority {
    if (Platform.OS !== 'android') {
      return Notifications.AndroidNotificationPriority.DEFAULT;
    }

    switch (priority) {
      case 'urgent':
        return Notifications.AndroidNotificationPriority.MAX;
      case 'high':
        return Notifications.AndroidNotificationPriority.HIGH;
      case 'normal':
        return Notifications.AndroidNotificationPriority.DEFAULT;
      case 'low':
        return Notifications.AndroidNotificationPriority.LOW;
      default:
        return Notifications.AndroidNotificationPriority.DEFAULT;
    }
  }

  /**
   * Add notification listener
   */
  addNotificationReceivedListener(
    listener: (notification: Notifications.Notification) => void
  ): Notifications.Subscription {
    return Notifications.addNotificationReceivedListener(listener);
  }

  /**
   * Add notification response listener (when user taps notification)
   */
  addNotificationResponseReceivedListener(
    listener: (response: Notifications.NotificationResponse) => void
  ): Notifications.Subscription {
    return Notifications.addNotificationResponseReceivedListener(listener);
  }
}
