/**
 * useDebounce Hook
 * Debounces a value to prevent rapid updates
 */

import { useState, useEffect } from 'react';
import { uiConstants } from '../theme';

/**
 * Debounce a value
 * @param value - Value to debounce
 * @param delay - Delay in milliseconds (default: SEARCH_DEBOUNCE_TIME)
 * @returns Debounced value
 */
export function useDebounce<T>(
  value: T,
  delay: number = uiConstants.SEARCH_DEBOUNCE_TIME
): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;

// Usage example:
// const [searchTerm, setSearchTerm] = useState('');
// const debouncedSearchTerm = useDebounce(searchTerm, 300);
//
// useEffect(() => {
//   if (debouncedSearchTerm) {
//     performSearch(debouncedSearchTerm);
//   }
// }, [debouncedSearchTerm]);
