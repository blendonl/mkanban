/**
 * Markdown Board Repository
 * High-level board operations - loading and saving entire boards
 * Ported from Python: src/infrastructure/storage/markdown_board_repository.py
 */

import { FileSystemManager } from "./FileSystemManager";
import { MarkdownParser } from "./MarkdownParser";
import { BoardPersistence } from "./BoardPersistence";
import { getColumnDirectoryPath } from "./FileOperations";
import { BoardRepository } from "../../domain/repositories/BoardRepository";
import { Board } from "../../domain/entities/Board";
import { Column } from "../../domain/entities/Column";
import { Item } from "../../domain/entities/Item";
import { Parent } from "../../domain/entities/Parent";
import { BoardId } from "../../core/types";
import { BOARD_FILENAME, COLUMN_METADATA_FILENAME } from "../../core/constants";
import { generateIdFromName } from "../../utils/stringUtils";
import { now } from "../../utils/dateUtils";
import { FileSystemObserver } from "../../core/FileSystemObserver";

export class MarkdownBoardRepository implements BoardRepository, FileSystemObserver {
  private fileSystem: FileSystemManager;
  private parser: MarkdownParser;
  private persistence: BoardPersistence;
  private boardsDir: string;

  constructor(fileSystem: FileSystemManager) {
    this.fileSystem = fileSystem;
    this.parser = new MarkdownParser(fileSystem);
    this.persistence = new BoardPersistence(fileSystem, this.parser);
    this.boardsDir = fileSystem.getBoardsDirectory();

    // Register as observer to receive boards directory changes
    fileSystem.addObserver(this);
  }

  /**
   * Called when the boards directory path changes
   * Updates the cached boards directory path
   */
  onBoardsDirectoryChanged(newPath: string): void {
    console.log(`MarkdownBoardRepository: Boards directory changed from ${this.boardsDir} to ${newPath}`);
    this.boardsDir = newPath;
  }

  /**
   * Load all boards from the boards directory
   */
  async loadAllBoards(): Promise<Board[]> {
    try {
      console.log("Loading all boards from", this.boardsDir);
      const boards: Board[] = [];

      // Ensure boards directory exists
      await this.fileSystem.ensureDirectoryExists(this.boardsDir);

      // Get all board directories
      const boardDirs = await this.fileSystem.listDirectories(this.boardsDir);

      for (const boardDir of boardDirs) {
        const kanbanFile = `${boardDir}${BOARD_FILENAME}`;
        const exists = await this.fileSystem.fileExists(kanbanFile);

        if (exists) {
          const board = await this.loadBoardFromFile(kanbanFile);
          if (board) {
            boards.push(board);
          }
        }
      }

      console.log(`Loaded ${boards.length} boards`);
      return boards;
    } catch (error) {
      console.error("Failed to load all boards:", error);
      return [];
    }
  }

  /**
   * Load a board by its ID
   */
  async loadBoardById(boardId: BoardId): Promise<Board | null> {
    try {
      console.log("Loading board by ID:", boardId);

      const boardDirs = await this.fileSystem.listDirectories(this.boardsDir);

      for (const boardDir of boardDirs) {
        const kanbanFile = `${boardDir}${BOARD_FILENAME}`;
        const exists = await this.fileSystem.fileExists(kanbanFile);

        if (exists) {
          const board = await this.loadBoardFromFile(kanbanFile);
          if (board && board.id === boardId) {
            console.log("Found board by ID:", board.name);
            return board;
          }
        }
      }

      console.warn("Board not found by ID:", boardId);
      return null;
    } catch (error) {
      console.error("Failed to load board by ID:", error);
      return null;
    }
  }

  /**
   * Load a board by its name
   */
  async loadBoardByName(boardName: string): Promise<Board | null> {
    try {
      console.log("Loading board by name:", boardName);
      const boards = await this.loadAllBoards();

      for (const board of boards) {
        if (board.name.toLowerCase() === boardName.toLowerCase()) {
          console.log("Found board by name:", boardName);
          return board;
        }
      }

      console.warn("Board not found by name:", boardName);
      return null;
    } catch (error) {
      console.error("Failed to load board by name:", error);
      return null;
    }
  }

