/**
 * Markdown Storage Repository
 * Item-level storage operations with rollback support
 * Ported from Python: src/infrastructure/storage/markdown_storage_repository.py
 */

import { FileSystemManager } from "./FileSystemManager";
import { MarkdownParser } from "./MarkdownParser";
import { BoardPersistence } from "./BoardPersistence";
import { findItemFileById } from "./FileOperations";
import { StorageRepository } from "../../domain/repositories/StorageRepository";
import { Board } from "../../domain/entities/Board";
import { Column } from "../../domain/entities/Column";
import { Item } from "../../domain/entities/Item";

export class MarkdownStorageRepository implements StorageRepository {
  private fileSystem: FileSystemManager;
  private parser: MarkdownParser;
  private persistence: BoardPersistence;

  constructor(fileSystem: FileSystemManager) {
    this.fileSystem = fileSystem;
    this.parser = new MarkdownParser(fileSystem);
    this.persistence = new BoardPersistence(fileSystem, this.parser);
  }

  /**
   * Delete an item from a column
   */
  async deleteItemFromColumn(board: Board, item: Item, column: Column): Promise<boolean> {
    try {
      console.log(
        `Deleting item from column: board="${board.name}", column="${column.name}", item="${item.title}"`
      );

      const columnDir = this.fileSystem.getColumnDirectory(board.name, column.name);
      const itemFile = await findItemFileById(
        this.fileSystem,
        this.parser,
        columnDir,
        item.id
      );

      if (itemFile) {
        const deleted = await this.fileSystem.deleteFile(itemFile);

        if (deleted) {
          console.log(
            `Successfully deleted item: board="${board.name}", column="${column.name}", item="${item.title}"`
          );
          return true;
        } else {
          console.error(
            `Failed to delete item file: board="${board.name}", column="${column.name}", item="${item.title}"`
          );
          return false;
        }
      }

      console.warn(
        `Item file not found for deletion: board="${board.name}", column="${column.name}", item="${item.title}"`
      );
      return false;
    } catch (error) {
      console.error(
        `Failed to delete item from column: board="${board.name}", column="${column.name}", item="${item.title}"`,
        error
      );
      return false;
    }
  }

  /**
   * Move an item between columns with rollback on failure
   */
  async moveItemBetweenColumns(
    board: Board,
    item: Item,
    oldColumn: Column,
    newColumn: Column
  ): Promise<boolean> {
    try {
      console.log(
        `Moving item between columns: board="${board.name}", item="${item.title}", from="${oldColumn.name}" to="${newColumn.name}"`
      );

      // First, save the item to the new column
      try {
        await this.persistence.saveItemToColumn(board.name, newColumn.name, {
          id: item.id,
          title: item.title,
          description: item.description,
          parent_id: item.parent_id,
          created_at: item.created_at,
          moved_in_progress_at: item.moved_in_progress_at,
          moved_in_done_at: item.moved_in_done_at,
          worked_on_for: item.worked_on_for,
        });

        console.log(
          `Saved item to new column: board="${board.name}", column="${newColumn.name}", item="${item.title}"`
        );

        // Then, delete from the old column
        const deleted = await this.deleteItemFromColumn(board, item, oldColumn);

        if (deleted) {
          console.log(
            `Successfully moved item between columns: board="${board.name}", item="${item.title}", from="${oldColumn.name}" to="${newColumn.name}"`
          );
          return true;
        } else {
          // If delete failed, try to clean up the new file (rollback)
          console.warn(
            `Failed to delete from old column, cleaning up new column: board="${board.name}", item="${item.title}"`
          );
          await this.deleteItemFromColumn(board, item, newColumn);
          return false;
        }
      } catch (saveError) {
        console.error(
          `Failed to save item to new column: board="${board.name}", column="${newColumn.name}", item="${item.title}"`,
          saveError
        );
        return false;
      }
    } catch (error) {
      console.error(
        `Failed to move item between columns: board="${board.name}", item="${item.title}"`,
        error
      );
      return false;
    }
  }

  /**
   * Save entire board to storage (all columns and items)
   */
  async saveBoardToStorage(board: Board): Promise<void> {
    try {
      console.log(`Saving board to storage: board="${board.name}"`);

      // Save all columns and their items
      for (const column of board.columns) {
        console.log(`Saving column: board="${board.name}", column="${column.name}"`);

        // Ensure column directory exists
        const columnDir = this.fileSystem.getColumnDirectory(board.name, column.name);
        await this.fileSystem.ensureDirectoryExists(columnDir);

        // Save column metadata
        await this.persistence.saveColumnMetadata(board.name, column.name, {
          id: column.id,
          name: column.name,
          position: column.position,
          limit: column.limit,
          created_at: column.created_at,
        });

        // Save all items in this column
        for (const item of column.items) {
          await this.persistence.saveItemToColumn(board.name, column.name, {
            id: item.id,
            title: item.title,
            description: item.description,
            parent_id: item.parent_id,
            created_at: item.created_at,
            moved_in_progress_at: item.moved_in_progress_at,
            moved_in_done_at: item.moved_in_done_at,
            worked_on_for: item.worked_on_for,
          });
        }
      }

      console.log(`Successfully saved board to storage: board="${board.name}"`);
    } catch (error) {
      console.error(`Failed to save board to storage: board="${board.name}"`, error);
      throw error;
    }
  }
}
