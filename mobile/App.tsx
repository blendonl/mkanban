import React from 'react';
import { StatusBar } from 'expo-status-bar';
import AppNavigator from './src/ui/navigation/AppNavigator';
import ErrorBoundary from './src/ui/components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <AppNavigator />
      <StatusBar style="light" />
    </ErrorBoundary>
  );
}
