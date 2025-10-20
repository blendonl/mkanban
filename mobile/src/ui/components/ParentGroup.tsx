import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Item, Parent } from '../../domain/entities';
import ItemCard from './ItemCard';
import ParentBadge from './ParentBadge';
import theme from '../theme/colors';

interface ParentGroupProps {
  parent: Parent | null;
  items: Item[];
  onItemPress: (item: Item) => void;
  onItemLongPress?: (item: Item) => void;
}

export default function ParentGroup({
  parent,
  items,
  onItemPress,
  onItemLongPress,
}: ParentGroupProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        {parent ? (
          <ParentBadge name={parent.name} color={parent.color} size="medium" />
        ) : (
          <Text style={styles.ungroupedLabel}>No Parent</Text>
        )}
        <Text style={styles.count}>{items.length}</Text>
      </View>
      <View style={styles.items}>
        {items.map((item) => (
          <ItemCard
            key={item.id}
            item={item}
            parent={parent}
            onPress={() => onItemPress(item)}
            onLongPress={onItemLongPress ? () => onItemLongPress(item) : undefined}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
  },
  ungroupedLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text.secondary,
    fontStyle: 'italic',
  },
  count: {
    fontSize: 12,
    fontWeight: '600',
    color: theme.text.tertiary,
    backgroundColor: theme.background.elevated,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  items: {
    gap: 8,
  },
});
