/**
 * Base exception class for all MKanban errors
 */
export class MKanbanError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MKanbanError';
    // Maintains proper stack trace for where error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

/**
 * Exception raised when validation fails
 */
export class ValidationError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Exception raised when an item is not found
 */
export class ItemNotFoundError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'ItemNotFoundError';
  }
}

/**
 * Exception raised when a column is not found
 */
export class ColumnNotFoundError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'ColumnNotFoundError';
  }
}

/**
 * Exception raised when a board is not found
 */
export class BoardNotFoundError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'BoardNotFoundError';
  }
}

/**
 * Exception raised when a storage operation fails
 */
export class StorageError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'StorageError';
  }
}

/**
 * Exception raised when a file operation fails
 */
export class FileOperationError extends StorageError {
  constructor(message: string) {
    super(message);
    this.name = 'FileOperationError';
  }
}

/**
 * Exception raised when parsing fails
 */
export class ParseError extends StorageError {
  constructor(message: string) {
    super(message);
    this.name = 'ParseError';
  }
}

/**
 * Exception raised when configuration is invalid
 */
export class ConfigurationError extends MKanbanError {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}
