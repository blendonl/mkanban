/**
 * Spacing system for consistent layout
 * Based on 4px base unit
 */

export const spacing = {
  // Base units
  none: 0,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 40,

  // Semantic spacing
  gutter: 16,
  cardPadding: 12,
  screenPadding: 16,
  sectionSpacing: 24,

  // Component-specific
  buttonPadding: {
    horizontal: 20,
    vertical: 12,
  },
  inputPadding: {
    horizontal: 12,
    vertical: 12,
  },
  modalPadding: {
    horizontal: 16,
    vertical: 16,
  },
} as const;

export type Spacing = typeof spacing;

export default spacing;
