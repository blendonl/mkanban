import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { Parent } from '../../domain/entities';
import { ParentColor } from '../../core/enums';
import ColorPicker from './ColorPicker';

interface ParentFormModalProps {
  visible: boolean;
  parent?: Parent | null; // If editing, pass existing parent
  onSave: (name: string, color: ParentColor, parentId?: string) => Promise<void>;
  onClose: () => void;
}

export default function ParentFormModal({
  visible,
  parent,
  onSave,
  onClose,
}: ParentFormModalProps) {
  const [name, setName] = useState('');
  const [selectedColor, setSelectedColor] = useState<ParentColor>(ParentColor.BLUE);
  const [isSaving, setIsSaving] = useState(false);

  const isEditing = !!parent;

  // Initialize form when parent changes
  useEffect(() => {
    if (parent) {
      setName(parent.name);
      setSelectedColor(parent.color);
    } else {
      setName('');
      setSelectedColor(ParentColor.BLUE);
    }
  }, [parent, visible]);

  const handleSave = async () => {
    const trimmedName = name.trim();

    if (!trimmedName) {
      Alert.alert('Validation Error', 'Parent name is required');
      return;
    }

    if (trimmedName.length > 100) {
      Alert.alert('Validation Error', 'Parent name must be 100 characters or less');
      return;
    }

    try {
      setIsSaving(true);
      await onSave(trimmedName, selectedColor, parent?.id);
      handleClose();
    } catch (error) {
      Alert.alert('Error', `Failed to save parent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    setName('');
    setSelectedColor(ParentColor.BLUE);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={handleClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <View style={styles.header}>
            <Text style={styles.title}>{isEditing ? 'Edit Parent' : 'New Parent'}</Text>
            <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content}>
            <View style={styles.field}>
              <Text style={styles.label}>Name *</Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="e.g., Feature X, Project Alpha"
                placeholderTextColor="#9ca3af"
                autoFocus={!isEditing}
                maxLength={100}
              />
            </View>

            <ColorPicker selectedColor={selectedColor} onColorSelect={setSelectedColor} />
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={handleClose}
              disabled={isSaving}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.saveButton, isSaving && styles.disabledButton]}
              onPress={handleSave}
              disabled={isSaving}
            >
              <Text style={styles.saveButtonText}>
                {isSaving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: 12,
    width: '90%',
    maxHeight: '80%',
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  closeButton: {
    padding: 4,
  },
  closeButtonText: {
    fontSize: 24,
    color: '#6b7280',
  },
  content: {
    padding: 16,
  },
  field: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#1f2937',
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1f2937',
  },
  footer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f3f4f6',
  },
  cancelButtonText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    backgroundColor: '#3b82f6',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
});
