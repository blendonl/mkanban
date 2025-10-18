/**
 * Item entity representing a task/item in a kanban column
 * Ported from Python: src/domain/entities/item.py
 * MVP version: Git and JIRA fields excluded
 */

import { ItemId, ColumnId, ParentId, Timestamp, FilePath, Metadata } from "../../core/types";
import { now } from "../../utils/dateUtils";
import { generateIdFromName, getSafeFilename } from "../../utils/stringUtils";

export interface ItemProps {
  id?: ItemId;
  title: string;
  column_id: ColumnId;
  description?: string;
  parent_id?: ParentId | null;
  created_at?: Timestamp;
  moved_in_progress_at?: Timestamp | null;
  moved_in_done_at?: Timestamp | null;
  worked_on_for?: string | null;
  file_path?: FilePath | null;
  metadata?: Metadata;
}

export class Item {
  id: ItemId;
  title: string;
  column_id: ColumnId;
  description: string;
  parent_id: ParentId | null;
  created_at: Timestamp;
  moved_in_progress_at: Timestamp | null;
  moved_in_done_at: Timestamp | null;
  worked_on_for: string | null; // Format: "HH:MM"
  file_path: FilePath | null;
  metadata: Metadata;

  constructor(props: ItemProps) {
    this.title = props.title;
    this.column_id = props.column_id;
    this.description = props.description || "";
    this.parent_id = props.parent_id !== undefined ? props.parent_id : null;
    this.created_at = props.created_at || now();
    this.moved_in_progress_at = props.moved_in_progress_at !== undefined ? props.moved_in_progress_at : null;
    this.moved_in_done_at = props.moved_in_done_at !== undefined ? props.moved_in_done_at : null;
    this.worked_on_for = props.worked_on_for !== undefined ? props.worked_on_for : null;
    this.file_path = props.file_path !== undefined ? props.file_path : null;
    this.metadata = props.metadata || {};

    // Auto-generate ID if not provided
    if (props.id) {
      this.id = props.id;
    } else if (this.file_path) {
      // Extract ID from filename
      const filename = this.file_path.split("/").pop() || "";
      const stem = filename.replace(/\.md$/, "");

      // Try to extract ID prefix (e.g., "REC-27-fix-bug" -> "REC-27")
      const parts = stem.split("-");
      if (parts.length >= 2 && /^\d+$/.test(parts[1])) {
        this.id = `${parts[0]}-${parts[1]}`;
      } else {
        this.id = stem;
      }

      if (!this.title || this.title === stem) {
        this.title = stem;
      }
    } else {
      // Manual items will have ID set by ItemService with board context
      this.id = generateIdFromName(this.title) || "unnamed_item";
    }
  }

  /**
   * Update item properties
   * Protected fields (timing) cannot be manually updated
   */
  update(updates: Partial<ItemProps>): void {
    const protectedFields = new Set(["moved_in_progress_at", "moved_in_done_at", "worked_on_for"]);

    Object.entries(updates).forEach(([key, value]) => {
      if (!protectedFields.has(key)) {
        (this as any)[key] = value;
      }
    });
  }

  /**
   * Move item to a different column
   * Automatically tracks timestamps for in-progress and done columns
   */
  moveToColumn(columnId: ColumnId): void {
    const oldColumnId = this.column_id;
    this.column_id = columnId;

    // Normalize column IDs for comparison (handle both hyphen and underscore)
    const normalizedColumnId = columnId.replace(/_/g, "-");
    const normalizedOldColumnId = oldColumnId ? oldColumnId.replace(/_/g, "-") : null;

    // Track when item moves to in-progress
    if (normalizedColumnId === "in-progress" && normalizedOldColumnId !== "in-progress") {
      this.moved_in_progress_at = now();
    }

    // Track when item moves to done and calculate work duration
    if (normalizedColumnId === "done" && normalizedOldColumnId !== "done") {
      this.moved_in_done_at = now();

      // Calculate worked_on_for if item was previously in progress
      if (this.moved_in_progress_at) {
        this.worked_on_for = this._calculateWorkDuration(
          this.moved_in_progress_at,
          this.moved_in_done_at
        );
      }
    }
  }

  /**
   * Set or clear the parent ID
   */
  setParent(parentId: ParentId | null): void {
    this.parent_id = parentId;
  }

  /**
   * Check if item has a parent
   */
  get hasParent(): boolean {
    return this.parent_id !== null;
  }

  /**
   * Get the issue type from metadata, defaults to "Task"
   */
  getIssueType(): string {
    return this.metadata.issue_type || "Task";
  }

  /**
   * Set the issue type in metadata
   */
  setIssueType(issueType: string): void {
    this.metadata.issue_type = issueType;
  }

  /**
   * Get the icon for the current issue type
   */
  getIssueTypeIcon(): string {
    const issueType = this.getIssueType().toLowerCase();

    if (issueType.includes("epic")) {
      return "📚";
    } else if (issueType.includes("story")) {
      return "📖";
    } else if (issueType.includes("bug")) {
      return "🐛";
    } else if (issueType.includes("subtask")) {
      return "☑️";
    } else if (issueType.includes("task")) {
      return "📋";
    }
    return "📄";
  }

  /**
   * Calculate work duration in HH:MM format
   */
  private _calculateWorkDuration(startTime: Timestamp, endTime: Timestamp): string | null {
    try {
      const start = startTime instanceof Date ? startTime : new Date(startTime);
      const end = endTime instanceof Date ? endTime : new Date(endTime);

      const durationMs = end.getTime() - start.getTime();
      const totalMinutes = Math.floor(durationMs / (1000 * 60));
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;

      return `${hours}:${minutes.toString().padStart(2, "0")}`;
    } catch {
      return null;
    }
  }

  /**
   * Convert to plain object for serialization
   */
  toDict(): Record<string, any> {
    const result: Record<string, any> = {
      id: this.id,
      title: this.title,
      column_id: this.column_id,
      description: this.description,
      parent_id: this.parent_id,
      created_at: this.created_at,
      moved_in_progress_at: this.moved_in_progress_at,
      moved_in_done_at: this.moved_in_done_at,
      worked_on_for: this.worked_on_for,
    };

    // Add metadata if present
    if (Object.keys(this.metadata).length > 0) {
      result.metadata = this.metadata;
    }

    return result;
  }

  /**
   * Create Item from plain object (deserialization)
   */
  static fromDict(data: Record<string, any>): Item {
    return new Item({
      id: data.id,
      title: data.title,
      column_id: data.column_id,
      description: data.description,
      parent_id: data.parent_id,
      created_at: data.created_at ? new Date(data.created_at) : undefined,
      moved_in_progress_at: data.moved_in_progress_at ? new Date(data.moved_in_progress_at) : null,
      moved_in_done_at: data.moved_in_done_at ? new Date(data.moved_in_done_at) : null,
      worked_on_for: data.worked_on_for,
      file_path: data.file_path,
      metadata: data.metadata || {},
    });
  }
}
