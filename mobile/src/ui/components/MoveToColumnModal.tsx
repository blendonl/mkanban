import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
} from 'react-native';
import { Column } from '../../domain/entities/Column';
import theme from '../theme/colors';

interface MoveToColumnModalProps {
  visible: boolean;
  columns: Column[];
  currentColumnId: string;
  onSelectColumn: (columnId: string) => void;
  onClose: () => void;
}

export default function MoveToColumnModal({
  visible,
  columns,
  currentColumnId,
  onSelectColumn,
  onClose,
}: MoveToColumnModalProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          <View style={styles.header}>
            <Text style={styles.title}>Move to Column</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollView}>
            {columns.map((column) => {
              const isCurrent = column.id === currentColumnId;
              return (
                <TouchableOpacity
                  key={column.id}
                  style={[
                    styles.columnOption,
                    isCurrent && styles.currentColumnOption,
                  ]}
                  onPress={() => {
                    if (!isCurrent) {
                      onSelectColumn(column.id);
                    }
                  }}
                  disabled={isCurrent}
                >
                  <View style={styles.columnInfo}>
                    <Text
                      style={[
                        styles.columnName,
                        isCurrent && styles.currentColumnText,
                      ]}
                    >
                      {column.name}
                    </Text>
                    <Text style={styles.columnCount}>
                      {column.items.length} items
                    </Text>
                  </View>
                  {isCurrent && (
                    <Text style={styles.currentBadge}>Current</Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
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
    padding: 20,
  },
  modalContainer: {
    backgroundColor: theme.modal.background,
    borderRadius: 12,
    width: '100%',
    maxWidth: 400,
    maxHeight: '70%',
    shadowColor: theme.card.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
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
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.text.primary,
  },
  closeButton: {
    fontSize: 24,
    color: theme.text.secondary,
    fontWeight: '300',
  },
  scrollView: {
    maxHeight: 400,
  },
  columnOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.background.elevated,
  },
  currentColumnOption: {
    backgroundColor: theme.background.elevated,
  },
  columnInfo: {
    flex: 1,
  },
  columnName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text.primary,
    marginBottom: 4,
  },
  currentColumnText: {
    color: theme.text.secondary,
  },
  columnCount: {
    fontSize: 13,
    color: theme.text.tertiary,
  },
  currentBadge: {
    fontSize: 12,
    fontWeight: '600',
    color: theme.accent.primary,
    backgroundColor: theme.background.elevated,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
});
