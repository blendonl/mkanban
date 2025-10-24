/**
 * Shadow system for consistent elevation
 * Handles platform differences between iOS and Android
 */

import { Platform, ViewStyle } from 'react-native';

/**
 * Create a shadow style object that works on both iOS and Android
 * @param elevation - Android elevation value
 * @param shadowColor - Shadow color (default: black)
 * @param shadowOffset - iOS shadow offset
 * @param shadowOpacity - iOS shadow opacity
 * @param shadowRadius - iOS shadow blur radius
 */
const createShadow = (
  elevation: number,
  shadowColor: string = '#000000',
  shadowOffset: { width: number; height: number } = { width: 0, height: 2 },
  shadowOpacity: number = 0.1,
  shadowRadius: number = 4
): ViewStyle => {
  if (Platform.OS === 'android') {
    return {
      elevation,
    };
  }

  return {
    shadowColor,
    shadowOffset,
    shadowOpacity,
    shadowRadius,
  };
};

export const shadows = {
  none: createShadow(0, '#000000', { width: 0, height: 0 }, 0, 0),

  sm: createShadow(1, '#000000', { width: 0, height: 1 }, 0.05, 2),

  md: createShadow(2, '#000000', { width: 0, height: 2 }, 0.1, 4),

  lg: createShadow(4, '#000000', { width: 0, height: 4 }, 0.15, 6),

  xl: createShadow(8, '#000000', { width: 0, height: 8 }, 0.2, 12),

  // Semantic shadows
  card: createShadow(2, '#000000', { width: 0, height: 2 }, 0.1, 4),

  modal: createShadow(8, '#000000', { width: 0, height: 4 }, 0.2, 8),

  fab: createShadow(8, '#000000', { width: 0, height: 4 }, 0.3, 4),

  button: createShadow(2, '#000000', { width: 0, height: 2 }, 0.1, 3),
} as const;

export type Shadows = typeof shadows;

export default shadows;
