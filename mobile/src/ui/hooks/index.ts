/**
 * Custom Hooks Index
 * Central export point for all custom hooks
 */

export { useLoadingState } from './useLoadingState';
export type { LoadingState, UseLoadingStateReturn } from './useLoadingState';

export { useDebounce } from './useDebounce';

// Re-export for convenience
export { default as useLoadingStateHook } from './useLoadingState';
export { default as useDebounceHook } from './useDebounce';
