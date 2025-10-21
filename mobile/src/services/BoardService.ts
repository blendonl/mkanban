/**
 * BoardService handles business logic for board operations
 * Ported from Python: src/services/board_service.py
 */

import { Board } from '../domain/entities/Board';
import { Column } from '../domain/entities/Column';
import { BoardRepository } from '../domain/repositories/BoardRepository';
import { ValidationService } from './ValidationService';
import { BoardId, ColumnId } from '../core/types';
import { BoardNotFoundError, ValidationError } from '../core/exceptions';
import { getEventBus } from '../core/EventBus';

export class BoardService {
  private repository: BoardRepository;
  private validator: ValidationService;

  constructor(
    repository: BoardRepository,
    validator: ValidationService
  ) {
    this.repository = repository;
    this.validator = validator;
  }

  /**
   * Get all boards from storage
   */
  async getAllBoards(): Promise<Board[]> {
    return await this.repository.loadAllBoards();
  }

  /**
   * Get a board by its ID
   * @throws {BoardNotFoundError} if board not found
   */
  async getBoardById(boardId: BoardId): Promise<Board> {
    console.debug(`[BoardService] Loading board by id: ${boardId}`);
    const board = await this.repository.loadBoardById(boardId);

    if (!board) {
      console.warn(`[BoardService] Board not found: ${boardId}`);
      throw new BoardNotFoundError(`Board with id '${boardId}' not found`);
    }

    console.info(`[BoardService] Successfully loaded board: ${board.name}`);

    // Emit board loaded event
    await getEventBus().publish('board_loaded', {
      boardId: board.id,
      boardName: board.name,
      timestamp: new Date(),
    });

    return board;
  }

  /**
   * Get a board by its name
   * @throws {BoardNotFoundError} if board not found
   */
  async getBoardByName(boardName: string): Promise<Board> {
    console.debug(`[BoardService] Loading board by name: ${boardName}`);
    const board = await this.repository.loadBoardByName(boardName);

    if (!board) {
      console.warn(`[BoardService] Board not found: ${boardName}`);
      throw new BoardNotFoundError(`Board with name '${boardName}' not found`);
    }

    console.info(`[BoardService] Successfully loaded board: ${boardName}`);
    return board;
  }

  /**
   * Create a new board
   * @throws {ValidationError} if name is invalid or board already exists
   */
  async createBoard(name: string, description: string = ''): Promise<Board> {
    console.info(`[BoardService] Creating new board: ${name}`);
    this.validator.validateBoardName(name);

    const existingBoard = await this.repository.loadBoardByName(name);
    if (existingBoard) {
      console.warn(`[BoardService] Board already exists: ${name}`);
      throw new ValidationError(`Board with name '${name}' already exists`);
    }

    const board = new Board({ name, description });
    await this.repository.saveBoard(board);
    console.info(`[BoardService] Successfully created board: ${name}`);

    // Emit board created event
    await getEventBus().publish('board_created', {
      boardId: board.id,
      boardName: board.name,
      timestamp: new Date(),
    });

    return board;
  }

  /**
   * Save a board to storage
   * @throws {ValidationError} if board structure is invalid
   */
  async saveBoard(board: Board): Promise<void> {
    console.debug(`[BoardService] Saving board: ${board.name}`);
    this.validator.validateBoard(board);
    await this.repository.saveBoard(board);
    console.info(`[BoardService] Successfully saved board: ${board.name}`);

    // Emit board updated event
    await getEventBus().publish('board_updated', {
      boardId: board.id,
      boardName: board.name,
      timestamp: new Date(),
    });
  }

  /**
   * Delete a board from storage
   * @returns true if board was deleted, false if not found
   */
  async deleteBoard(boardId: BoardId): Promise<boolean> {
    const deleted = await this.repository.deleteBoard(boardId);

    if (deleted) {
      // Emit board deleted event
      await getEventBus().publish('board_deleted', {
        boardId,
        boardName: '', // Name not available after deletion
        timestamp: new Date(),
      });
    }

    return deleted;
  }

  /**
   * Add a new column to a board
   * @throws {ValidationError} if column name is invalid or already exists
   */
  async addColumnToBoard(
    board: Board,
    columnName: string,
    position?: number | null
  ): Promise<Column> {
    console.info(`[BoardService] Adding column '${columnName}' to board '${board.name}'`);
    this.validator.validateColumnName(columnName);

    // Check for duplicate column names (case-insensitive)
    for (const existingColumn of board.columns) {
      if (existingColumn.name.toLowerCase() === columnName.toLowerCase()) {
        console.warn(`[BoardService] Column already exists: ${columnName}`);
        throw new ValidationError(`Column '${columnName}' already exists in board`);
      }
    }

    const column = board.addColumn(columnName, position);
    console.info(`[BoardService] Successfully added column '${columnName}' to board '${board.name}'`);

    // Emit column created event
    await getEventBus().publish('column_created', {
      columnId: column.id,
      columnName: column.name,
      boardId: board.id,
      timestamp: new Date(),
    });

    return column;
  }

  /**
   * Remove a column from a board
   * @throws {ValidationError} if column contains items
   * @returns true if column was removed, false if not found
   */
  async removeColumnFromBoard(board: Board, columnId: ColumnId): Promise<boolean> {
    const column = board.getColumnById(columnId);
    if (!column) {
      return false;
    }

    if (column.items.length > 0) {
      throw new ValidationError('Cannot delete column that contains items');
    }

    return board.removeColumn(columnId);
  }

  /**
   * List all board names
   */
  async listBoardNames(): Promise<string[]> {
    return await this.repository.listBoardNames();
  }

  /**
   * Get a board by name, or create a sample board if it doesn't exist
   */
  async getOrCreateSampleBoard(name: string = 'default'): Promise<Board> {
    try {
      return await this.getBoardByName(name);
    } catch (error) {
      if (error instanceof BoardNotFoundError) {
        const board = await this.repository.createSampleBoard(name);
        await this.repository.saveBoard(board);
        return board;
      }
      throw error;
    }
  }
}
