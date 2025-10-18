/**
 * Date utility functions for MKanban mobile app
 * Ported from Python: src/utils/date_utils.py
 */

/**
 * Get current timestamp as Date object
 */
export function now(): Date {
  return new Date();
}

/**
 * Format a Date object to ISO string for YAML frontmatter
 * Uses ISO 8601 format: 2025-01-15T10:30:00Z
 */
export function formatTimestamp(timestamp: Date): string {
  return timestamp.toISOString();
}

/**
 * Parse a timestamp string to Date object
 * Supports ISO format and falls back to current time on error
 */
export function parseTimestamp(timestampStr: string): Date {
  try {
    const parsed = new Date(timestampStr);
    // Check if valid date
    if (isNaN(parsed.getTime())) {
      return now();
    }
    return parsed;
  } catch {
    return now();
  }
}

/**
 * Ensure a value is a Date object
 * Converts string to Date, returns current time for null/undefined
 */
export function ensureDateTime(value: Date | string | null | undefined): Date {
  if (value === null || value === undefined) {
    return now();
  }
  if (typeof value === "string") {
    return parseTimestamp(value);
  }
  return value;
}
