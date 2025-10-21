/**
 * Storage Permissions Utility
 * Handles requesting external storage permissions for Android
 */

import { Platform, PermissionsAndroid, Alert } from 'react-native';
import { NativeStoragePermission } from './nativeStoragePermission';

/**
 * Request storage permission based on Android version
 *
 * Android 10 and below: Uses WRITE_EXTERNAL_STORAGE permission
 * Android 11+: Uses MANAGE_EXTERNAL_STORAGE permission (requires settings)
 *
 * @returns Promise<boolean> - true if permission granted, false otherwise
 */
export async function requestStoragePermission(): Promise<boolean> {
  if (Platform.OS !== 'android') {
    return true; // iOS doesn't need external storage permissions
  }

  const androidVersion = Platform.Version as number;

  if (androidVersion < 30) {
    // Android 10 and below - use WRITE_EXTERNAL_STORAGE
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
        {
          title: 'Storage Permission',
          message: 'MKanban needs access to storage to save your boards',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );

      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } catch (err) {
      console.error('Permission request error:', err);
      return false;
    }
  }

  // Android 11+ - Use native module for MANAGE_EXTERNAL_STORAGE
  console.log('[Permission Request] Using native module for Android 11+');
  return new Promise((resolve) => {
    Alert.alert(
      'Storage Permission Required',
      'To store boards in shared storage (/storage/emulated/0/mkanban/boards/), MKanban needs "All files access" permission.\n\nPlease enable it in the next screen.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
          onPress: () => resolve(false),
        },
        {
          text: 'Open Settings',
          onPress: async () => {
            try {
              // Use native module to open settings
              await NativeStoragePermission.requestPermission();
              resolve(true);
            } catch (error) {
              console.error('[Permission Request] Failed to open settings:', error);
              Alert.alert(
                'Error',
                'Could not open settings. Please manually enable "All files access" for MKanban in Settings > Apps > MKanban > Permissions'
              );
              resolve(false);
            }
          },
        },
      ]
    );
  });
}

/**
 * Check if storage permission is granted (Android only)
 *
 * @returns Promise<boolean> - true if permission is granted
 */
export async function checkStoragePermission(): Promise<boolean> {
  console.log('[Permission Check] Starting permission check...');

  if (Platform.OS !== 'android') {
    console.log('[Permission Check] iOS detected, no permission needed');
    return true;
  }

  const androidVersion = Platform.Version as number;
  console.log(`[Permission Check] Android version: ${androidVersion}`);

  if (androidVersion < 30) {
    // Android 10 and below
    const granted = await PermissionsAndroid.check(
      PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE
    );
    console.log(`[Permission Check] Android <30: WRITE_EXTERNAL_STORAGE = ${granted}`);
    return granted;
  }

  // Android 11+ - Use native module to check MANAGE_EXTERNAL_STORAGE
  console.log('[Permission Check] Android 11+, using native module...');

  try {
    const granted = await NativeStoragePermission.checkPermission();
    console.log(`[Permission Check] Native module result: ${granted}`);
    return granted;
  } catch (error) {
    console.error('[Permission Check] Native module check failed:', error);
    return false;
  }
}
