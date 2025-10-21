/**
 * notificationPermissions - Utility functions for handling notification permissions
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

export enum PermissionStatus {
  GRANTED = 'granted',
  DENIED = 'denied',
  UNDETERMINED = 'undetermined',
}

export interface NotificationPermissionResult {
  status: PermissionStatus;
  canAskAgain: boolean;
}

/**
 * Request notification permissions
 */
export async function requestNotificationPermissions(): Promise<NotificationPermissionResult> {
  try {
    const { status, canAskAgain } = await Notifications.requestPermissionsAsync({
      ios: {
        allowAlert: true,
        allowBadge: true,
        allowSound: true,
        allowAnnouncements: true,
      },
    });

    return {
      status: status as PermissionStatus,
      canAskAgain: canAskAgain ?? false,
    };
  } catch (error) {
    console.error('Error requesting notification permissions:', error);
    return {
      status: PermissionStatus.DENIED,
      canAskAgain: false,
    };
  }
}

/**
 * Check current notification permission status
 */
export async function getNotificationPermissionStatus(): Promise<NotificationPermissionResult> {
  try {
    const { status, canAskAgain } = await Notifications.getPermissionsAsync();

    return {
      status: status as PermissionStatus,
      canAskAgain: canAskAgain ?? false,
    };
  } catch (error) {
    console.error('Error getting notification permissions:', error);
    return {
      status: PermissionStatus.UNDETERMINED,
      canAskAgain: true,
    };
  }
}

/**
 * Check if notifications are enabled
 */
export async function areNotificationsEnabled(): Promise<boolean> {
  const { status } = await getNotificationPermissionStatus();
  return status === PermissionStatus.GRANTED;
}

/**
 * Request permissions if not already granted
 */
export async function ensureNotificationPermissions(): Promise<boolean> {
  const current = await getNotificationPermissionStatus();

  if (current.status === PermissionStatus.GRANTED) {
    return true;
  }

  if (current.status === PermissionStatus.UNDETERMINED || current.canAskAgain) {
    const result = await requestNotificationPermissions();
    return result.status === PermissionStatus.GRANTED;
  }

  return false;
}

/**
 * Setup notification channels (Android)
 */
export async function setupNotificationChannels(): Promise<void> {
  if (Platform.OS !== 'android') {
    return;
  }

  try {
    // Reminders channel
    await Notifications.setNotificationChannelAsync('reminders', {
      name: 'Reminders',
      description: 'Task reminders and time-based notifications',
      importance: Notifications.AndroidImportance.HIGH,
      sound: 'default',
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF6B6B',
      enableVibrate: true,
      enableLights: true,
      showBadge: true,
    });

    // Automations channel
    await Notifications.setNotificationChannelAsync('automations', {
      name: 'Automations',
      description: 'Automated task updates and actions',
      importance: Notifications.AndroidImportance.DEFAULT,
      sound: 'default',
      vibrationPattern: [0, 250],
      lightColor: '#4ECDC4',
      enableVibrate: true,
      enableLights: true,
      showBadge: true,
    });

    // System channel
    await Notifications.setNotificationChannelAsync('system', {
      name: 'System',
      description: 'System notifications and status updates',
      importance: Notifications.AndroidImportance.LOW,
      sound: 'default',
      lightColor: '#95E1D3',
      enableVibrate: false,
      enableLights: true,
      showBadge: false,
    });

    // Urgent channel
    await Notifications.setNotificationChannelAsync('urgent', {
      name: 'Urgent',
      description: 'Urgent notifications requiring immediate attention',
      importance: Notifications.AndroidImportance.MAX,
      sound: 'default',
      vibrationPattern: [0, 500, 250, 500],
      lightColor: '#FF0000',
      enableVibrate: true,
      enableLights: true,
      showBadge: true,
    });
  } catch (error) {
    console.error('Error setting up notification channels:', error);
  }
}

/**
 * Get notification channel for priority
 */
export function getChannelForPriority(priority: 'low' | 'normal' | 'high' | 'urgent'): string {
  switch (priority) {
    case 'urgent':
      return 'urgent';
    case 'high':
      return 'reminders';
    case 'normal':
      return 'automations';
    case 'low':
      return 'system';
    default:
      return 'automations';
  }
}
