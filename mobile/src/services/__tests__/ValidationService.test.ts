import { ValidationService } from '../ValidationService';
import { ValidationError } from '../../core/exceptions';
import { Board } from '../../domain/entities/Board';
import { Column } from '../../domain/entities/Column';

describe('ValidationService', () => {
  let service: ValidationService;

  beforeEach(() => {
    service = new ValidationService();
  });

  describe('validateBoardName', () => {
    it('should accept valid board names', () => {
      expect(() => service.validateBoardName('My Board')).not.toThrow();
      expect(() => service.validateBoardName('project-2024')).not.toThrow();
      expect(() => service.validateBoardName('a')).not.toThrow();
    });

    it('should reject empty names', () => {
      expect(() => service.validateBoardName('')).toThrow(ValidationError);
      expect(() => service.validateBoardName('   ')).toThrow(ValidationError);
      expect(() => service.validateBoardName('')).toThrow('Board name cannot be empty');
    });

    it('should reject names over 100 characters', () => {
      const longName = 'a'.repeat(101);
      expect(() => service.validateBoardName(longName)).toThrow(ValidationError);
      expect(() => service.validateBoardName(longName)).toThrow(
        'Board name cannot exceed 100 characters'
      );
    });

    it('should reject names with invalid characters', () => {
      const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
      invalidChars.forEach((char) => {
        expect(() => service.validateBoardName(`board${char}name`)).toThrow(ValidationError);
      });
    });

    it('should accept names at exactly 100 characters', () => {
      const maxName = 'a'.repeat(100);
      expect(() => service.validateBoardName(maxName)).not.toThrow();
    });
  });

  describe('validateColumnName', () => {
    it('should accept valid column names', () => {
      expect(() => service.validateColumnName('To Do')).not.toThrow();
      expect(() => service.validateColumnName('in-progress')).not.toThrow();
      expect(() => service.validateColumnName('Done')).not.toThrow();
    });

    it('should reject empty names', () => {
      expect(() => service.validateColumnName('')).toThrow(ValidationError);
      expect(() => service.validateColumnName('   ')).toThrow(ValidationError);
      expect(() => service.validateColumnName('')).toThrow('Column name cannot be empty');
    });

    it('should reject names over 50 characters', () => {
      const longName = 'a'.repeat(51);
      expect(() => service.validateColumnName(longName)).toThrow(ValidationError);
      expect(() => service.validateColumnName(longName)).toThrow(
        'Column name cannot exceed 50 characters'
      );
    });

    it('should accept names at exactly 50 characters', () => {
      const maxName = 'a'.repeat(50);
      expect(() => service.validateColumnName(maxName)).not.toThrow();
    });
  });

  describe('validateItemTitle', () => {
    it('should accept valid item titles', () => {
      expect(() => service.validateItemTitle('Fix bug')).not.toThrow();
      expect(() => service.validateItemTitle('Implement feature X')).not.toThrow();
    });

    it('should reject empty titles', () => {
      expect(() => service.validateItemTitle('')).toThrow(ValidationError);
      expect(() => service.validateItemTitle('   ')).toThrow(ValidationError);
      expect(() => service.validateItemTitle('')).toThrow('Item title cannot be empty');
    });

    it('should reject titles over 200 characters', () => {
      const longTitle = 'a'.repeat(201);
      expect(() => service.validateItemTitle(longTitle)).toThrow(ValidationError);
      expect(() => service.validateItemTitle(longTitle)).toThrow(
        'Item title cannot exceed 200 characters'
      );
    });

    it('should accept titles at exactly 200 characters', () => {
      const maxTitle = 'a'.repeat(200);
      expect(() => service.validateItemTitle(maxTitle)).not.toThrow();
    });
  });

  describe('validateBoard', () => {
    it('should accept valid boards', () => {
      const board = new Board('My Project', 'Description');
      board.addColumn('To Do');
      expect(() => service.validateBoard(board)).not.toThrow();
    });

    it('should reject boards with invalid names', () => {
      const board = new Board('', 'Description');
      board.addColumn('To Do');
      expect(() => service.validateBoard(board)).toThrow(ValidationError);
    });

    it('should reject boards with no columns', () => {
      const board = new Board('My Project', 'Description');
      expect(() => service.validateBoard(board)).toThrow(ValidationError);
      expect(() => service.validateBoard(board)).toThrow('Board must have at least one column');
    });

    it('should reject boards with duplicate column names (case-insensitive)', () => {
      const board = new Board('My Project', 'Description');
      board.addColumn('To Do');
      board.addColumn('to do'); // Same name, different case
      expect(() => service.validateBoard(board)).toThrow(ValidationError);
      expect(() => service.validateBoard(board)).toThrow(
        'Board cannot have duplicate column names'
      );
    });

    it('should reject boards with duplicate positions', () => {
      const board = new Board('My Project', 'Description');
      const col1 = board.addColumn('To Do', 1);
      const col2 = board.addColumn('In Progress', 1); // Same position
      expect(() => service.validateBoard(board)).toThrow(ValidationError);
      expect(() => service.validateBoard(board)).toThrow(
        'Board cannot have columns with duplicate positions'
      );
    });

    it('should accept boards with unique column names', () => {
      const board = new Board('My Project', 'Description');
      board.addColumn('To Do');
      board.addColumn('In Progress');
      board.addColumn('Done');
      expect(() => service.validateBoard(board)).not.toThrow();
    });
  });

  describe('validateColumnLimit', () => {
    it('should accept null and undefined limits', () => {
      expect(() => service.validateColumnLimit(null)).not.toThrow();
      expect(() => service.validateColumnLimit(undefined)).not.toThrow();
    });

    it('should accept valid limits', () => {
      expect(() => service.validateColumnLimit(1)).not.toThrow();
      expect(() => service.validateColumnLimit(5)).not.toThrow();
      expect(() => service.validateColumnLimit(100)).not.toThrow();
    });

    it('should reject limits less than 1', () => {
      expect(() => service.validateColumnLimit(0)).toThrow(ValidationError);
      expect(() => service.validateColumnLimit(-1)).toThrow(ValidationError);
      expect(() => service.validateColumnLimit(0)).toThrow('Column limit must be at least 1');
    });
  });

  describe('validateColumnCapacity', () => {
    it('should accept columns without limits', () => {
      const column = new Column('To Do', 0);
      column.addItem('Task 1');
      column.addItem('Task 2');
      expect(() => service.validateColumnCapacity(column)).not.toThrow();
    });

    it('should accept columns below capacity', () => {
      const column = new Column('To Do', 0);
      column.limit = 5;
      column.addItem('Task 1');
      column.addItem('Task 2');
      expect(() => service.validateColumnCapacity(column)).not.toThrow();
    });

    it('should reject columns at capacity', () => {
      const column = new Column('To Do', 0);
      column.limit = 2;
      column.addItem('Task 1');
      column.addItem('Task 2');
      expect(() => service.validateColumnCapacity(column)).toThrow(ValidationError);
      expect(() => service.validateColumnCapacity(column)).toThrow(
        "Column 'To Do' is at capacity (2 items). Cannot add more items."
      );
    });

    it('should reject columns over capacity', () => {
      const column = new Column('To Do', 0);
      column.limit = 1;
      column.addItem('Task 1');
      column.addItem('Task 2');
      expect(() => service.validateColumnCapacity(column)).toThrow(ValidationError);
    });
  });
});
