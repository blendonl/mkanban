/**
 * Settings Screen for MKanban mobile app
 * Comprehensive settings management with directory picker, migration, and advanced options
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
  Switch,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { FileSystemManager } from '../../infrastructure/storage/FileSystemManager';
import { StorageConfig } from '../../core/StorageConfig';
import { BoardService } from '../../services/BoardService';
import { getContainer } from '../../core/DependencyContainer';
import { Directory } from 'expo-file-system';
import DirectoryPickerModal from '../components/DirectoryPickerModal';
import Toast from '../components/Toast';
import theme from '../theme/colors';

// App version - should match package.json
const APP_VERSION = '1.0.0';
const APP_BUILD = '1';

interface MigrationModalProps {
  visible: boolean;
  onMigrateAndChange: () => void;
  onChangeOnly: () => void;
  onCancel: () => void;
  boardCount: number;
}

const MigrationWarningModal: React.FC<MigrationModalProps> = ({
  visible,
  onMigrateAndChange,
  onChangeOnly,
  onCancel,
  boardCount,
}) => {
  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.modalOverlay}>
        <View style={styles.migrationModal}>
          <Text style={styles.migrationTitle}>⚠️ Boards Detected</Text>
          <Text style={styles.migrationMessage}>
            Your current directory contains {boardCount} board{boardCount !== 1 ? 's' : ''}.
            {'\n\n'}
            What would you like to do?
          </Text>

          <TouchableOpacity
            style={[styles.migrationButton, styles.migrationButtonPrimary]}
            onPress={onMigrateAndChange}
          >
            <Text style={styles.migrationButtonText}>📦 Migrate & Change</Text>
            <Text style={styles.migrationButtonSubtext}>
              Copy boards to new location and switch
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.migrationButton, styles.migrationButtonSecondary]}
            onPress={onChangeOnly}
          >
            <Text style={styles.migrationButtonText}>🔀 Change Only</Text>
            <Text style={styles.migrationButtonSubtext}>
              Switch without copying (boards stay in old location)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.migrationButton, styles.migrationButtonCancel]}
            onPress={onCancel}
          >
            <Text style={styles.migrationCancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

interface MigrationProgressModalProps {
  visible: boolean;
  progress: { current: number; total: number };
}

const MigrationProgressModal: React.FC<MigrationProgressModalProps> = ({
  visible,
  progress,
}) => {
  const percentage = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.modalOverlay}>
        <View style={styles.progressModal}>
          <ActivityIndicator size="large" color={theme.accent.primary} />
          <Text style={styles.progressTitle}>Migrating Boards...</Text>
          <Text style={styles.progressText}>
            {progress.current} / {progress.total} items ({percentage}%)
          </Text>
          <Text style={styles.progressSubtext}>Please wait, do not close the app</Text>
        </View>
      </View>
    </Modal>
  );
};

export default function SettingsScreen() {
  const navigation = useNavigation();

  // State for settings
  const [boardsPath, setBoardsPath] = useState<string>('');
  const [isCustomPath, setIsCustomPath] = useState<boolean>(false);
  const [storageSize, setStorageSize] = useState<string>('Calculating...');
  const [boardCount, setBoardCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);

  // State for modals
  const [directoryPickerVisible, setDirectoryPickerVisible] = useState(false);
  const [migrationWarningVisible, setMigrationWarningVisible] = useState(false);
  const [migrationProgressVisible, setMigrationProgressVisible] = useState(false);
  const [migrationProgress, setMigrationProgress] = useState({ current: 0, total: 0 });

  // State for pending directory change
  const [pendingNewPath, setPendingNewPath] = useState<string | null>(null);

  // State for toast
  const [toastVisible, setToastVisible] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error' | 'info'>('info');

  // Placeholder settings for future features
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [autoSaveInterval, setAutoSaveInterval] = useState(30);

  useEffect(() => {
    loadSettings();
  }, []);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToastMessage(message);
    setToastType(type);
    setToastVisible(true);
  };

  const loadSettings = async () => {
    try {
      const container = getContainer();
      const storageConfig = container.get(StorageConfig);
      const fsManager = container.get(FileSystemManager);

      const path = await storageConfig.getBoardsDirectory();
      const isCustom = await storageConfig.isUsingCustomDirectory();

      setBoardsPath(path);
      setIsCustomPath(isCustom);

      // Calculate storage size and board count
      await calculateStorageInfo(path, fsManager, storageConfig);
    } catch (error) {
      console.error('Failed to load settings:', error);
      showToast('Failed to load settings', 'error');
    }
  };

  const calculateStorageInfo = async (
    path: string,
    fsManager: FileSystemManager,
    storageConfig: StorageConfig
  ) => {
    try {
      const dir = new Directory(path);
      if (dir.exists) {
        // Get board count
        const boards = await storageConfig.listBoards(path);
        setBoardCount(boards.length);

        // Simplified storage calculation
        setStorageSize('< 1 MB');
      } else {
        setBoardCount(0);
        setStorageSize('0 MB');
      }
    } catch (error) {
      console.error('Failed to calculate storage info:', error);
      setStorageSize('Unknown');
      setBoardCount(0);
    }
  };

  const handleChangeDirectory = () => {
    setDirectoryPickerVisible(true);
  };

  const handleDirectorySelected = async (newPath: string) => {
    setDirectoryPickerVisible(false);

    // Validate that newPath is not undefined or empty
    if (!newPath || typeof newPath !== 'string' || newPath.trim().length === 0) {
      console.error('Invalid directory path:', newPath);
      showToast('Invalid directory path selected', 'error');
      return;
    }

    try {
      const container = getContainer();
      const storageConfig = container.get(StorageConfig);

      // Check if current directory has boards
      const hasBoards = await storageConfig.hasExistingBoards(boardsPath);

      if (hasBoards && boardCount > 0) {
        // Show migration warning
        setPendingNewPath(newPath);
        setMigrationWarningVisible(true);
      } else {
        // No boards, just change directory
        await performDirectoryChange(newPath, false);
      }
    } catch (error) {
      console.error('Error handling directory selection:', error);
      showToast('Failed to process directory change', 'error');
    }
  };

  const handleMigrateAndChange = async () => {
    setMigrationWarningVisible(false);

    if (!pendingNewPath) return;

    await performDirectoryChange(pendingNewPath, true);
  };

  const handleChangeOnly = async () => {
    setMigrationWarningVisible(false);

    if (!pendingNewPath) return;

    await performDirectoryChange(pendingNewPath, false);
  };

  const performDirectoryChange = async (newPath: string, migrate: boolean) => {
    setIsLoading(true);

    try {
      const container = getContainer();
      const storageConfig = container.get(StorageConfig);
      const boardService = container.get(BoardService);
      const fsManager = container.get(FileSystemManager);

      // Perform migration if requested
      if (migrate) {
        setMigrationProgressVisible(true);

        const result = await storageConfig.migrateBoards(
          boardsPath,
          newPath,
          (current, total) => {
            setMigrationProgress({ current, total });
          }
        );

        setMigrationProgressVisible(false);

        if (!result.success) {
          showToast(result.message, 'error');
          setIsLoading(false);
          return;
        }

        showToast(`Migrated ${result.copiedFiles} files successfully`, 'success');
      }

      // Update configuration
      await storageConfig.setBoardsDirectory(newPath);

      // Update FileSystemManager
      fsManager.setBoardsDirectory(newPath);

      // Reload board list
      await boardService.loadBoards();

      // Reload settings
      await loadSettings();

      // Navigate to board list
      navigation.navigate('BoardList' as never);

      showToast('Boards directory updated successfully', 'success');
    } catch (error) {
      console.error('Failed to change directory:', error);
      showToast(`Failed to change directory: ${error}`, 'error');
    } finally {
      setIsLoading(false);
      setPendingNewPath(null);
    }
  };

  const handleResetToDefault = () => {
    Alert.alert(
      'Reset to Default Directory',
      'This will reset the boards directory to the default location. Your boards will remain in their current location.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);

              const container = getContainer();
              const storageConfig = container.get(StorageConfig);
              const fsManager = container.get(FileSystemManager);
              const boardService = container.get(BoardService);

              // Reset to default
              await storageConfig.resetToDefault();

              // Update FileSystemManager
              const defaultPath = storageConfig.getDefaultBoardsDirectory();
              fsManager.setBoardsDirectory(defaultPath);

              // Reload boards
              await boardService.loadBoards();

              // Reload settings
              await loadSettings();

              // Navigate to board list
              navigation.navigate('BoardList' as never);

              showToast('Reset to default directory', 'success');
            } catch (error) {
              console.error('Failed to reset:', error);
              showToast('Failed to reset to default', 'error');
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

              const container = getContainer();
              const storageConfig = container.get(StorageConfig);
              storageConfig.clearCache();

              setTimeout(() => {
                setIsLoading(false);
                showToast('Cache cleared successfully', 'success');
              }, 500);
            } catch (error) {
              console.error('Failed to clear cache:', error);
              showToast('Failed to clear cache', 'error');
              setIsLoading(false);
            }
          },
        },
      ]
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
          onPress={handleChangeDirectory}
          disabled={isLoading}
        >
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Boards Directory</Text>
            <Text style={styles.settingValue} numberOfLines={1}>
              {boardsPath}
            </Text>
            {isCustomPath && (
              <Text style={styles.customBadge}>Custom</Text>
            )}
          </View>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Board Count</Text>
            <Text style={styles.settingValue}>{boardCount} board{boardCount !== 1 ? 's' : ''}</Text>
          </View>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Storage Used</Text>
            <Text style={styles.settingValue}>{storageSize}</Text>
          </View>
        </View>

        {isCustomPath && (
          <TouchableOpacity
            style={styles.settingItem}
            onPress={handleResetToDefault}
            disabled={isLoading}
          >
            <Text style={styles.settingLabel}>Reset to Default Directory</Text>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={styles.settingItem}
          onPress={handleClearCache}
          disabled={isLoading}
        >
          <Text style={styles.settingLabel}>Clear Cache</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Appearance Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Appearance</Text>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Auto-Save</Text>
            <Text style={styles.settingValue}>
              Automatically save changes every {autoSaveInterval} seconds
            </Text>
          </View>
          <Switch
            value={autoSaveEnabled}
            onValueChange={setAutoSaveEnabled}
            trackColor={{ false: theme.background.elevated, true: theme.accent.primary }}
            thumbColor={autoSaveEnabled ? theme.background.primary : theme.text.tertiary}
            disabled
          />
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Theme</Text>
            <Text style={styles.settingValue}>Catppuccin Mocha (Dark)</Text>
          </View>
          <Text style={styles.disabledText}>Coming Soon</Text>
        </View>
      </View>

      {/* Integration Settings (Placeholders for desktop parity) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Integrations</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            💡 Git and JIRA integrations are available on MKanban Desktop
          </Text>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>Git Integration</Text>
            <Text style={styles.settingValue}>Branch-based task management</Text>
          </View>
          <Text style={styles.disabledText}>Desktop Only</Text>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingContent}>
            <Text style={styles.settingLabel}>JIRA Sync</Text>
            <Text style={styles.settingValue}>Bidirectional JIRA synchronization</Text>
          </View>
          <Text style={styles.disabledText}>Desktop Only</Text>
        </View>
      </View>

      {/* Data Management Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Management</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            📁 Your boards are stored as markdown files. Sync them across devices using:
          </Text>
          <Text style={styles.infoText}>• iCloud Drive</Text>
          <Text style={styles.infoText}>• Dropbox</Text>
          <Text style={styles.infoText}>• Google Drive</Text>
          <Text style={styles.infoText}>• Syncthing</Text>
          <Text style={styles.infoText}>• Any file sync service</Text>
        </View>
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

      {/* Modals */}
      <DirectoryPickerModal
        visible={directoryPickerVisible}
        currentPath={boardsPath}
        defaultPath={getContainer().get(StorageConfig).getDefaultBoardsDirectory()}
        onConfirm={handleDirectorySelected}
        onCancel={() => setDirectoryPickerVisible(false)}
      />

      <MigrationWarningModal
        visible={migrationWarningVisible}
        onMigrateAndChange={handleMigrateAndChange}
        onChangeOnly={handleChangeOnly}
        onCancel={() => {
          setMigrationWarningVisible(false);
          setPendingNewPath(null);
        }}
        boardCount={boardCount}
      />

      <MigrationProgressModal
        visible={migrationProgressVisible}
        progress={migrationProgress}
      />

      <Toast
        visible={toastVisible}
        message={toastMessage}
        type={toastType}
        onHide={() => setToastVisible(false)}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background.primary,
  },
  section: {
    marginTop: 20,
    backgroundColor: theme.background.elevated,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: theme.border.primary,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.text.tertiary,
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    backgroundColor: theme.background.secondary,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
    minHeight: 50,
  },
  settingContent: {
    flex: 1,
    marginRight: 8,
  },
  settingLabel: {
    fontSize: 16,
    color: theme.text.primary,
    marginBottom: 2,
  },
  settingValue: {
    fontSize: 14,
    color: theme.text.secondary,
  },
  customBadge: {
    fontSize: 12,
    color: theme.accent.info,
    fontWeight: '600',
    marginTop: 4,
  },
  chevron: {
    fontSize: 24,
    color: theme.text.muted,
    fontWeight: '300',
  },
  disabledText: {
    fontSize: 14,
    color: theme.text.disabled,
  },
  dangerText: {
    color: theme.accent.error,
  },
  infoBox: {
    backgroundColor: theme.background.secondary,
    padding: 16,
    margin: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.border.secondary,
  },
  infoText: {
    fontSize: 14,
    color: theme.text.secondary,
    lineHeight: 20,
    marginBottom: 4,
  },
  boldText: {
    fontWeight: '600',
    color: theme.text.primary,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 30,
    paddingBottom: 50,
  },
  footerText: {
    fontSize: 13,
    color: theme.text.muted,
    marginBottom: 4,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: theme.modal.overlay,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  migrationModal: {
    backgroundColor: theme.background.elevated,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  migrationTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text.primary,
    marginBottom: 12,
    textAlign: 'center',
  },
  migrationMessage: {
    fontSize: 15,
    color: theme.text.secondary,
    marginBottom: 24,
    textAlign: 'center',
    lineHeight: 22,
  },
  migrationButton: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  migrationButtonPrimary: {
    backgroundColor: theme.button.primary.background,
  },
  migrationButtonSecondary: {
    backgroundColor: theme.button.secondary.background,
  },
  migrationButtonCancel: {
    backgroundColor: theme.background.secondary,
  },
  migrationButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text.primary,
    textAlign: 'center',
    marginBottom: 4,
  },
  migrationButtonSubtext: {
    fontSize: 13,
    color: theme.text.tertiary,
    textAlign: 'center',
  },
  migrationCancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text.secondary,
    textAlign: 'center',
  },
  progressModal: {
    backgroundColor: theme.background.elevated,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    width: '100%',
    maxWidth: 300,
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.text.primary,
    marginTop: 16,
    marginBottom: 8,
  },
  progressText: {
    fontSize: 16,
    color: theme.text.secondary,
    marginBottom: 4,
  },
  progressSubtext: {
    fontSize: 13,
    color: theme.text.tertiary,
    marginTop: 8,
    textAlign: 'center',
  },
});
