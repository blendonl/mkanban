/**
 * Directory Picker Modal Component
 * Allows users to select a custom boards directory using native folder picker
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { File, Directory } from 'expo-file-system';
import * as FileSystemLegacy from 'expo-file-system/legacy';
import theme from '../theme';
import alertService from '../../services/AlertService';
import logger from '../../utils/logger';

interface DirectoryPickerModalProps {
  visible: boolean;
  currentPath: string;
  defaultPath: string;
  onConfirm: (path: string) => Promise<void>;
  onCancel: () => void;
}

export default function DirectoryPickerModal({
  visible,
  currentPath,
  defaultPath,
  onConfirm,
  onCancel,
}: DirectoryPickerModalProps) {
  const [selectedPath, setSelectedPath] = useState(currentPath);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPicking, setIsPicking] = useState(false);

  useEffect(() => {
    setSelectedPath(currentPath);
  }, [currentPath, visible]);

  const handleBrowseFolders = async () => {
    try {
      setIsPicking(true);

      // Use StorageAccessFramework for directory selection on Android
      // On iOS, this will use the standard directory picker
      const permissions = await FileSystemLegacy.StorageAccessFramework.requestDirectoryPermissionsAsync();

      if (permissions.granted) {
        let directoryPath = permissions.directoryUri;

        // Ensure path ends with /
        if (!directoryPath.endsWith('/')) {
          directoryPath += '/';
        }

        // Validate the selected path
        const isValid = await validatePath(directoryPath);
        if (isValid) {
          setSelectedPath(directoryPath);
        } else {
          alertService.showError(
            'The selected directory is not accessible or writable. Please choose a different location.',
            'Invalid Directory'
          );
        }
      }
    } catch (error) {
      logger.error('Error picking directory', error);
      alertService.showError('Failed to open folder picker. Please try again.');
    } finally {
      setIsPicking(false);
    }
  };

  const validatePath = async (path: string): Promise<boolean> => {
    try {
      // Check if this is a SAF URI (content://) - use StorageAccessFramework
      if (path.startsWith('content://')) {
        // For SAF URIs, use StorageAccessFramework methods
        // Try to create a test file to verify write permissions
        const testFileName = `.test-write-${Date.now()}`;
        const fileUri = await FileSystemLegacy.StorageAccessFramework.createFileAsync(
          path,
          testFileName,
          'text/plain'
        );

        // Clean up test file
        await FileSystemLegacy.deleteAsync(fileUri, { idempotent: true });

        return true;
      } else {
        // For regular file:// URIs, use the new Directory/File API
        const dir = new Directory(path);

        // Try to create the directory if it doesn't exist
        if (!dir.exists) {
          dir.create({ intermediates: true, idempotent: true });
        }

        // Try to write a test file INSIDE the directory to verify write permissions
        const testFileName = `.test-write-${Date.now()}`;
        const testFile = new File(dir, testFileName);
        testFile.write('test');

        // Clean up test file
        if (testFile.exists) {
          testFile.delete();
        }

        return true;
      }
    } catch (error) {
      logger.error('Path validation failed', error, { path });
      return false;
    }
  };

  const handleConfirm = async () => {
    if (!selectedPath || selectedPath.trim().length === 0) {
      alertService.showValidationError('Please select a valid directory');
      return;
    }

    const trimmedPath = selectedPath.trim();

    // Check if path has changed
    if (trimmedPath === currentPath) {
      onCancel();
      return;
    }

    // Validate the path before confirming
    setIsProcessing(true);
    const isValid = await validatePath(trimmedPath);
    setIsProcessing(false);

    if (!isValid) {
      alertService.showError(
        'The selected directory is not accessible or writable. Please choose a different location.',
        'Invalid Directory'
      );
      return;
    }

    // Apply the change
    await applyChange(trimmedPath);
  };

  const applyChange = async (path: string) => {
    try {
      setIsProcessing(true);
      await onConfirm(path);
    } catch (error) {
      logger.error('Failed to set directory', error, { path });
      alertService.showError(`Failed to set directory: ${error}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onCancel}
    >
      <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onCancel} disabled={isProcessing}>
            <Text style={styles.cancelButton}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Boards Directory</Text>
          <TouchableOpacity
            onPress={handleConfirm}
            disabled={isProcessing || !selectedPath.trim()}
          >
            <Text
              style={[
                styles.confirmButton,
                (isProcessing || !selectedPath.trim()) && styles.confirmButtonDisabled,
              ]}
            >
              {isProcessing ? 'Saving...' : 'Save'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content}>
          {/* Current Path Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Current Location</Text>
            <View style={styles.pathBox}>
              <Text style={styles.pathText} numberOfLines={3}>
                {currentPath}
              </Text>
            </View>
          </View>

          {/* Selected Path Display */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Selected Location</Text>
            <View style={styles.pathBox}>
              <Text style={styles.pathText} numberOfLines={3}>
                {selectedPath}
              </Text>
            </View>
          </View>

          {/* Browse Button */}
          <View style={styles.section}>
            <TouchableOpacity
              style={styles.browseButton}
              onPress={handleBrowseFolders}
              disabled={isProcessing || isPicking}
            >
              {isPicking ? (
                <ActivityIndicator color={theme.button.primary.text} />
              ) : (
                <Text style={styles.browseButtonText}>
                  📁 Browse Folders
                </Text>
              )}
            </TouchableOpacity>
            <Text style={styles.helperText}>
              Tap to open the system folder picker and choose a directory
            </Text>
          </View>

          {/* Warning */}
          <View style={styles.warningBox}>
            <Text style={styles.warningTitle}>⚠️ Important Notes</Text>
            <Text style={styles.warningText}>
              • Changing the directory will not automatically move your existing boards
            </Text>
            <Text style={styles.warningText}>
              • You may need to manually copy boards to the new location
            </Text>
            <Text style={styles.warningText}>
              • The directory must be writable by this app
            </Text>
            <Text style={styles.warningText}>
              • Use cloud storage paths (iCloud, Dropbox) for cross-device sync
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background.primary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.card.border,
    backgroundColor: theme.card.background,
  },
  title: {
    ...theme.typography.textStyles.h3,
    color: theme.text.primary,
  },
  cancelButton: {
    ...theme.typography.textStyles.body,
    color: theme.accent.primary,
  },
  confirmButton: {
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.accent.primary,
  },
  confirmButtonDisabled: {
    color: theme.text.tertiary,
  },
  content: {
    flex: 1,
  },
  section: {
    marginTop: theme.spacing.xl,
    paddingHorizontal: theme.spacing.lg,
  },
  sectionTitle: {
    ...theme.typography.textStyles.caption,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.text.secondary,
    textTransform: 'uppercase',
    marginBottom: theme.spacing.sm,
  },
  pathBox: {
    backgroundColor: theme.card.background,
    borderRadius: theme.radius.input,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.card.border,
  },
  pathText: {
    ...theme.typography.textStyles.caption,
    color: theme.text.primary,
    fontFamily: 'monospace',
  },
  browseButton: {
    backgroundColor: theme.button.primary.background,
    borderRadius: theme.radius.button,
    padding: theme.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: theme.ui.FAB_SIZE,
  },
  browseButtonText: {
    ...theme.typography.textStyles.h3,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.button.primary.text,
  },
  helperText: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.text.tertiary,
    marginTop: theme.spacing.sm,
    textAlign: 'center',
  },
  warningBox: {
    backgroundColor: '#fff3cd',
    padding: theme.spacing.lg,
    margin: theme.spacing.lg,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: '#ffc107',
  },
  warningTitle: {
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
    color: '#856404',
    marginBottom: theme.spacing.sm,
  },
  warningText: {
    ...theme.typography.textStyles.caption,
    color: '#856404',
    lineHeight: theme.typography.lineHeights.base,
    marginBottom: theme.spacing.xs,
  },
});
