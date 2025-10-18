/**
 * Board Persistence Layer
 * Low-level file operations for saving/loading board data
 * Ported from Python: src/infrastructure/storage/board_persistence.py
 */

import { FileSystemManager } from "./FileSystemManager";
import { MarkdownParser } from "./MarkdownParser";
import {
  findItemFileById,
  getBoardDirectoryPath,
  getColumnDirectoryPath,
  cleanupColumnFiles,
  getUniqueFilename,
} from "./FileOperations";
import { ItemId } from "../../core/types";
import { BOARD_FILENAME, COLUMN_METADATA_FILENAME } from "../../core/constants";
import { getTitleFilename } from "../../utils/stringUtils";
import { now } from "../../utils/dateUtils";

export interface ItemData {
  id: ItemId;
  title: string;
  description?: string;
  parent_id?: string | null;
  created_at?: Date;
  moved_in_progress_at?: Date | null;
  moved_in_done_at?: Date | null;
  worked_on_for?: string | null; // Format: "HH:MM"
  [key: string]: any; // Allow additional metadata
}

export interface ColumnData {
  id: string;
  name: string;
  position: number;
  limit?: number | null;
  created_at?: Date;
}

export class BoardPersistence {
  private fileSystem: FileSystemManager;
  private parser: MarkdownParser;
  private boardsDir: string;

  constructor(fileSystem: FileSystemManager, parser: MarkdownParser) {
    this.fileSystem = fileSystem;
    this.parser = parser;
    this.boardsDir = fileSystem.getBoardsDirectory();
  }

  /**
   * Save an item to a column directory
   */
  async saveItemToColumn(
    boardName: string,
    columnName: string,
    itemData: ItemData
  ): Promise<void> {
    try {
      const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
      const columnDir = getColumnDirectoryPath(boardDir, columnName);

      // Ensure column directory exists
      await this.fileSystem.ensureDirectoryExists(columnDir);

      const itemId = itemData.id;
      const title = itemData.title;
      const content = itemData.description || "";

      // Generate new filename: {id}-{title}.md (lowercase)
      const titlePart = getTitleFilename(title);
      const newFilename = `${itemId.toLowerCase()}-${titlePart}`;
      const newItemFile = `${columnDir}${newFilename}.md`;

      // Check if item already exists with different filename
      const oldItemFile = await findItemFileById(
        this.fileSystem,
        this.parser,
        columnDir,
        itemId
      );

      if (oldItemFile) {
        const currentFilename = this.getFileStem(oldItemFile);
        if (currentFilename !== newFilename) {
          // Need to rename - check for collisions
          const newFileExists = await this.fileSystem.fileExists(newItemFile);
          if (newFileExists && newItemFile !== oldItemFile) {
            // Collision - get unique filename
            const uniqueFilename = await getUniqueFilename(
              this.fileSystem,
              this.parser,
              newItemFile,
              itemId
            );
            const uniquePath = `${columnDir}${uniqueFilename}.md`;
            await this.fileSystem.renameFile(oldItemFile, uniquePath);
          } else {
            // Safe to rename
            await this.fileSystem.renameFile(oldItemFile, newItemFile);
          }
        }
      }

      // Extract metadata (exclude title and description which become content)
      const metadata: Record<string, any> = {};
      for (const [key, value] of Object.entries(itemData)) {
        if (key !== "title" && key !== "description") {
          metadata[key] = value;
        }
      }

      // Ensure created_at has a default
      if (!metadata.created_at) {
        metadata.created_at = now();
      }

      // Save the item with metadata
      const finalItemFile = oldItemFile || newItemFile;
      await this.parser.saveItemWithMetadata(finalItemFile, title, content, metadata);
    } catch (error) {
      throw new Error(
        `Failed to save item "${itemData.title}" to column "${columnName}": ${error}`
      );
    }
  }