  /**
   * Load a board from its kanban.md file
   */
  async loadBoardFromFile(kanbanFile: string): Promise<Board | null> {
    try {
      // Parse board metadata
      const parsed = await this.parser.parseBoardMetadata(kanbanFile);
      const boardName = parsed.name;
      const metadata = parsed.metadata;

      // Get board directory (parent of kanban.md)
      const boardDir = this.getParentDirectory(kanbanFile);

      // Create Board instance
      const board = new Board({
        id: metadata.id || this.getBoardDirName(boardDir),
        name: boardName,
        description: metadata.description || "",
        created_at: metadata.created_at ? new Date(metadata.created_at) : now(),
        file_path: kanbanFile,
      });

      // Load columns with items
      await this.loadColumnsForBoard(board, boardDir);

      // Load parents
      this.loadParentsForBoard(board, metadata);

      return board;
    } catch (error) {
      console.error(`Failed to load board from file ${kanbanFile}:`, error);
      return null;
    }
  }

  /**
   * Save a board (metadata, columns, items, parents)
   */
  async saveBoard(board: Board): Promise<void> {
    try {
      console.log("Saving board:", board.name);

      const kanbanFile = this.persistence.getBoardFilePath(board.name);

      // Ensure board directory exists
      const boardDir = this.getParentDirectory(kanbanFile);
      await this.fileSystem.ensureDirectoryExists(boardDir);

      // Prepare board metadata
      const boardData: Record<string, any> = {
        id: board.id,
        name: board.name,
        description: board.description,
        created_at: board.created_at,
        parents: board.parents.map((parent) => ({
          id: parent.id,
          name: parent.name,
          color: parent.color,
          created_at: parent.created_at,
        })),
      };

      // Save board metadata to kanban.md
      await this.parser.saveBoardMetadata(kanbanFile, board.name, boardData);

      // Save all columns
      await this.saveColumnsForBoard(board, boardDir);

      console.log("Successfully saved board:", board.name);
    } catch (error) {
      throw new Error(`Failed to save board "${board.name}": ${error}`);
    }
  }

  /**
   * Delete a board by its ID
   */
  async deleteBoard(boardId: BoardId): Promise<boolean> {
    try {
      console.log("Deleting board:", boardId);

      // Load the board to get its name
      const board = await this.loadBoardById(boardId);
      if (!board) {
        console.warn("Cannot delete non-existent board:", boardId);
        return false;
      }

      // Get board directory
      const boardDir = this.fileSystem.getBoardDirectory(board.name);

      // Delete the entire directory
      const deleted = await this.fileSystem.deleteDirectory(boardDir);

      if (deleted) {
        console.log("Successfully deleted board:", board.name);
      }

      return deleted;
    } catch (error) {
      console.error("Failed to delete board:", error);
      return false;
    }
  }

  /**
   * List all board names
   */
  async listBoardNames(): Promise<string[]> {
    try {
      const boards = await this.loadAllBoards();
      return boards.map((board) => board.name);
    } catch (error) {
      console.error("Failed to list board names:", error);
      return [];
    }
  }

  /**
   * Create a sample board with default columns
   */
  async createSampleBoard(name: string): Promise<Board> {
    console.log("Creating sample board:", name);

    const board = new Board({
      name,
      description: "Sample board for getting started",
    });

    // Add default columns
    board.addColumn("To Do", 0);
    board.addColumn("In Progress", 1);
    board.addColumn("Done", 2);

    // Add sample parent
    board.addParent("Sample Project", "blue");

    console.log("Created sample board:", name);
    return board;
  }

