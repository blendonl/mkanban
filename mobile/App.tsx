import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import AppNavigator from './src/ui/navigation/AppNavigator';
import ErrorBoundary from './src/ui/components/ErrorBoundary';
import PermissionScreen from './src/ui/screens/PermissionScreen';
import { checkStoragePermission } from './src/utils/storagePermissions';
import { Platform, View, ActivityIndicator } from 'react-native';

export default function App() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    // iOS doesn't need external storage permissions
    if (Platform.OS !== 'android') {
      setHasPermission(true);
      return;
    }

    // Check if we have storage permission
    const granted = await checkStoragePermission();
    setHasPermission(granted);
  };

  const handlePermissionGranted = async () => {
    // Re-check permissions after user grants them
    await checkPermissions();
  };

  // Show loading screen while checking permissions
  if (hasPermission === null) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1a' }}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  // Show permission screen if not granted
  if (!hasPermission) {
    return (
      <ErrorBoundary>
        <PermissionScreen onPermissionGranted={handlePermissionGranted} />
        <StatusBar style="light" />
      </ErrorBoundary>
    );
  }

  // Show main app if permission granted
  return (
    <ErrorBoundary>
      <AppNavigator />
      <StatusBar style="light" />
    </ErrorBoundary>
  );
}
