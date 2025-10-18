/**
 * Unit Tests for BoardService
 */

import { BoardService } from '../BoardService';
import { ValidationService } from '../ValidationService';
import { Board } from '../../domain/entities/Board';
import { Column } from '../../domain/entities/Column';
import { BoardRepository } from '../../domain/repositories/BoardRepository';
import { StorageRepository } from '../../domain/repositories/StorageRepository';

// Mock repositories
class MockBoardRepository implements BoardRepository {
  private boards: Map<string, Board> = new Map();

  async loadAllBoards(): Promise<Board[]> {
    return Array.from(this.boards.values());
  }

  async loadBoardById(boardId: string): Promise<Board | null> {
    return this.boards.get(boardId) || null;
  }

  async loadBoardByName(name: string): Promise<Board | null> {
    return Array.from(this.boards.values()).find((b) => b.name === name) || null;
  }

  async saveBoard(board: Board): Promise<boolean> {
    this.boards.set(board.id, board);
    return true;
  }

  async deleteBoard(boardId: string): Promise<boolean> {
    return this.boards.delete(boardId);
  }

  async listBoardNames(): Promise<string[]> {
    return Array.from(this.boards.values()).map((b) => b.name);
  }

  // Helper for testing
  reset() {
    this.boards.clear();
  }

  addBoard(board: Board) {
    this.boards.set(board.id, board);
  }
}

class MockStorageRepository implements StorageRepository {
  async deleteItemFromColumn(): Promise<boolean> {
    return true;
  }

  async moveItemBetweenColumns(): Promise<boolean> {
    return true;
  }

  async saveBoardToStorage(): Promise<boolean> {
    return true;
  }
}