  /**
   * Load columns for a board from the file system
   */
  private async loadColumnsForBoard(board: Board, boardDir: string): Promise<void> {
    try {
      const columnDirs = await this.fileSystem.listDirectories(boardDir);

      // Sort column directories alphabetically
      columnDirs.sort();

      // First pass: load columns with explicit positions from metadata
      const columnsWithPositions: Array<{ column: Column; columnDir: string }> = [];
      const columnsWithoutPositions: Array<{ column: Column; columnDir: string }> = [];
      const usedPositions = new Set<number>();

      for (const columnDir of columnDirs) {
        const columnMetadataFile = `${columnDir}${COLUMN_METADATA_FILENAME}`;
        const metadataExists = await this.fileSystem.fileExists(columnMetadataFile);

        let column: Column;
        const columnDirName = this.getDirectoryName(columnDir);

        if (metadataExists) {
          try {
            const metadata = await this.parser.parseColumnMetadata(columnMetadataFile);
            if (metadata) {
              const position = metadata.position;
              column = new Column({
                id: metadata.id || columnDirName,
                name: metadata.name || this.formatColumnName(columnDirName),
                position: position !== undefined ? position : 0,
                limit: metadata.limit,
                created_at: metadata.created_at ? new Date(metadata.created_at) : now(),
                file_path: columnMetadataFile,
              });

              if (position !== undefined && position !== null) {
                usedPositions.add(position);
                columnsWithPositions.push({ column, columnDir });
              } else {
                columnsWithoutPositions.push({ column, columnDir });
              }
            } else {
              // Metadata file exists but empty
              column = new Column({
                id: columnDirName,
                name: this.formatColumnName(columnDirName),
                file_path: columnDir,
              });
              columnsWithoutPositions.push({ column, columnDir });
            }
          } catch (error) {
            // Failed to parse metadata, use defaults
            column = new Column({
              id: columnDirName,
              name: this.formatColumnName(columnDirName),
              file_path: columnDir,
            });
            columnsWithoutPositions.push({ column, columnDir });
          }
        } else {
          // No metadata file
          column = new Column({
            id: columnDirName,
            name: this.formatColumnName(columnDirName),
            file_path: columnDir,
          });
          columnsWithoutPositions.push({ column, columnDir });
        }
      }

      // Second pass: assign positions to columns without explicit positions
      let nextPosition = 0;
      for (const { column, columnDir } of columnsWithoutPositions) {
        while (usedPositions.has(nextPosition)) {
          nextPosition++;
        }
        column.position = nextPosition;
        usedPositions.add(nextPosition);
        nextPosition++;
      }

      // Load items for all columns
      const allColumns = [...columnsWithPositions, ...columnsWithoutPositions];
      for (const { column, columnDir } of allColumns) {
        await this.loadItemsForColumn(column, columnDir);
        board.columns.push(column);
      }

      // Sort columns by position, then by name
      board.columns.sort((a, b) => {
        if (a.position !== b.position) {
          return a.position - b.position;
        }
        return a.name.localeCompare(b.name);
      });
    } catch (error) {
      console.error("Failed to load columns for board:", error);
    }
  }

