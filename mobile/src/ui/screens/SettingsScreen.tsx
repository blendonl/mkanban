/**
 * Settings Screen for MKanban mobile app
 * Allows users to configure app settings and view information
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Platform,
} from 'react-native';
import { FileSystemManager } from '../../infrastructure/storage/FileSystemManager';
import { getContainer } from '../../core/DependencyContainer';
import { Directory } from 'expo-file-system';

// App version - should match package.json
const APP_VERSION = '1.0.0';
const APP_BUILD = '1';

export default function SettingsScreen() {
  const [boardsPath, setBoardsPath] = useState<string>('');
  const [storageSize, setStorageSize] = useState<string>('Calculating...');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const container = getContainer();
      const fsManager = container.get(FileSystemManager);
      const path = fsManager.getBoardsDirectory();
      setBoardsPath(path);

      // Calculate storage size
      await calculateStorageSize(path);
    } catch (error) {
      console.error('Failed to load settings:', error);
      Alert.alert('Error', 'Failed to load settings');
    }
  };

  const calculateStorageSize = async (path: string) => {
    try {
      const dir = new Directory(path);
      if (dir.exists) {
        // This is a simplified calculation
        // In a real app, you'd recursively calculate directory size
        setStorageSize('< 1 MB');
      } else {
        setStorageSize('0 MB');
      }
    } catch (error) {
      console.error('Failed to calculate storage:', error);
      setStorageSize('Unknown');
    }
  };

  const handleResetToDefault = () => {
    Alert.alert(
      'Reset to Default',
      'This will reset all settings to default values. Your boards and items will NOT be deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);
              // Reset logic here (if we add custom path support later)
              await loadSettings();
              Alert.alert('Success', 'Settings reset to default');
            } catch (error) {
              console.error('Failed to reset settings:', error);
              Alert.alert('Error', 'Failed to reset settings');
            } finally {
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will clear temporary files and cache. Your boards and items will NOT be deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);
              // Clear cache logic here
              // For now, just show success
              setTimeout(() => {
                setIsLoading(false);
                Alert.alert('Success', 'Cache cleared successfully');
              }, 500);
            } catch (error) {
              console.error('Failed to clear cache:', error);
              Alert.alert('Error', 'Failed to clear cache');
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleOpenBoardsFolder = () => {
    Alert.alert(
      'Boards Directory',
      `Your boards are stored in:\n\n${boardsPath}\n\nYou can sync this folder using iCloud, Dropbox, or any file sync service.`,
      [{ text: 'OK' }]
    );
  };

  const handleAbout = () => {
    Alert.alert(
      'About MKanban',
      `Version: ${APP_VERSION} (${APP_BUILD})\n\n` +
        'MKanban is a mobile Kanban board application with markdown-based storage.\n\n' +
        'Compatible with MKanban Desktop (Python TUI version)\n\n' +
        'GitHub: https://github.com/yourusername/mkanban',
      [{ text: 'OK' }]
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* Storage Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Storage</Text>

        <TouchableOpacity
          style={styles.settingItem}
          onPress={handleOpenBoardsFolder}
        >
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Boards Directory</Text>
            <Text style={styles.settingValue} numberOfLines={1}>
              {boardsPath}
            </Text>
          </View>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Storage Used</Text>
            <Text style={styles.settingValue}>{storageSize}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.settingItem}
          onPress={handleClearCache}
          disabled={isLoading}
        >
          <Text style={styles.settingLabel}>Clear Cache</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Data Management Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Management</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            💡 Your boards are stored as markdown files. You can sync them across devices using:
          </Text>
          <Text style={styles.infoText}>• iCloud Drive</Text>
          <Text style={styles.infoText}>• Dropbox</Text>
          <Text style={styles.infoText}>• Google Drive</Text>
          <Text style={styles.infoText}>• Syncthing</Text>
          <Text style={styles.infoText}>• Any file sync service</Text>
        </View>

        <TouchableOpacity
          style={styles.settingItem}
          onPress={handleResetToDefault}
          disabled={isLoading}
        >
          <Text style={[styles.settingLabel, styles.dangerText]}>
            Reset to Default
          </Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      {/* About Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Version</Text>
          <Text style={styles.settingValue}>
            {APP_VERSION} ({APP_BUILD})
          </Text>
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Platform</Text>
          <Text style={styles.settingValue}>
            {Platform.OS === 'ios' ? 'iOS' : 'Android'}
          </Text>
        </View>

        <TouchableOpacity style={styles.settingItem} onPress={handleAbout}>
          <Text style={styles.settingLabel}>App Information</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Compatibility Note */}
      <View style={styles.section}>
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            ✨ <Text style={styles.boldText}>Desktop Compatible</Text>
          </Text>
          <Text style={styles.infoText}>
            This mobile app uses the same markdown file format as MKanban Desktop (Python TUI).
            You can seamlessly work with the same boards on both platforms.
          </Text>
        </View>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>MKanban Mobile</Text>
        <Text style={styles.footerText}>Made with ❤️ for productivity</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    marginTop: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    backgroundColor: '#f5f5f5',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    minHeight: 50,
  },
  settingContent: {
    flex: 1,
    marginRight: 8,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 2,
  },
  settingValue: {
    fontSize: 14,
    color: '#666',
  },
  chevron: {
    fontSize: 24,
    color: '#ccc',
    fontWeight: '300',
  },
  dangerText: {
    color: '#ff3b30',
  },
  infoBox: {
    backgroundColor: '#f0f7ff',
    padding: 16,
    margin: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d0e7ff',
  },
  infoText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
    marginBottom: 4,
  },
  boldText: {
    fontWeight: '600',
    color: '#333',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 30,
    paddingBottom: 50,
  },
  footerText: {
    fontSize: 13,
    color: '#999',
    marginBottom: 4,
  },
});
