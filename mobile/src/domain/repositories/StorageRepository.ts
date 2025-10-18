/**
 * StorageRepository interface for item-level storage operations
 * Ported from Python: src/domain/repositories/storage_repository.py
 */

import { Board } from "../entities/Board";
import { Column } from "../entities/Column";
import { Item } from "../entities/Item";

export interface StorageRepository {
  /**
   * Delete an item file from a column directory
   */
  deleteItemFromColumn(board: Board, item: Item, column: Column): Promise<boolean>;

  /**
   * Move an item file between column directories
   */
  moveItemBetweenColumns(
    board: Board,
    item: Item,
    oldColumn: Column,
    newColumn: Column
  ): Promise<boolean>;

  /**
   * Save the board and all its items to storage
   */
  saveBoardToStorage(board: Board): Promise<void>;
}