  /**
   * Load items for a column from the file system
   */
  private async loadItemsForColumn(column: Column, columnDir: string): Promise<void> {
    try {
      const itemFiles = await this.fileSystem.listFiles(columnDir, "*.md");

      for (const itemFile of itemFiles) {
        // Skip column.md
        if (itemFile.endsWith(COLUMN_METADATA_FILENAME)) {
          continue;
        }

        try {
          const parsed = await this.parser.parseItemMetadata(itemFile);
          const title = parsed.title;
          const content = parsed.content;
          const metadata = parsed.metadata;

          // System-managed timing fields - validate based on current column
          const timingMetadata = {
            moved_in_progress_at: metadata.moved_in_progress_at
              ? new Date(metadata.moved_in_progress_at)
              : null,
            moved_in_done_at: metadata.moved_in_done_at
              ? new Date(metadata.moved_in_done_at)
              : null,
            worked_on_for: metadata.worked_on_for || null,
          };

          // Normalize column ID for comparison
          const normalizedColumnId = column.id.replace(/_/g, "-");

          // Validate timing fields based on current column
          if (normalizedColumnId !== "in-progress" && normalizedColumnId !== "done") {
            // Item is in to-do or other column - reset timing fields
            timingMetadata.moved_in_progress_at = null;
            timingMetadata.moved_in_done_at = null;
            timingMetadata.worked_on_for = null;
          } else if (normalizedColumnId === "in-progress") {
            // Item is in progress - clear done-related fields
            timingMetadata.moved_in_done_at = null;
            timingMetadata.worked_on_for = null;
          }
          // If in 'done' column, keep all timing fields as-is

          // Create Item instance
          const item = new Item({
            id: metadata.id || generateIdFromName(this.getFileStem(itemFile)),
            title: metadata.title || title,
            description: metadata.description || content || "",
            column_id: column.id,
            parent_id: metadata.parent_id || null,
            created_at: metadata.created_at ? new Date(metadata.created_at) : now(),
            moved_in_progress_at: timingMetadata.moved_in_progress_at,
            moved_in_done_at: timingMetadata.moved_in_done_at,
            worked_on_for: timingMetadata.worked_on_for,
            file_path: itemFile,
          });

          column.items.push(item);
        } catch (error) {
          // Skip corrupted item files
          console.warn(`Skipping corrupted item file ${itemFile}:`, error);
          continue;
        }
      }
    } catch (error) {
      console.error("Failed to load items for column:", error);
    }
  }

  /**
   * Load parents for a board from metadata
   */
  private loadParentsForBoard(board: Board, metadata: Record<string, any>): void {
    const parentsData = metadata.parents || [];

    for (const parentData of parentsData) {
      const parent = new Parent({
        id: parentData.id || generateIdFromName(parentData.name || ""),
        name: parentData.name || "",
        color: parentData.color || "blue",
        created_at: parentData.created_at ? new Date(parentData.created_at) : now(),
      });
      board.parents.push(parent);
    }
  }

  /**
   * Save all columns for a board
   */
  private async saveColumnsForBoard(board: Board, boardDir: string): Promise<void> {
    try {
      // Get existing column directories
      const existingColumnDirs = await this.fileSystem.listDirectories(boardDir);
      const existingColumnNames = new Set(
        existingColumnDirs.map((dir) => this.getDirectoryName(dir))
      );

      // Get board column directory names
      const boardColumnNames = new Set(
        board.columns.map((col) => generateIdFromName(col.name))
      );

      // Remove columns that no longer exist
      for (const dirName of existingColumnNames) {
        if (!boardColumnNames.has(dirName)) {
          const columnDir = `${boardDir}${dirName}/`;
          await this.fileSystem.deleteDirectory(columnDir);
        }
      }

      // Save each column
      for (const column of board.columns) {
        const columnDir = getColumnDirectoryPath(boardDir, column.name);

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
    } catch (error) {
      console.error("Failed to save columns for board:", error);
      throw error;
    }
  }

  /**
   * Get parent directory from a path
   */
  private getParentDirectory(path: string): string {
    const parts = path.split("/").filter((p) => p.length > 0);
    parts.pop(); // Remove filename
    return parts.join("/") + "/";
  }

  /**
   * Get directory name from path (last segment)
   */
  private getDirectoryName(path: string): string {
    const parts = path.split("/").filter((p) => p.length > 0);
    return parts[parts.length - 1];
  }

  /**
   * Get board directory name from path
   */
  private getBoardDirName(boardDir: string): string {
    return this.getDirectoryName(boardDir);
  }

  /**
   * Format column name from directory name
   * Converts "to-do" -> "To Do", "in-progress" -> "In Progress"
   */
  private formatColumnName(dirName: string): string {
    return dirName
      .replace(/-/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
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
