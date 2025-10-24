/**
 * useLoadingState Hook
 * Shared state management for loading, error, and data states
 */

import { useState, useCallback } from 'react';

export interface LoadingState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export interface UseLoadingStateReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  setData: (data: T | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: Error | null) => void;
  reset: () => void;
  executeAsync: (asyncFn: () => Promise<T>) => Promise<T | null>;
}

/**
 * Custom hook for managing loading, error, and data states
 * @param initialData - Initial data value
 * @returns Object containing state and state management functions
 */
export function useLoadingState<T>(
  initialData: T | null = null
): UseLoadingStateReturn<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Reset all states to initial values
   */
  const reset = useCallback(() => {
    setData(initialData);
    setLoading(false);
    setError(null);
  }, [initialData]);

  /**
   * Execute an async function and manage loading/error states automatically
   * @param asyncFn - Async function to execute
   * @returns Promise resolving to the data or null on error
   */
  const executeAsync = useCallback(async (asyncFn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await asyncFn();
      setData(result);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      setLoading(false);
      return null;
    }
  }, []);

  return {
    data,
    loading,
    error,
    setData,
    setLoading,
    setError,
    reset,
    executeAsync,
  };
}

export default useLoadingState;

// Usage example:
// const { data, loading, error, executeAsync } = useLoadingState<Board>();
//
// useEffect(() => {
//   executeAsync(() => boardService.getBoardById(boardId));
// }, [boardId]);
