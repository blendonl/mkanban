/**
 * Border radius system for consistent rounded corners
 */

export const radius = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 20,
  full: 9999, // For circular/pill shapes

  // Semantic radius
  button: 8,
  card: 12,
  input: 8,
  modal: 12,
  badge: 12,
  fab: 28, // Half of FAB_SIZE (56)
} as const;

export type Radius = typeof radius;

export default radius;
