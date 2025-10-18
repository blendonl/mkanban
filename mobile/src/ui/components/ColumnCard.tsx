import React, { useMemo, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ListRenderItem } from 'react-native';
import { Column } from '../../domain/entities/Column';
import { Item } from '../../domain/entities/Item';
import { Parent } from '../../domain/entities/Parent';
import ItemCard from './ItemCard';
import ParentGroup from './ParentGroup';

// Type for grouped items with parent
interface GroupedItemsData {
  type: 'group';
  parentId: string | null;
  parent: Parent | null;
  items: Item[];
}

// Type for individual item
interface FlatItemData {
  type: 'item';
  item: Item;
  parent?: Parent;
}

interface ColumnCardProps {
  column: Column;
  parents: Parent[];
  showParentGroups?: boolean;
  onItemPress: (item: Item) => void;
  onItemLongPress?: (item: Item) => void;
  onAddItem: () => void;
}

const ColumnCard = React.memo<ColumnCardProps>(({
  column,
  parents,
  showParentGroups = false,
  onItemPress,
  onItemLongPress,
  onAddItem,
}) => {
  // Create a map of parent IDs to Parent objects for quick lookup
  const parentMap = useMemo(() => {
    const map = new Map<string, Parent>();
    parents.forEach((parent) => {
      map.set(parent.id, parent);
    });
    return map;
  }, [parents]);

  // Prepare data for FlatList based on view mode
  const listData = useMemo((): (GroupedItemsData | FlatItemData)[] => {
    if (showParentGroups) {
      // Group items by parent
      const groups = new Map<string | null, Item[]>();

      column.items.forEach((item) => {
        const parentId = item.parent_id || null;
        if (!groups.has(parentId)) {
          groups.set(parentId, []);
        }
        groups.get(parentId)!.push(item);
      });

      // Convert groups to array for FlatList
      return Array.from(groups.entries()).map(([parentId, items]) => ({
        type: 'group' as const,
        parentId,
        parent: parentId ? parentMap.get(parentId) || null : null,
        items,
      }));
    } else {
      // Flat view: convert items to FlatItemData
      return column.items.map((item) => ({
        type: 'item' as const,
        item,
        parent: item.parent_id ? parentMap.get(item.parent_id) : undefined,
      }));
    }
  }, [column.items, showParentGroups, parentMap]);

  // Render function for FlatList items
  const renderItem: ListRenderItem<GroupedItemsData | FlatItemData> = useCallback(
    ({ item: data }) => {
      if (data.type === 'group') {
        return (
          <ParentGroup
            parent={data.parent}
            items={data.items}
            onItemPress={onItemPress}
            onItemLongPress={onItemLongPress}
          />
        );
      } else {
        return (
          <ItemCard
            item={data.item}
            parent={data.parent}
            onPress={() => onItemPress(data.item)}
            onLongPress={onItemLongPress ? () => onItemLongPress(data.item) : undefined}
          />
        );
      }
    },
    [onItemPress, onItemLongPress]
  );

  // Key extractor for FlatList
  const keyExtractor = useCallback(
    (item: GroupedItemsData | FlatItemData, index: number) => {
      if (item.type === 'group') {
        return `group-${item.parentId || 'no-parent'}`;
      } else {
        return `item-${item.item.id}`;
      }
    },
    []
  );

  // Empty component
  const renderEmpty = useCallback(
    () => (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No items yet</Text>
      </View>
    ),
    []
  );

  // Footer component with Add Item button
  const renderFooter = useCallback(
    () => (
      <TouchableOpacity style={styles.addButton} onPress={onAddItem}>
        <Text style={styles.addButtonText}>+ Add Item</Text>
      </TouchableOpacity>
    ),
    [onAddItem]
  );

  return (
    <View style={styles.container}>
      {/* Column Header */}
      <View style={styles.header}>
        <Text style={styles.title}>{column.name}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{column.items.length}</Text>
        </View>
      </View>

      {/* Items List with Virtualization */}
      <FlatList
        data={listData}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={renderFooter}
        style={styles.itemsContainer}
        contentContainerStyle={styles.itemsContent}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={5}
        initialNumToRender={10}
      />
    </View>
  );
});

ColumnCard.displayName = 'ColumnCard';

export default ColumnCard;

const styles = StyleSheet.create({
  container: {
    width: 280,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    marginHorizontal: 8,
    padding: 12,
    maxHeight: '100%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 2,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  badge: {
    backgroundColor: '#2563eb',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  itemsContainer: {
    flex: 1,
  },
  itemsContent: {
    paddingBottom: 8,
  },
  emptyContainer: {
    padding: 16,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#9ca3af',
    fontStyle: 'italic',
  },
  addButton: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 4,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderStyle: 'dashed',
  },
  addButtonText: {
    color: '#2563eb',
    fontSize: 14,
    fontWeight: '600',
  },
});
