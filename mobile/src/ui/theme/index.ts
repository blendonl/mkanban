/**
 * Unified theme system export
 * Central point for all theme-related imports
 */

import colors, { theme as colorTheme, CatppuccinColors } from './colors';
import spacing from './spacing';
import typography from './typography';
import radius from './radius';
import shadows from './shadows';
import uiConstants from './uiConstants';

/**
 * Complete theme object combining all design tokens
 */
export const theme = {
  // Colors (existing)
  ...colorTheme,

  // New design tokens
  spacing,
  typography,
  radius,
  shadows,
  ui: uiConstants,
} as const;

// Export individual modules for granular imports
export { colors, CatppuccinColors };
export { spacing };
export { typography };
export { radius };
export { shadows };
export { uiConstants };

// Export theme as default
export default theme;

// Type exports
export type Theme = typeof theme;