  /**
   * Delete an item from a column
   */
  async deleteItemFromColumn(
    boardName: string,
    columnName: string,
    itemId: ItemId
  ): Promise<boolean> {
    try {
      const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
      const columnDir = getColumnDirectoryPath(boardDir, columnName);

      const itemFile = await findItemFileById(
        this.fileSystem,
        this.parser,
        columnDir,
        itemId
      );

      if (itemFile) {
        return await this.fileSystem.deleteFile(itemFile);
      }

      return false;
    } catch (error) {
      console.error(`Failed to delete item ${itemId} from column ${columnName}:`, error);
      return false;
    }
  }

  /**
   * Move an item between columns
   */
  async moveItemBetweenColumns(
    boardName: string,
    oldColumnName: string,
    newColumnName: string,
    itemData: ItemData
  ): Promise<boolean> {
    try {
      const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
      const oldColumnDir = getColumnDirectoryPath(boardDir, oldColumnName);
      const newColumnDir = getColumnDirectoryPath(boardDir, newColumnName);

      // Ensure new column directory exists
      await this.fileSystem.ensureDirectoryExists(newColumnDir);

      const itemId = itemData.id;

      // Find old item file
      const oldItemFile = await findItemFileById(
        this.fileSystem,
        this.parser,
        oldColumnDir,
        itemId
      );

      if (oldItemFile) {
        // Save to new column
        await this.saveItemToColumn(boardName, newColumnName, itemData);

        // Delete from old column
        await this.fileSystem.deleteFile(oldItemFile);
        return true;
      }

      return false;
    } catch (error) {
      console.error(
        `Failed to move item ${itemData.id} from ${oldColumnName} to ${newColumnName}:`,
        error
      );
      return false;
    }
  }

  /**
   * Save column metadata
   */
  async saveColumnMetadata(
    boardName: string,
    columnName: string,
    columnData: ColumnData
  ): Promise<void> {
    try {
      const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
      const columnDir = getColumnDirectoryPath(boardDir, columnName);

      await this.fileSystem.ensureDirectoryExists(columnDir);

      const columnMetadataFile = `${columnDir}${COLUMN_METADATA_FILENAME}`;

      const metadata: Record<string, any> = {
        position: columnData.position,
        created_at: columnData.created_at || now(),
      };

      if (columnData.limit !== undefined && columnData.limit !== null) {
        metadata.limit = columnData.limit;
      }

      await this.parser.saveColumnMetadata(columnMetadataFile, columnName, metadata);
    } catch (error) {
      throw new Error(`Failed to save column metadata for "${columnName}": ${error}`);
    }
  }

  /**
   * Clean up orphaned files in a column
   */
  async cleanupColumn(
    boardName: string,
    columnName: string,
    currentItemIds: Set<ItemId>
  ): Promise<void> {
    try {
      const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
      const columnDir = getColumnDirectoryPath(boardDir, columnName);

      await cleanupColumnFiles(this.fileSystem, this.parser, columnDir, currentItemIds);
    } catch (error) {
      console.error(`Failed to cleanup column ${columnName}:`, error);
    }
  }

  /**
   * Get the path to a board's kanban.md file
   */
  getBoardFilePath(boardName: string): string {
    const boardDir = getBoardDirectoryPath(this.boardsDir, boardName);
    return `${boardDir}${BOARD_FILENAME}`;
  }

  /**
   * List all board directories
   */
  async listBoardDirectories(): Promise<string[]> {
    try {
      const exists = await this.fileSystem.directoryExists(this.boardsDir);
      if (!exists) {
        return [];
      }

      return await this.fileSystem.listDirectories(this.boardsDir);
    } catch (error) {
      console.error(`Failed to list board directories:`, error);
      return [];
    }
  }

  /**
   * Get file stem (filename without extension)
   */
  private getFileStem(filePath: string): string {
    const parts = filePath.split("/");
    const filename = parts[parts.length - 1];
    return filename.replace(/\.md$/, "");
  }
}
