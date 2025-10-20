import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ParentColor } from '../../core/enums';
import theme from '../theme/colors';

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
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  small: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  medium: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  large: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  text: {
    color: '#fff',
    fontWeight: '600',
  },
  textSmall: {
    fontSize: 10,
  },
  textMedium: {
    fontSize: 12,
  },
  textLarge: {
    fontSize: 14,
  },
});
