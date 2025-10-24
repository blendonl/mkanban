import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ParentColor } from '../../core/enums';
import theme from '../theme';

interface ParentBadgeProps {
  name: string;
  color: ParentColor;
  size?: 'small' | 'medium' | 'large';
}

const COLOR_MAP: Record<ParentColor, string> = {
  [ParentColor.RED]: theme.parent.red,
  [ParentColor.ORANGE]: theme.parent.orange,
  [ParentColor.YELLOW]: theme.parent.yellow,
  [ParentColor.GREEN]: theme.parent.green,
  [ParentColor.BLUE]: theme.parent.blue,
  [ParentColor.CYAN]: theme.parent.cyan,
  [ParentColor.PURPLE]: theme.parent.purple,
};

const ParentBadge = React.memo<ParentBadgeProps>(({ name, color, size = 'medium' }) => {
  const backgroundColor = COLOR_MAP[color] || COLOR_MAP[ParentColor.BLUE];

  const sizeStyles = {
    small: styles.small,
    medium: styles.medium,
    large: styles.large,
  };

  const textSizeStyles = {
    small: styles.textSmall,
    medium: styles.textMedium,
    large: styles.textLarge,
  };

  return (
    <View style={[styles.badge, sizeStyles[size], { backgroundColor }]}>
      <Text style={[styles.text, textSizeStyles[size]]} numberOfLines={1}>
        {name}
      </Text>
    </View>
  );
});

ParentBadge.displayName = 'ParentBadge';

export default ParentBadge;

const styles = StyleSheet.create({
  badge: {
    borderRadius: theme.radius.badge,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
    alignSelf: 'flex-start',
  },
  small: {
    paddingHorizontal: theme.spacing.xs,
    paddingVertical: 2,
    borderRadius: theme.radius.sm,
  },
  medium: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.badge,
  },
  large: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.lg,
  },
  text: {
    color: theme.colors.white,
    fontWeight: theme.typography.fontWeights.semibold,
  },
  textSmall: {
    fontSize: theme.typography.fontSizes.xs,
  },
  textMedium: {
    fontSize: theme.typography.fontSizes.sm,
  },
  textLarge: {
    fontSize: theme.typography.fontSizes.base,
  },
});
