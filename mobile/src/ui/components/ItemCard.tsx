import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Item } from '../../domain/entities/Item';
import { Parent } from '../../domain/entities/Parent';
import ParentBadge from './ParentBadge';
import theme from '../theme';
import { getIssueTypeIcon } from '../../utils/issueTypeUtils';
import { uiConstants } from '../theme';

interface ItemCardProps {
  item: Item;
  parent?: Parent;
  onPress: () => void;
  onLongPress?: () => void;
}

const ItemCard = React.memo<ItemCardProps>(({ item, parent, onPress, onLongPress }) => {
  // Use centralized issue type utility
  const icon = getIssueTypeIcon(item.getIssueType());

  // Extract description preview
  const descriptionPreview = item.description
    ? item.description.length > uiConstants.DESCRIPTION_PREVIEW_LENGTH
      ? `${item.description.substring(0, uiConstants.DESCRIPTION_PREVIEW_LENGTH)}...`
      : item.description
    : '';

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      onLongPress={onLongPress}
      activeOpacity={theme.ui.PRESSED_OPACITY}
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
    backgroundColor: theme.card.background,
    borderRadius: theme.radius.card,
    padding: theme.spacing.cardPadding,
    marginBottom: theme.spacing.sm,
    borderWidth: 1,
    borderColor: theme.card.border,
    ...theme.shadows.card,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: theme.spacing.sm,
  },
  icon: {
    fontSize: theme.typography.fontSizes.lg,
    marginRight: theme.spacing.sm,
    marginTop: 2,
  },
  title: {
    flex: 1,
    ...theme.typography.textStyles.body,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.text.primary,
  },
  parentContainer: {
    marginBottom: theme.spacing.sm,
  },
  description: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.text.secondary,
    marginBottom: theme.spacing.sm,
  },
  itemId: {
    ...theme.typography.textStyles.caption,
    color: theme.text.tertiary,
  },
});
