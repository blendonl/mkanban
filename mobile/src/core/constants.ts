/**
 * Application constants for MKanban mobile app
 * Ported from Python: src/core/constants.py
 */

// File structure constants
export const BOARD_FILENAME = "kanban.md";
export const COLUMN_METADATA_FILENAME = "column.md";

// Default column names
export const DEFAULT_COLUMN_NAMES = ["to-do", "in-progress", "done"];

// Default parent color
export const DEFAULT_PARENT_COLOR = "blue";

// Item ID prefix length for board prefix generation
export const BOARD_PREFIX_LENGTH = 3;

// Default file extension for items
export const ITEM_FILE_EXTENSION = ".md";

// Default issue type for manually created items
export const DEFAULT_ISSUE_TYPE = "Task";

// Column normalization - map various spellings to standard IDs
export const COLUMN_ID_MAPPINGS: { [key: string]: string } = {
  "to-do": "to-do",
  "todo": "to-do",
  "to_do": "to-do",
  "in-progress": "in-progress",
  "inprogress": "in-progress",
  "in_progress": "in-progress",
  "done": "done",
  "completed": "done",
};
