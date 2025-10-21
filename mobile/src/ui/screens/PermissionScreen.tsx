/**
 * Permission Screen
 * Displays when storage permissions are not granted
 * Provides clear instructions and a button to open settings
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Platform,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { requestStoragePermission, checkStoragePermission } from '../../utils/storagePermissions';

interface PermissionScreenProps {
  onPermissionGranted: () => void;
}

export default function PermissionScreen({ onPermissionGranted }: PermissionScreenProps) {
  const [isChecking, setIsChecking] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState<Date | null>(null);

  const handleRequestPermission = async () => {
    setIsChecking(true);
    console.log('[PermissionScreen] Requesting permission...');
    const granted = await requestStoragePermission();
    setIsChecking(false);
    console.log(`[PermissionScreen] Permission request result: ${granted}`);

    if (granted) {
      onPermissionGranted();
    }
  };

  const handleCheckAgain = async () => {
    setIsChecking(true);
    setLastCheckTime(new Date());
    console.log('[PermissionScreen] Checking permission again...');

    const granted = await checkStoragePermission();
    setIsChecking(false);
    console.log(`[PermissionScreen] Permission check result: ${granted}`);

    if (granted) {
      Alert.alert(
        'Success!',
        'Storage permission has been granted. Loading boards...',
        [{ text: 'OK', onPress: () => onPermissionGranted() }]
      );
    } else {
      Alert.alert(
        'Permission Still Required',
        'Storage permission is still not granted. Please make sure you:\n\n' +
        '1. Opened Settings\n' +
        '2. Found "MKanban" (or "mobile") in the app list\n' +
        '3. Enabled "Allow management of all files"\n\n' +
        'The permission should show as "Allowed" or "On".',
        [{ text: 'Try Again', onPress: handleCheckAgain }]
      );
    }
  };

  const androidVersion = Platform.OS === 'android' ? Platform.Version : 0;
  const requiresManualSetup = androidVersion >= 30;

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {/* Icon */}
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>📂</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>Storage Permission Required</Text>

        {/* Description */}
        <Text style={styles.description}>
          MKanban needs access to your device's storage to save and load your Kanban boards.
        </Text>

        {requiresManualSetup ? (
          <>
            <Text style={styles.descriptionBold}>
              On Android 11+, you need to manually enable "All files access" permission.
            </Text>

            <View style={styles.instructionsContainer}>
              <Text style={styles.instructionsTitle}>How to grant permission:</Text>
              <Text style={styles.instructionStep}>1. Tap "Open Settings" below</Text>
              <Text style={styles.instructionStep}>2. Find "MKanban" in the list</Text>
              <Text style={styles.instructionStep}>3. Toggle "Allow management of all files" ON</Text>
              <Text style={styles.instructionStep}>4. Return to this app</Text>
            </View>
          </>
        ) : (
          <Text style={styles.descriptionBold}>
            Tap "Grant Permission" to continue.
          </Text>
        )}

        {/* Permission Button */}
        <TouchableOpacity
          style={[styles.button, isChecking && styles.buttonDisabled]}
          onPress={handleRequestPermission}
          activeOpacity={0.8}
          disabled={isChecking}
        >
          {isChecking ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>
              {requiresManualSetup ? 'Open Settings' : 'Grant Permission'}
            </Text>
          )}
        </TouchableOpacity>

        {/* Check Again Button (only for manual setup) */}
        {requiresManualSetup && (
          <>
            <TouchableOpacity
              style={[styles.buttonSecondary, isChecking && styles.buttonDisabled]}
              onPress={handleCheckAgain}
              activeOpacity={0.8}
              disabled={isChecking}
            >
              {isChecking ? (
                <ActivityIndicator color="#007AFF" />
              ) : (
                <Text style={styles.buttonSecondaryText}>
                  I've Granted Permission - Check Again
                </Text>
              )}
            </TouchableOpacity>
            {lastCheckTime && (
              <Text style={styles.debugText}>
                Last checked: {lastCheckTime.toLocaleTimeString()}
              </Text>
            )}
          </>
        )}

        {/* Privacy Note */}
        <Text style={styles.privacyNote}>
          Your data stays on your device. We only access the /storage/emulated/0/mkanban/ folder.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  content: {
    maxWidth: 400,
    width: '100%',
    alignItems: 'center',
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  icon: {
    fontSize: 50,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: '#cccccc',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 24,
  },
  descriptionBold: {
    fontSize: 16,
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 24,
    fontWeight: '600',
    lineHeight: 24,
  },
  instructionsContainer: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    width: '100%',
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
  },
  instructionStep: {
    fontSize: 14,
    color: '#cccccc',
    marginBottom: 8,
    lineHeight: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 32,
    marginBottom: 16,
    width: '100%',
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 32,
    marginBottom: 24,
    width: '100%',
    alignItems: 'center',
  },
  buttonSecondaryText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  debugText: {
    fontSize: 11,
    color: '#666666',
    textAlign: 'center',
    marginTop: -16,
    marginBottom: 16,
  },
  privacyNote: {
    fontSize: 12,
    color: '#888888',
    textAlign: 'center',
    lineHeight: 18,
  },
});
