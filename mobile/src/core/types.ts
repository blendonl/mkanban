/**
 * Core type definitions for MKanban mobile app
 * Ported from Python: src/core/types/__init__.py
 */

// Type aliases matching Python implementation
export type ItemId = string;
export type ColumnId = string;
export type BoardId = string;
export type ParentId = string;
export type FilePath = string;
export type Timestamp = Date;

// Metadata type for YAML frontmatter
export type Metadata = {
  [key: string]: string | number | boolean | Array<any> | { [key: string]: any };
};

// Re-export enums
export { ParentColor } from './enums';
