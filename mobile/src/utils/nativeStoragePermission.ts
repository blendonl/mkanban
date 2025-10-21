/**
 * Native Storage Permission Module Bridge
 * Bridges to native Android code for MANAGE_EXTERNAL_STORAGE permission
 */

import { NativeModules, Platform } from 'react-native';

interface StoragePermissionModuleType {
  checkPermission(): Promise<boolean>;
  requestPermission(): Promise<boolean>;
  getExternalStoragePath(): Promise<string>;
}

const { StoragePermissionModule } = NativeModules;

if (!StoragePermissionModule && Platform.OS === 'android') {
  console.error('[Native Module] StoragePermissionModule not found! Make sure native code is compiled.');
}

export const NativeStoragePermission: StoragePermissionModuleType = {
  /**
   * Check if MANAGE_EXTERNAL_STORAGE permission is granted (Android 11+)
   */
  async checkPermission(): Promise<boolean> {
    if (Platform.OS !== 'android') {
      return true;
    }

    if (!StoragePermissionModule) {
      console.warn('[Native Module] StoragePermissionModule not available, assuming no permission');
      return false;
    }

    try {
      const granted = await StoragePermissionModule.checkPermission();
      console.log(`[Native Module] checkPermission result: ${granted}`);
      return granted;
    } catch (error) {
      console.error('[Native Module] checkPermission failed:', error);
      return false;
    }
  },

  /**
   * Request MANAGE_EXTERNAL_STORAGE permission (opens settings on Android 11+)
   */
  async requestPermission(): Promise<boolean> {
    if (Platform.OS !== 'android') {
      return true;
    }

    if (!StoragePermissionModule) {
      console.warn('[Native Module] StoragePermissionModule not available');
      return false;
    }

    try {
      const result = await StoragePermissionModule.requestPermission();
      console.log(`[Native Module] requestPermission result: ${result}`);
      return result;
    } catch (error) {
      console.error('[Native Module] requestPermission failed:', error);
      return false;
    }
  },

  /**
   * Get the external storage directory path
   */
  async getExternalStoragePath(): Promise<string> {
    if (Platform.OS !== 'android') {
      return '';
    }

    if (!StoragePermissionModule) {
      console.warn('[Native Module] StoragePermissionModule not available');
      return '/storage/emulated/0';
    }

    try {
      const path = await StoragePermissionModule.getExternalStoragePath();
      console.log(`[Native Module] externalStoragePath: ${path}`);
      return path;
    } catch (error) {
      console.error('[Native Module] getExternalStoragePath failed:', error);
      return '/storage/emulated/0';
    }
  },
};
