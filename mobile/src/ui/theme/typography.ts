/**
 * Typography system for consistent text styling
 */

export const fontSizes = {
  xs: 10,
  sm: 12,
  md: 13,
  base: 14,
  lg: 16,
  xl: 18,
  xxl: 20,
  xxxl: 24,
  display: 32,
} as const;

export const fontWeights = {
  light: '300',
  regular: '400',
  medium: '500',
  semibold: '600',
  bold: 'bold',
} as const;

export const lineHeights = {
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.75,
  loose: 2,
  // Specific line heights
  xs: 14,
  sm: 16,
  md: 18,
  base: 20,
  lg: 22,
  xl: 24,
  xxl: 28,
} as const;

/**
 * Predefined text styles for common use cases
 */
export const textStyles = {
  // Headings
  h1: {
    fontSize: fontSizes.xxxl,
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.xxl,
  },
  h2: {
    fontSize: fontSizes.xxl,
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.xl,
  },
  h3: {
    fontSize: fontSizes.xl,
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.lg,
  },
  h4: {
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.base,
  },

  // Body text
  body: {
    fontSize: fontSizes.base,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.base,
  },
  bodyLarge: {
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.lg,
  },
  bodySmall: {
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.sm,
  },

  // UI elements
  button: {
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.semibold,
  },
  caption: {
    fontSize: fontSizes.xs,
    fontWeight: fontWeights.medium,
  },
  label: {
    fontSize: fontSizes.base,
    fontWeight: fontWeights.semibold,
  },
} as const;

export const typography = {
  fontSizes,
  fontWeights,
  lineHeights,
  textStyles,
} as const;

export type Typography = typeof typography;

export default typography;
