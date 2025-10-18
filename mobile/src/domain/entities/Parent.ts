/**
 * Parent entity for grouping related items
 * Ported from Python: src/domain/entities/parent.py
 */

import { ParentId, Timestamp } from "../../core/types";
import { ParentColor } from "../../core/enums";
import { now } from "../../utils/dateUtils";

export interface ParentProps {
  id: ParentId;
  name: string;
  description?: string;
  color?: string;
  created_at?: Timestamp;
}

export class Parent {
  id: ParentId;
  name: string;
  description: string;
  color: string;
  created_at: Timestamp;

  constructor(props: ParentProps) {
    this.id = props.id;
    this.name = props.name;
    this.description = props.description || "";
    this.color = props.color || ParentColor.BLUE;
    this.created_at = props.created_at || now();
  }

  /**
   * Convert to plain object for serialization
   */
  toDict(): Record<string, any> {
    return {
      id: this.id,
      name: this.name,
      description: this.description,
      color: this.color,
      created_at: this.created_at,
    };
  }

  /**
   * Create Parent from plain object (deserialization)
   */
  static fromDict(data: Record<string, any>): Parent {
    return new Parent({
      id: data.id,
      name: data.name,
      description: data.description,
      color: data.color,
      created_at: data.created_at ? new Date(data.created_at) : undefined,
    });
  }
}
