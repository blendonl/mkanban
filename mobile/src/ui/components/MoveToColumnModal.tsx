import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { Column } from '../../domain/entities/Column';
import BaseModal from './BaseModal';
import theme from '../theme';

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
    <BaseModal
      visible={visible}
      onClose={onClose}
      title="Move to Column"
      scrollable
    >
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
            activeOpacity={theme.ui.PRESSED_OPACITY}
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
    </BaseModal>
  );
}

const styles = StyleSheet.create({
  columnOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.secondary,
  },
  currentColumnOption: {
    backgroundColor: theme.background.elevated,
  },
  columnInfo: {
    flex: 1,
  },
  columnName: {
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.text.primary,
    marginBottom: theme.spacing.xs,
  },
  currentColumnText: {
    color: theme.text.secondary,
  },
  columnCount: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.text.tertiary,
  },
  currentBadge: {
    ...theme.typography.textStyles.caption,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.accent.primary,
    backgroundColor: theme.background.elevated,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.badge,
  },
});