describe('BoardService', () => {
  let boardService: BoardService;
  let mockBoardRepo: MockBoardRepository;
  let mockStorageRepo: MockStorageRepository;
  let validationService: ValidationService;

  beforeEach(() => {
    mockBoardRepo = new MockBoardRepository();
    mockStorageRepo = new MockStorageRepository();
    validationService = new ValidationService();
    boardService = new BoardService(mockBoardRepo, mockStorageRepo, validationService);
  });

  describe('getAllBoards', () => {
    it('should return all boards from repository', async () => {
      const board1 = new Board('board-1', 'Board 1', [], []);
      const board2 = new Board('board-2', 'Board 2', [], []);
      mockBoardRepo.addBoard(board1);
      mockBoardRepo.addBoard(board2);

      const boards = await boardService.getAllBoards();

      expect(boards).toHaveLength(2);
      expect(boards[0].id).toBe('board-1');
      expect(boards[1].id).toBe('board-2');
    });

    it('should return empty array when no boards exist', async () => {
      const boards = await boardService.getAllBoards();

      expect(boards).toHaveLength(0);
    });
  });

  describe('getBoardById', () => {
    it('should return board when it exists', async () => {
      const board = new Board('test-board', 'Test Board', [], []);
      mockBoardRepo.addBoard(board);

      const result = await boardService.getBoardById('test-board');

      expect(result).not.toBeNull();
      expect(result?.id).toBe('test-board');
      expect(result?.name).toBe('Test Board');
    });

    it('should return null when board does not exist', async () => {
      const result = await boardService.getBoardById('nonexistent');

      expect(result).toBeNull();
    });

    it('should throw error when boardId is empty', async () => {
      await expect(boardService.getBoardById('')).rejects.toThrow('Board ID cannot be empty');
    });
  });

  describe('getBoardByName', () => {
    it('should return board when it exists', async () => {
      const board = new Board('test-board', 'Test Board', [], []);
      mockBoardRepo.addBoard(board);

      const result = await boardService.getBoardByName('Test Board');

      expect(result).not.toBeNull();
      expect(result?.name).toBe('Test Board');
    });

    it('should return null when board does not exist', async () => {
      const result = await boardService.getBoardByName('Nonexistent');

      expect(result).toBeNull();
    });

    it('should throw error for invalid board name', async () => {
      await expect(boardService.getBoardByName('')).rejects.toThrow();
    });
  });

  describe('createBoard', () => {
    it('should create a new board with valid name', async () => {
      const board = await boardService.createBoard('New Board');

      expect(board).not.toBeNull();
      expect(board?.name).toBe('New Board');
      expect(board?.columns).toHaveLength(3); // Default columns
      expect(board?.columns[0].name).toBe('To Do');
      expect(board?.columns[1].name).toBe('In Progress');
      expect(board?.columns[2].name).toBe('Done');
    });

    it('should create board with description', async () => {
      const board = await boardService.createBoard('New Board', 'Test description');

      expect(board?.description).toBe('Test description');
    });

    it('should throw error for invalid board name', async () => {
      await expect(boardService.createBoard('')).rejects.toThrow();
    });

    it('should throw error for excessively long board name', async () => {
      const longName = 'a'.repeat(101);
      await expect(boardService.createBoard(longName)).rejects.toThrow();
    });
  });

  describe('saveBoard', () => {
    it('should save valid board', async () => {
      const board = new Board('test', 'Test', [], []);
      const result = await boardService.saveBoard(board);

      expect(result).toBe(true);
    });

    it('should throw error for invalid board', async () => {
      const invalidBoard = new Board('', '', [], []); // Empty name
      await expect(boardService.saveBoard(invalidBoard)).rejects.toThrow();
    });
  });

  describe('deleteBoard', () => {
    it('should delete existing board', async () => {
      const board = new Board('test', 'Test', [], []);
      mockBoardRepo.addBoard(board);

      const result = await boardService.deleteBoard('test');

      expect(result).toBe(true);
      const deletedBoard = await boardService.getBoardById('test');
      expect(deletedBoard).toBeNull();
    });

    it('should return false when board does not exist', async () => {
      const result = await boardService.deleteBoard('nonexistent');

      expect(result).toBe(false);
    });

    it('should throw error for empty board ID', async () => {
      await expect(boardService.deleteBoard('')).rejects.toThrow();
    });
  });

  describe('addColumnToBoard', () => {
    it('should add column with unique name', async () => {
      const board = new Board('test', 'Test', [], []);

      const result = await boardService.addColumnToBoard(board, 'Review');

      expect(result).toBe(true);
      expect(board.columns).toHaveLength(1);
      expect(board.columns[0].name).toBe('Review');
    });

    it('should assign correct position to new column', async () => {
      const board = new Board('test', 'Test', [], []);

      await boardService.addColumnToBoard(board, 'First', 1);
      await boardService.addColumnToBoard(board, 'Second', 2);

      expect(board.columns[0].position).toBe(1);
      expect(board.columns[1].position).toBe(2);
    });

    it('should throw error for duplicate column name', async () => {
      const board = new Board('test', 'Test', [], []);
      await boardService.addColumnToBoard(board, 'Review');

      await expect(boardService.addColumnToBoard(board, 'Review')).rejects.toThrow(
        'Column with name Review already exists'
      );
    });

    it('should throw error for invalid column name', async () => {
      const board = new Board('test', 'Test', [], []);

      await expect(boardService.addColumnToBoard(board, '')).rejects.toThrow();
    });
  });

  describe('removeColumnFromBoard', () => {
    it('should remove empty column', async () => {
      const column = new Column('col-1', 'Test Column', [], 1);
      const board = new Board('test', 'Test', [column], []);

      const result = await boardService.removeColumnFromBoard(board, 'col-1');

      expect(result).toBe(true);
      expect(board.columns).toHaveLength(0);
    });

    it('should throw error when removing column with items', async () => {
      const column = new Column('col-1', 'Test Column', [], 1);
      // Simulate adding an item
      column.items.push({
        id: 'item-1',
        title: 'Test Item',
        description: '',
        parent_id: null,
        metadata: {},
        created_at: new Date().toISOString(),
        getIssueType: () => 'Task',
        setIssueType: () => {},
        getIssueTypeIcon: () => '📋',
      } as any);

      const board = new Board('test', 'Test', [column], []);

      await expect(boardService.removeColumnFromBoard(board, 'col-1')).rejects.toThrow(
        'Cannot remove column with items'
      );
    });

    it('should throw error when column does not exist', async () => {
      const board = new Board('test', 'Test', [], []);

      await expect(boardService.removeColumnFromBoard(board, 'nonexistent')).rejects.toThrow(
        'Column with ID nonexistent not found'
      );
    });
  });

  describe('listBoardNames', () => {
    it('should return list of all board names', async () => {
      mockBoardRepo.addBoard(new Board('b1', 'Board 1', [], []));
      mockBoardRepo.addBoard(new Board('b2', 'Board 2', [], []));
      mockBoardRepo.addBoard(new Board('b3', 'Board 3', [], []));

      const names = await boardService.listBoardNames();

      expect(names).toHaveLength(3);
      expect(names).toContain('Board 1');
      expect(names).toContain('Board 2');
      expect(names).toContain('Board 3');
    });

    it('should return empty array when no boards exist', async () => {
      const names = await boardService.listBoardNames();

      expect(names).toHaveLength(0);
    });
  });
});
