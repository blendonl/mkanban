import {
  MKanbanError,
  ValidationError,
  ItemNotFoundError,
  ColumnNotFoundError,
  BoardNotFoundError,
  StorageError,
  FileOperationError,
  ParseError,
  ConfigurationError,
} from '../exceptions';

describe('Exception Classes', () => {
  describe('MKanbanError', () => {
    it('should create error with correct message and name', () => {
      const error = new MKanbanError('Test error');
      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error.message).toBe('Test error');
      expect(error.name).toBe('MKanbanError');
    });

    it('should have stack trace', () => {
      const error = new MKanbanError('Test error');
      expect(error.stack).toBeDefined();
    });
  });

  describe('ValidationError', () => {
    it('should extend MKanbanError', () => {
      const error = new ValidationError('Validation failed');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.message).toBe('Validation failed');
      expect(error.name).toBe('ValidationError');
    });
  });

  describe('ItemNotFoundError', () => {
    it('should extend MKanbanError', () => {
      const error = new ItemNotFoundError('Item not found');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(ItemNotFoundError);
      expect(error.message).toBe('Item not found');
      expect(error.name).toBe('ItemNotFoundError');
    });
  });

  describe('ColumnNotFoundError', () => {
    it('should extend MKanbanError', () => {
      const error = new ColumnNotFoundError('Column not found');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(ColumnNotFoundError);
      expect(error.message).toBe('Column not found');
      expect(error.name).toBe('ColumnNotFoundError');
    });
  });

  describe('BoardNotFoundError', () => {
    it('should extend MKanbanError', () => {
      const error = new BoardNotFoundError('Board not found');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(BoardNotFoundError);
      expect(error.message).toBe('Board not found');
      expect(error.name).toBe('BoardNotFoundError');
    });
  });

  describe('StorageError', () => {
    it('should extend MKanbanError', () => {
      const error = new StorageError('Storage failed');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(StorageError);
      expect(error.message).toBe('Storage failed');
      expect(error.name).toBe('StorageError');
    });
  });

  describe('FileOperationError', () => {
    it('should extend StorageError', () => {
      const error = new FileOperationError('File operation failed');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(StorageError);
      expect(error).toBeInstanceOf(FileOperationError);
      expect(error.message).toBe('File operation failed');
      expect(error.name).toBe('FileOperationError');
    });
  });

  describe('ParseError', () => {
    it('should extend StorageError', () => {
      const error = new ParseError('Parse failed');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(StorageError);
      expect(error).toBeInstanceOf(ParseError);
      expect(error.message).toBe('Parse failed');
      expect(error.name).toBe('ParseError');
    });
  });

  describe('ConfigurationError', () => {
    it('should extend MKanbanError', () => {
      const error = new ConfigurationError('Config invalid');
      expect(error).toBeInstanceOf(MKanbanError);
      expect(error).toBeInstanceOf(ConfigurationError);
      expect(error.message).toBe('Config invalid');
      expect(error.name).toBe('ConfigurationError');
    });
  });

  describe('Error throwing and catching', () => {
    it('should be catchable as Error', () => {
      expect(() => {
        throw new ValidationError('Test');
      }).toThrow(Error);
    });

    it('should be catchable as MKanbanError', () => {
      expect(() => {
        throw new ValidationError('Test');
      }).toThrow(MKanbanError);
    });

    it('should be catchable by specific type', () => {
      expect(() => {
        throw new ValidationError('Test');
      }).toThrow(ValidationError);
    });

    it('should preserve error type in catch', () => {
      try {
        throw new ItemNotFoundError('Item XYZ not found');
      } catch (error) {
        expect(error).toBeInstanceOf(ItemNotFoundError);
        if (error instanceof ItemNotFoundError) {
          expect(error.message).toBe('Item XYZ not found');
        }
      }
    });
  });
});
