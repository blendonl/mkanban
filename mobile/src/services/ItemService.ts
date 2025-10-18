/**
 * ItemService handles business logic for item operations
 * Ported from Python: src/services/item_service.py
 */

import { Board } from '../domain/entities/Board';
import { Item } from '../domain/entities/Item';
import { StorageRepository } from '../domain/repositories/StorageRepository';
import { ValidationService } from './ValidationService';
import { ItemId, ColumnId, ParentId } from '../core/types';
import {
  ItemNotFoundError,
  ColumnNotFoundError,
  ValidationError,
} from '../core/exceptions';
import { generateManualItemId, getBoardPrefix } from '../utils/stringUtils';
import { DEFAULT_ISSUE_TYPE } from '../core/constants';

export class ItemService {
  private storage: StorageRepository;
  private validator: ValidationService;

  constructor(storage: StorageRepository, validator: ValidationService) {
    this.storage = storage;
    this.validator = validator;
  }

  /**
   * Create a new item in a column
   * @throws {ColumnNotFoundError} if column not found
   * @throws {ValidationError} if validation fails or column at capacity
   */
  async createItem(
    board: Board,
    columnId: ColumnId,
    title: string,
    description: string = '',
    parentId?: ParentId | null
  ): Promise<Item> {
    console.info(`[ItemService] Creating item: ${title} in board: ${board.name}`);
    this.validator.validateItemTitle(title);

    const column = board.getColumnById(columnId);
    if (!column) {
      console.warn(`[ItemService] Column not found: ${columnId}`);
      throw new ColumnNotFoundError(`Column with id '${columnId}' not found`);
    }

    // Check if column is at capacity before adding
    this.validator.validateColumnCapacity(column);

    if (parentId) {
      const parent = board.getParentById(parentId);
      if (!parent) {
        console.warn(`[ItemService] Parent not found: ${parentId}`);
        throw new ValidationError(`Parent with id '${parentId}' not found`);
      }
    }

    // Generate ID for manual item
    const nextIndex = this._getNextItemIndex(board);
    const itemId = generateManualItemId(board.name, nextIndex);

    const item = column.addItem(title, parentId || null, itemId);
    if (description) {
      item.description = description;
    }

    // Set default issue type for manually created items
    item.metadata.issue_type = DEFAULT_ISSUE_TYPE;

    console.info(
      `[ItemService] Successfully created item: ${title} [${itemId}] in column: ${column.name}`
    );
    return item;
  }

  /**
   * Calculate the next sequential index for manual items on this board
   * Scans all items across all columns to find the highest index
   */
  private _getNextItemIndex(board: Board): number {
    const boardPrefix = getBoardPrefix(board.name);
    const pattern = new RegExp(`^${boardPrefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}-(\\d+)$`);
    let maxIndex = 0;

    // Scan all items across all columns
    for (const column of board.columns) {
      for (const item of column.items) {
        const match = item.id.match(pattern);
        if (match) {
          const index = parseInt(match[1], 10);
          maxIndex = Math.max(maxIndex, index);
        }
      }
    }

    return maxIndex + 1;
  }

  /**
   * Update an item's properties
   * @throws {ItemNotFoundError} if item not found
   * @throws {ValidationError} if validation fails
   */
  async updateItem(board: Board, itemId: ItemId, updates: Partial<Item>): Promise<boolean> {
    for (const column of board.columns) {
      const item = column.getItemById(itemId);
      if (item) {
        if (updates.title) {
          this.validator.validateItemTitle(updates.title);
        }

        item.update(updates);
        return true;
      }
    }

    throw new ItemNotFoundError(`Item with id '${itemId}' not found`);
  }

