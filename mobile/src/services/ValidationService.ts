import { ValidationError } from '../core/exceptions';
import { Board } from '../domain/entities/Board';
import { Column } from '../domain/entities/Column';

/**
 * Service for validating domain entities and their properties.
 * Throws ValidationError when validation fails.
 */
export class ValidationService {
  /**
   * Validate board name
   * @throws {ValidationError} if name is invalid
   */
  validateBoardName(name: string): void {
    if (!name || !name.trim()) {
      throw new ValidationError('Board name cannot be empty');
    }

    if (name.length > 100) {
      throw new ValidationError('Board name cannot exceed 100 characters');
    }

    const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
    const hasInvalidChars = invalidChars.some((char) => name.includes(char));

    if (hasInvalidChars) {
      throw new ValidationError(
        `Board name contains invalid characters: ${invalidChars.join(', ')}`
      );
    }
  }

  /**
   * Validate column name
   * @throws {ValidationError} if name is invalid
   */
  validateColumnName(name: string): void {
    if (!name || !name.trim()) {
      throw new ValidationError('Column name cannot be empty');
    }

    if (name.length > 50) {
      throw new ValidationError('Column name cannot exceed 50 characters');
    }
  }

  /**
   * Validate item title
   * @throws {ValidationError} if title is invalid
   */
  validateItemTitle(title: string): void {
    if (!title || !title.trim()) {
      throw new ValidationError('Item title cannot be empty');
    }

    if (title.length > 200) {
      throw new ValidationError('Item title cannot exceed 200 characters');
    }
  }

  /**
   * Validate complete board structure
   * @throws {ValidationError} if board is invalid
   */
  validateBoard(board: Board): void {
    // Validate board name
    this.validateBoardName(board.name);

    // Board must have at least one column
    if (board.columns.length === 0) {
      throw new ValidationError('Board must have at least one column');
    }

    // Check for duplicate column names (case-insensitive)
    const columnNames = board.columns.map((col) => col.name.toLowerCase());
    const uniqueNames = new Set(columnNames);
    if (columnNames.length !== uniqueNames.size) {
      throw new ValidationError('Board cannot have duplicate column names');
    }

    // Check for duplicate positions
    const positions = board.columns
      .map((col) => col.position)
      .filter((pos): pos is number => pos !== null && pos !== undefined);

    const uniquePositions = new Set(positions);
    if (positions.length !== uniquePositions.size) {
      throw new ValidationError('Board cannot have columns with duplicate positions');
    }
  }

  /**
   * Validate column limit value
   * @throws {ValidationError} if limit is invalid
   */
  validateColumnLimit(limit: number | null | undefined): void {
    if (limit !== null && limit !== undefined && limit < 1) {
      throw new ValidationError('Column limit must be at least 1');
    }
  }

  /**
   * Validate that column has capacity for more items
   * @throws {ValidationError} if column is at capacity
   */
  validateColumnCapacity(column: Column): void {
    if (column.limit !== null && column.limit !== undefined) {
      if (column.items.length >= column.limit) {
        throw new ValidationError(
          `Column '${column.name}' is at capacity (${column.limit} items). Cannot add more items.`
        );
      }
    }
  }
}
