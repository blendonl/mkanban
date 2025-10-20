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
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { File, Directory } from 'expo-file-system';
import * as FileSystemLegacy from 'expo-file-system/legacy';
import theme from '../theme/colors';

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
          Alert.alert(
            'Invalid Directory',
            'The selected directory is not accessible or writable. Please choose a different location.'
          );
        }
      }
    } catch (error) {
      console.error('Error picking directory:', error);
      Alert.alert(
        'Error',
        'Failed to open folder picker. Please try again.'
      );
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
      console.error('Path validation failed:', error);
      return false;
    }
  };

  const handleConfirm = async () => {
    if (!selectedPath || selectedPath.trim().length === 0) {
      Alert.alert('Invalid Path', 'Please select a valid directory');
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
      Alert.alert(
        'Invalid Directory',
        'The selected directory is not accessible or writable. Please choose a different location.'
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
      console.error('Failed to set directory:', error);
      Alert.alert('Error', `Failed to set directory: ${error}`);
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
      <View style={styles.container}>
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
      </View>
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.card.border,
    backgroundColor: theme.card.background,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.text.primary,
  },
  cancelButton: {
    fontSize: 16,
    color: theme.accent.primary,
  },
  confirmButton: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.accent.primary,
  },
  confirmButtonDisabled: {
    color: theme.text.tertiary,
  },
  content: {
    flex: 1,
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.text.secondary,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  pathBox: {
    backgroundColor: theme.card.background,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: theme.card.border,
  },
  pathText: {
    fontSize: 13,
    color: theme.text.primary,
    fontFamily: 'monospace',
  },
  browseButton: {
    backgroundColor: theme.button.primary.background,
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  browseButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.button.primary.text,
  },
  helperText: {
    fontSize: 12,
    color: theme.text.tertiary,
    marginTop: 8,
    textAlign: 'center',
  },
  warningBox: {
    backgroundColor: '#fff3cd',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ffc107',
  },
  warningTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#856404',
    lineHeight: 20,
    marginBottom: 4,
  },
});
