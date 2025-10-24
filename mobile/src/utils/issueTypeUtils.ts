/**
 * Issue type utilities
 * Centralized logic for issue types and their icons
 */

import { IssueType } from '../core/enums';

/**
 * Mapping of issue types to their emoji icons
 */
export const ISSUE_TYPE_ICONS: Record<string, string> = {
  [IssueType.EPIC]: '📚',
  [IssueType.STORY]: '📖',
  [IssueType.BUG]: '🐛',
  [IssueType.SUBTASK]: '☑️',
  [IssueType.TASK]: '📋',
  // Fallback for unknown types
  default: '📄',
} as const;

/**
 * Get the icon for a specific issue type
 * Handles case-insensitive matching and partial matches
 * @param issueType - The issue type string
 * @returns The corresponding emoji icon
 */
export function getIssueTypeIcon(issueType: string): string {
  if (!issueType) {
    return ISSUE_TYPE_ICONS.default;
  }

  const normalizedType = issueType.toLowerCase();

  // Check for exact matches first
  for (const [type, icon] of Object.entries(ISSUE_TYPE_ICONS)) {
    if (type.toLowerCase() === normalizedType) {
      return icon;
    }
  }

  // Check for partial matches
  if (normalizedType.includes('epic')) {
    return ISSUE_TYPE_ICONS[IssueType.EPIC];
  } else if (normalizedType.includes('story')) {
    return ISSUE_TYPE_ICONS[IssueType.STORY];
  } else if (normalizedType.includes('bug')) {
    return ISSUE_TYPE_ICONS[IssueType.BUG];
  } else if (normalizedType.includes('subtask')) {
    return ISSUE_TYPE_ICONS[IssueType.SUBTASK];
  } else if (normalizedType.includes('task')) {
    return ISSUE_TYPE_ICONS[IssueType.TASK];
  }

  return ISSUE_TYPE_ICONS.default;
}

/**
 * Get all available issue types
 * @returns Array of all issue type values
 */
export function getAllIssueTypes(): string[] {
  return [
    IssueType.TASK,
    IssueType.STORY,
    IssueType.BUG,
    IssueType.EPIC,
    IssueType.SUBTASK,
  ];
}

/**
 * Check if a string is a valid issue type
 * @param issueType - The string to check
 * @returns True if the string is a valid issue type
 */
export function isValidIssueType(issueType: string): boolean {
  return getAllIssueTypes().includes(issueType);
}

/**
 * Get a human-readable label for an issue type
 * @param issueType - The issue type
 * @returns Formatted label with icon
 */
export function getIssueTypeLabel(issueType: string): string {
  const icon = getIssueTypeIcon(issueType);
  return `${icon} ${issueType}`;
}
