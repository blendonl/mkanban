import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Parent } from '../../domain/entities';
import ParentBadge from './ParentBadge';
import BaseModal from './BaseModal';
import { PrimaryButton, DangerButton } from './Button';
import theme from '../theme';
import alertService from '../../services/AlertService';

interface ParentManagementModalProps {
  visible: boolean;
  parents: Parent[];
  onClose: () => void;
  onEdit: (parent: Parent) => void;
  onDelete: (parentId: string) => void;
  onCreate: () => void;
}

export default function ParentManagementModal({
  visible,
  parents,
  onClose,
  onEdit,
  onDelete,
  onCreate,
}: ParentManagementModalProps) {
  const handleDelete = (parent: Parent) => {
    alertService.showDestructiveConfirm(
      `Are you sure you want to delete "${parent.name}"? Items assigned to this parent will not be deleted, but will lose their parent assignment.`,
      () => onDelete(parent.id),
      undefined,
      'Delete Parent'
    );
  };

  return (
    <BaseModal
      visible={visible}
      onClose={onClose}
      title="Manage Parents"
      footer={
        <PrimaryButton
          title="+ Create Parent"
          onPress={onCreate}
          fullWidth
        />
      }
    >
      {parents.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No parents yet</Text>
          <Text style={styles.emptySubtext}>
            Create a parent to organize your items
          </Text>
        </View>
      ) : (
        parents.map((parent) => (
          <View key={parent.id} style={styles.parentItem}>
            <View style={styles.parentInfo}>
              <ParentBadge name={parent.name} color={parent.color} size="large" />
            </View>
            <View style={styles.parentActions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => onEdit(parent)}
              >
                <Text style={styles.editButtonText}>Edit</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionButton, styles.deleteActionButton]}
                onPress={() => handleDelete(parent)}
              >
                <Text style={styles.deleteButtonText}>Delete</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}
    </BaseModal>
  );
}

const styles = StyleSheet.create({
  emptyState: {
    paddingVertical: theme.spacing.xxl,
    alignItems: 'center',
  },
  emptyText: {
    ...theme.typography.textStyles.h3,
    color: theme.text.secondary,
    marginBottom: theme.spacing.sm,
  },
  emptySubtext: {
    ...theme.typography.textStyles.body,
    color: theme.text.tertiary,
  },
  parentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    backgroundColor: theme.background.elevated,
    marginBottom: theme.spacing.sm,
  },
  parentInfo: {
    flex: 1,
  },
  parentActions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  actionButton: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    backgroundColor: theme.button.primary.background,
  },
  editButtonText: {
    color: theme.button.primary.text,
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
  },
  deleteActionButton: {
    backgroundColor: theme.button.danger.background,
  },
  deleteButtonText: {
    color: theme.button.danger.text,
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
  },
});
