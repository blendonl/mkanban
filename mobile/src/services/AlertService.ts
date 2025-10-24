/**
 * Alert Service for centralized user notifications
 * Replaces direct Alert.alert calls with consistent messaging
 */

import { Alert, AlertButton, AlertOptions } from 'react-native';

export interface AlertConfig {
  title: string;
  message: string;
  buttons?: AlertButton[];
  options?: AlertOptions;
}

class AlertService {
  /**
   * Show a generic alert
   */
  show(config: AlertConfig): void {
    Alert.alert(config.title, config.message, config.buttons, config.options);
  }

  /**
   * Show an error alert
   */
  showError(message: string, title: string = 'Error', onDismiss?: () => void): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: 'OK',
          onPress: onDismiss,
          style: 'default',
        },
      ],
      { cancelable: false }
    );
  }

  /**
   * Show a success alert
   */
  showSuccess(message: string, title: string = 'Success', onDismiss?: () => void): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: 'OK',
          onPress: onDismiss,
          style: 'default',
        },
      ],
      { cancelable: true }
    );
  }

  /**
   * Show an info alert
   */
  showInfo(message: string, title: string = 'Info', onDismiss?: () => void): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: 'OK',
          onPress: onDismiss,
          style: 'default',
        },
      ],
      { cancelable: true }
    );
  }

  /**
   * Show a warning alert
   */
  showWarning(message: string, title: string = 'Warning', onDismiss?: () => void): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: 'OK',
          onPress: onDismiss,
          style: 'default',
        },
      ],
      { cancelable: true }
    );
  }

  /**
   * Show a confirmation dialog with Yes/No buttons
   */
  showConfirm(
    message: string,
    onConfirm: () => void,
    onCancel?: () => void,
    title: string = 'Confirm',
    confirmText: string = 'Yes',
    cancelText: string = 'No'
  ): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: cancelText,
          onPress: onCancel,
          style: 'cancel',
        },
        {
          text: confirmText,
          onPress: onConfirm,
          style: 'default',
        },
      ],
      { cancelable: true }
    );
  }

  /**
   * Show a destructive confirmation dialog (for delete operations)
   */
  showDestructiveConfirm(
    message: string,
    onConfirm: () => void,
    onCancel?: () => void,
    title: string = 'Confirm',
    confirmText: string = 'Delete',
    cancelText: string = 'Cancel'
  ): void {
    Alert.alert(
      title,
      message,
      [
        {
          text: cancelText,
          onPress: onCancel,
          style: 'cancel',
        },
        {
          text: confirmText,
          onPress: onConfirm,
          style: 'destructive',
        },
      ],
      { cancelable: true }
    );
  }

  /**
   * Show a validation error alert
   */
  showValidationError(message: string, onDismiss?: () => void): void {
    this.showError(message, 'Validation Error', onDismiss);
  }

  /**
   * Show a network error alert
   */
  showNetworkError(onRetry?: () => void): void {
    const buttons: AlertButton[] = [
      {
        text: 'Cancel',
        style: 'cancel',
      },
    ];

    if (onRetry) {
      buttons.push({
        text: 'Retry',
        onPress: onRetry,
        style: 'default',
      });
    }

    Alert.alert(
      'Network Error',
      'Unable to connect to the server. Please check your internet connection and try again.',
      buttons,
      { cancelable: true }
    );
  }

  /**
   * Show a custom alert with multiple options
   */
  showOptions(
    title: string,
    message: string,
    options: Array<{ text: string; onPress: () => void; style?: 'default' | 'cancel' | 'destructive' }>
  ): void {
    const buttons: AlertButton[] = options.map((option) => ({
      text: option.text,
      onPress: option.onPress,
      style: option.style || 'default',
    }));

    Alert.alert(title, message, buttons, { cancelable: true });
  }

  /**
   * Show a loading error with retry option
   */
  showLoadingError(
    resourceName: string,
    onRetry?: () => void,
    onCancel?: () => void
  ): void {
    const buttons: AlertButton[] = [
      {
        text: 'Cancel',
        onPress: onCancel,
        style: 'cancel',
      },
    ];

    if (onRetry) {
      buttons.push({
        text: 'Retry',
        onPress: onRetry,
        style: 'default',
      });
    }

    Alert.alert(
      'Error',
      `Failed to load ${resourceName}. Please try again.`,
      buttons,
      { cancelable: false }
    );
  }
}

// Export singleton instance
export const alertService = new AlertService();

// Export default for convenience
export default alertService;

// Usage examples:
// alertService.showError('Failed to save board');
// alertService.showSuccess('Board created successfully');
// alertService.showConfirm('Are you sure?', () => deleteItem());
// alertService.showDestructiveConfirm('Delete this item?', () => deleteItem());
// alertService.showValidationError('Board name is required');
