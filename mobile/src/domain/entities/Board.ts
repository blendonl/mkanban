/**
 * Board entity representing a kanban board
 * Ported from Python: src/domain/entities/board.py
 */

import { BoardId, ColumnId, ParentId, Timestamp, FilePath } from "../../core/types";
import { now } from "../../utils/dateUtils";
import { generateIdFromName } from "../../utils/stringUtils";
import { Column } from "./Column";
import { Item } from "./Item";
import { Parent } from "./Parent";

export interface BoardProps {
  id?: BoardId;
  name: string;
  description?: string;
  file_path?: FilePath | null;
  columns?: Column[];
  parents?: Parent[];
  created_at?: Timestamp;
}

export class Board {
  id: BoardId;
  name: string;
  description: string;
  file_path: FilePath | null;
  columns: Column[];
  parents: Parent[];
  created_at: Timestamp;

  constructor(props: BoardProps) {
    this.name = props.name;
    this.description = props.description || "";
    this.file_path = props.file_path !== undefined ? props.file_path : null;
    this.columns = props.columns || [];
    this.parents = props.parents || [];
    this.created_at = props.created_at || now();

    // Auto-generate ID if not provided
    if (props.id) {
      this.id = props.id;
    } else if (this.file_path) {
      // Extract ID from file path (directory name)
      const pathParts = this.file_path.split("/");
      const dirName = pathParts[pathParts.length - 2] || pathParts[pathParts.length - 1];
      this.id = dirName;
      if (!this.name || this.name === dirName) {
        this.name = dirName;
      }
    } else {
      this.id = generateIdFromName(this.name) || "unnamed_board";
    }
  }

  /**
   * Update board properties
   */
  update(updates: Partial<BoardProps>): void {
    Object.assign(this, updates);
  }

  /**
   * Add a new column to the board
   */
  addColumn(name: string, position?: number | null): Column {
    const columnPosition = position !== undefined && position !== null ? position : this.columns.length;

    const column = new Column({ name, position: columnPosition });
    this.columns.push(column);

    // Sort columns by position, then name
    this.columns.sort((a, b) => {
      if (a.position !== b.position) {
        return a.position - b.position;
      }
      return a.name.localeCompare(b.name);
    });

    return column;
  }

  /**
   * Remove a column from the board
   */
  removeColumn(columnId: ColumnId): boolean {
    const originalCount = this.columns.length;
    this.columns = this.columns.filter((col) => col.id !== columnId);
    return this.columns.length < originalCount;
  }

  /**
   * Get a column by its ID
   */
  getColumnById(columnId: ColumnId): Column | null {
    return this.columns.find((col) => col.id === columnId) || null;
  }

  /**
   * Get the first column (by position)
   */
  getFirstColumn(): Column | null {
    if (this.columns.length === 0) {
      return null;
    }
    return this.columns.reduce((min, col) => (col.position < min.position ? col : min));
  }

  /**
   * Get all items that don't have a parent
   */
  getOrphanedItems(): Item[] {
    const items: Item[] = [];
    for (const column of this.columns) {
      items.push(...column.items.filter((item) => item.parent_id === null));
    }
    return items;
  }

  /**
   * Add a new parent to the board
   */
  addParent(name: string, color: string = "blue"): Parent {
    const parent = new Parent({
      id: generateIdFromName(name),
      name,
      color,
    });
    this.parents.push(parent);
    return parent;
  }

  /**
   * Remove a parent from the board
   */
  removeParent(parentId: ParentId): boolean {
    const originalCount = this.parents.length;
    this.parents = this.parents.filter((parent) => parent.id !== parentId);
    return this.parents.length < originalCount;
  }

  /**
   * Get a parent by its ID
   */
  getParentById(parentId: ParentId): Parent | null {
    return this.parents.find((parent) => parent.id === parentId) || null;
  }

  /**
   * Convert to plain object for serialization
   */
  toDict(): Record<string, any> {
    return {
      id: this.id,
      name: this.name,
      description: this.description,
      created_at: this.created_at,
    };
  }

  /**
   * Create Board from plain object (deserialization)
   */
  static fromDict(data: Record<string, any>): Board {
    return new Board({
      id: data.id,
      name: data.name,
      description: data.description,
      created_at: data.created_at ? new Date(data.created_at) : undefined,
      file_path: data.file_path,
    });
  }
}