  /**
   * Delete an item from the board
   * @throws {ItemNotFoundError} if item not found
   * @throws {ValidationError} if deletion fails
   */
  async deleteItem(board: Board, itemId: ItemId): Promise<boolean> {
    console.info(`[ItemService] Deleting item: ${itemId} from board: ${board.name}`);

    for (const column of board.columns) {
      const item = column.getItemById(itemId);
      if (item) {
        console.debug(
          `[ItemService] Found item to delete: ${item.title} in column: ${column.name}`
        );

        const deleted = await this.storage.deleteItemFromColumn(board, item, column);
        if (!deleted) {
          console.error(
            `[ItemService] Failed to delete item from storage: ${item.title}`
          );
          throw new ValidationError('Failed to delete item from storage');
        }

        const success = column.removeItem(itemId);
        if (success) {
          await this.storage.saveBoardToStorage(board);
          console.info(`[ItemService] Successfully deleted item: ${item.title}`);
        }
        return success;
      }
    }

    console.warn(`[ItemService] Item not found for deletion: ${itemId}`);
    throw new ItemNotFoundError(`Item with id '${itemId}' not found`);
  }

  /**
   * Move an item between columns
   * @throws {ItemNotFoundError} if item not found
   * @throws {ColumnNotFoundError} if target column not found
   * @throws {ValidationError} if target column at capacity
   */
  async moveItemBetweenColumns(
    board: Board,
    itemId: ItemId,
    targetColumnId: ColumnId
  ): Promise<boolean> {
    let itemToMove: Item | null = null;
    let sourceColumn = null;

    // Find the item in the board
    for (const column of board.columns) {
      const item = column.getItemById(itemId);
      if (item) {
        itemToMove = item;
        sourceColumn = column;
        break;
      }
    }

    if (!itemToMove || !sourceColumn) {
      throw new ItemNotFoundError(`Item with id '${itemId}' not found`);
    }

    if (sourceColumn.id === targetColumnId) {
      return false; // Already in target column
    }

    const targetColumn = board.getColumnById(targetColumnId);
    if (!targetColumn) {
      throw new ColumnNotFoundError(
        `Target column with id '${targetColumnId}' not found`
      );
    }

    // Check if target column is at capacity before moving
    this.validator.validateColumnCapacity(targetColumn);

    // Move item in storage
    const moved = await this.storage.moveItemBetweenColumns(
      board,
      itemToMove,
      sourceColumn,
      targetColumn
    );
    if (!moved) {
      return false;
    }

    // Update board structure
    const removed = sourceColumn.removeItem(itemId);
    if (!removed) {
      throw new ValidationError('Failed to remove item from source column');
    }

    itemToMove.moveToColumn(targetColumnId);
    targetColumn.moveItemToEnd(itemToMove);

    await this.storage.saveBoardToStorage(board);
    return true;
  }

  /**
   * Set or clear the parent for an item
   * @throws {ValidationError} if parent not found
   * @throws {ItemNotFoundError} if item not found
   */
  async setItemParent(
    board: Board,
    itemId: ItemId,
    parentId: ParentId | null
  ): Promise<boolean> {
    if (parentId) {
      const parent = board.getParentById(parentId);
      if (!parent) {
        throw new ValidationError(`Parent with id '${parentId}' not found`);
      }
    }

    for (const column of board.columns) {
      const item = column.getItemById(itemId);
      if (item) {
        item.setParent(parentId);
        return true;
      }
    }

    throw new ItemNotFoundError(`Item with id '${itemId}' not found`);
  }

  /**
   * Get items grouped by parent
   * Orphaned items come first, then items grouped by parent
   * @throws {ColumnNotFoundError} if column not found
   */
  async getItemsGroupedByParent(board: Board, columnId: ColumnId): Promise<Item[]> {
    const column = board.getColumnById(columnId);
    if (!column) {
      throw new ColumnNotFoundError(`Column with id '${columnId}' not found`);
    }

    const items = column.getAllItems();
    const orphanedItems = items.filter((item) => item.parent_id === null);
    const parentGroups: { [key: string]: Item[] } = {};

    // Group items by parent
    for (const item of items) {
      if (item.parent_id) {
        if (!parentGroups[item.parent_id]) {
          parentGroups[item.parent_id] = [];
        }
        parentGroups[item.parent_id].push(item);
      }
    }

    // Combine orphaned items with parent groups
    const groupedItems = [...orphanedItems];
    for (const parentId in parentGroups) {
      groupedItems.push(...parentGroups[parentId]);
    }

    return groupedItems;
  }
}
