/**
 * BoardRepository interface for board persistence operations
 * Ported from Python: src/domain/repositories/board_repository.py
 */

import { Board } from "../entities/Board";
import { BoardId } from "../../core/types";

export interface BoardRepository {
  /**
   * Load all boards from storage
   */
  loadAllBoards(): Promise<Board[]>;

  /**
   * Load a board by its ID
   */
  loadBoardById(boardId: BoardId): Promise<Board | null>;

  /**
   * Load a board by its name
   */
  loadBoardByName(boardName: string): Promise<Board | null>;

  /**
   * Save a board to storage
   */
  saveBoard(board: Board): Promise<void>;

  /**
   * Delete a board from storage
   */
  deleteBoard(boardId: BoardId): Promise<boolean>;

  /**
   * List all board names
   */
  listBoardNames(): Promise<string[]>;

  /**
   * Create a sample board with default columns
   */
  createSampleBoard(name: string): Promise<Board>;
}
