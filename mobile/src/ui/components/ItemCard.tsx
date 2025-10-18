import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Item } from '../../domain/entities/Item';
import { Parent } from '../../domain/entities/Parent';
import ParentBadge from './ParentBadge';

interface ItemCardProps {
  item: Item;
  parent?: Parent;
  onPress: () => void;
  onLongPress?: () => void;
}

const ISSUE_TYPE_ICONS: Record<string, string> = {
  Task: '📋',
  Story: '📖',
  Bug: '🐛',
  Epic: '📚',
  Subtask: '☑️',
};

const ItemCard = React.memo<ItemCardProps>(({ item, parent, onPress, onLongPress }) => {
  // Use the helper method to get icon directly from Item entity
  const icon = item.getIssueTypeIcon();

  // Extract description preview (first 100 characters)
  const descriptionPreview = item.description
    ? item.description.length > 100
      ? `${item.description.substring(0, 100)}...`
      : item.description
    : '';

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      onLongPress={onLongPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.icon}>{icon}</Text>
        <Text style={styles.title} numberOfLines={2}>
          {item.title}
        </Text>
      </View>

      {parent && (
        <View style={styles.parentContainer}>
          <ParentBadge name={parent.name} color={parent.color} size="small" />
        </View>
      )}

      {descriptionPreview && (
        <Text style={styles.description} numberOfLines={3}>
          {descriptionPreview}
        </Text>
      )}

      {item.id && (
        <Text style={styles.itemId}>{item.id}</Text>
      )}
    </TouchableOpacity>
  );
});

ItemCard.displayName = 'ItemCard';

export default ItemCard;

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  icon: {
    fontSize: 16,
    marginRight: 6,
    marginTop: 2,
  },
  title: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    lineHeight: 20,
  },
  parentContainer: {
    marginBottom: 8,
  },
  description: {
    fontSize: 12,
    color: '#6b7280',
    lineHeight: 18,
    marginBottom: 6,
  },
  itemId: {
    fontSize: 10,
    color: '#9ca3af',
    fontWeight: '500',
  },
});
