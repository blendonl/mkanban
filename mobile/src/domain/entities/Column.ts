/**
 * Column entity for organizing items in a kanban board
 * Ported from Python: src/domain/entities/column.py
 */

import { ColumnId, ParentId, Timestamp, FilePath } from "../../core/types";
import { now } from "../../utils/dateUtils";
import { generateIdFromName } from "../../utils/stringUtils";
import { Item } from "./Item";

export interface ColumnProps {
  id?: ColumnId;
  name: string;
  position?: number;
  limit?: number | null;
  created_at?: Timestamp;
  items?: Item[];
  file_path?: FilePath | null;
}

export class Column {
  id: ColumnId;
  name: string;
  position: number;
  limit: number | null;
  created_at: Timestamp;
  items: Item[];
  file_path: FilePath | null;

  constructor(props: ColumnProps) {
    this.name = props.name;
    this.position = props.position || 0;
    this.limit = props.limit !== undefined ? props.limit : null;
    this.created_at = props.created_at || now();
    this.items = props.items || [];
    this.file_path = props.file_path !== undefined ? props.file_path : null;

    // Auto-generate ID if not provided
    if (props.id) {
      this.id = props.id;
    } else if (this.file_path) {
      // Extract ID from file path (directory name)
      const pathParts = this.file_path.split("/");
      const dirName = pathParts[pathParts.length - 2] || pathParts[pathParts.length - 1];
      this.id = dirName;
      if (!this.name || this.name === dirName) {
        this.name = dirName.replace(/-/g, " ").replace(/_/g, " ");
        this.name = this.name
          .split(" ")
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
          .join(" ");
      }
    } else {
      this.id = generateIdFromName(this.name) || "unnamed_column";
    }
  }

  /**
   * Update column properties
   */
  update(updates: Partial<ColumnProps>): void {
    Object.assign(this, updates);
  }

  /**
   * Add a new item to the column
   */
  addItem(title: string, parentId?: ParentId | null, itemId?: string): Item {
    const item = new Item({
      id: itemId || "",
      title,
      parent_id: parentId,
      column_id: this.id,
    });
    this.items.push(item);
    return item;
  }

  /**
   * Move an existing item to the end of this column
   */
  moveItemToEnd(item: Item): boolean {
    item.moveToColumn(this.id);
    this.items.push(item);
    return true;
  }

  /**
   * Remove an item from the column
   */
  removeItem(itemId: string): boolean {
    const originalCount = this.items.length;
    this.items = this.items.filter((item) => item.id !== itemId);
    return this.items.length < originalCount;
  }

  /**
   * Get all items in the column
   */
  getAllItems(): Item[] {
    return this.items;
  }

  /**
   * Find an item by ID
   */
  getItemById(itemId: string): Item | null {
    return this.items.find((item) => item.id === itemId) || null;
  }

  /**
   * Convert to plain object for serialization
   */
  toDict(): Record<string, any> {
    return {
      id: this.id,
      name: this.name,
      position: this.position,
      limit: this.limit,
      created_at: this.created_at,
    };
  }

  /**
   * Create Column from plain object (deserialization)
   */
  static fromDict(data: Record<string, any>): Column {
    return new Column({
      id: data.id,
      name: data.name,
      position: data.position,
      limit: data.limit,
      created_at: data.created_at ? new Date(data.created_at) : undefined,
      file_path: data.file_path,
    });
  }
}
