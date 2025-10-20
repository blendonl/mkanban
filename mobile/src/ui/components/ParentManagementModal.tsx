import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { Parent } from '../../domain/entities';
import ParentBadge from './ParentBadge';
import theme from '../theme/colors';

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
    Alert.alert(
      'Delete Parent',
      `Are you sure you want to delete "${parent.name}"? Items assigned to this parent will not be deleted, but will lose their parent assignment.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => onDelete(parent.id),
        },
      ]
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <View style={styles.header}>
            <Text style={styles.title}>Manage Parents</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content}>
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
                      style={[styles.actionButton, styles.deleteButton]}
                      onPress={() => handleDelete(parent)}
                    >
                      <Text style={styles.deleteButtonText}>Delete</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            )}
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity style={styles.createButton} onPress={onCreate}>
              <Text style={styles.createButtonText}>+ Create Parent</Text>
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
    backgroundColor: theme.modal.overlay,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: theme.modal.background,
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
    borderBottomColor: theme.border.primary,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.text.primary,
  },
  closeButton: {
    padding: 4,
  },
  closeButtonText: {
    fontSize: 24,
    color: theme.text.secondary,
  },
  content: {
    padding: 16,
    maxHeight: 400,
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.text.secondary,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: theme.text.tertiary,
  },
  parentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    backgroundColor: theme.background.elevated,
    marginBottom: 8,
  },
  parentInfo: {
    flex: 1,
  },
  parentActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: theme.button.primary.background,
  },
  editButtonText: {
    color: theme.button.primary.text,
    fontSize: 14,
    fontWeight: '600',
  },
  deleteButton: {
    backgroundColor: theme.button.danger.background,
  },
  deleteButtonText: {
    color: theme.button.danger.text,
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: theme.border.primary,
  },
  createButton: {
    backgroundColor: theme.button.success.background,
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  createButtonText: {
    color: theme.button.success.text,
    fontSize: 16,
    fontWeight: '600',
  },
});
