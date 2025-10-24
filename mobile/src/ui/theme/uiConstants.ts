/**
 * UI-specific constants
 * Centralized values for component dimensions and limits
 */

export const uiConstants = {
  // Component dimensions
  DEFAULT_COLUMN_WIDTH: 280,
  MIN_COLUMN_WIDTH: 200,
  MAX_COLUMN_WIDTH: 400,

  FAB_SIZE: 56,
  HEADER_BUTTON_SIZE: 44,
  BADGE_MIN_WIDTH: 24,

  // Text limits
  DESCRIPTION_PREVIEW_LENGTH: 100,
  PARENT_NAME_MAX_LENGTH: 100,
  BOARD_NAME_MAX_LENGTH: 200,
  ITEM_TITLE_MAX_LENGTH: 500,

  // List configuration
  FLATLIST_INITIAL_NUM_TO_RENDER: 10,
  FLATLIST_MAX_TO_RENDER_PER_BATCH: 10,
  FLATLIST_WINDOW_SIZE: 5,

  // Animation durations (ms)
  ANIMATION_DURATION_SHORT: 200,
  ANIMATION_DURATION_MEDIUM: 300,
  ANIMATION_DURATION_LONG: 500,

  // Modal dimensions
  MODAL_WIDTH_PERCENTAGE: 0.9, // 90% of screen width
  MODAL_MAX_HEIGHT_PERCENTAGE: 0.8, // 80% of screen height
  PICKER_MAX_HEIGHT: 400,

  // Opacity values
  DISABLED_OPACITY: 0.5,
  PRESSED_OPACITY: 0.7,
  OVERLAY_OPACITY: 0.7,

  // Debounce/throttle times (ms)
  SEARCH_DEBOUNCE_TIME: 300,
  SCROLL_THROTTLE_TIME: 16, // ~60fps
  AUTO_SAVE_DEBOUNCE_TIME: 1000,
} as const;

export type UIConstants = typeof uiConstants;

export default uiConstants;
