import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
} from 'react-native';
import { Parent } from '../../domain/entities';
import { ParentColor } from '../../core/enums';
import ColorPicker from './ColorPicker';
import BaseModal from './BaseModal';
import { Input } from './Input';
import { PrimaryButton, SecondaryButton } from './Button';
import theme from '../theme';
import alertService from '../../services/AlertService';

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
      alertService.showValidationError('Parent name is required');
      return;
    }

    if (trimmedName.length > theme.ui.PARENT_NAME_MAX_LENGTH) {
      alertService.showValidationError(`Parent name must be ${theme.ui.PARENT_NAME_MAX_LENGTH} characters or less`);
      return;
    }

    try {
      setIsSaving(true);
      await onSave(trimmedName, selectedColor, parent?.id);
      handleClose();
    } catch (error) {
      alertService.showError(`Failed to save parent: ${error instanceof Error ? error.message : 'Unknown error'}`);
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
    <BaseModal
      visible={visible}
      onClose={handleClose}
      title={isEditing ? 'Edit Parent' : 'New Parent'}
      scrollable
      footer={
        <View style={styles.footer}>
          <SecondaryButton
            title="Cancel"
            onPress={handleClose}
            disabled={isSaving}
          />
          <PrimaryButton
            title={isSaving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            onPress={handleSave}
            disabled={isSaving}
            loading={isSaving}
          />
        </View>
      }
    >
      <View style={styles.field}>
        <Input
          label="Name"
          value={name}
          onChangeText={setName}
          placeholder="e.g., Feature X, Project Alpha"
          autoFocus={!isEditing}
          maxLength={theme.ui.PARENT_NAME_MAX_LENGTH}
          required
        />
      </View>

      <ColorPicker selectedColor={selectedColor} onColorSelect={setSelectedColor} />
    </BaseModal>
  );
}

const styles = StyleSheet.create({
  field: {
    marginBottom: theme.spacing.lg,
  },
  footer: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
});
