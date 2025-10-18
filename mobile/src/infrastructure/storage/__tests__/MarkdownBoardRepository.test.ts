/**
 * Unit Tests for MarkdownBoardRepository
 */

import { MarkdownBoardRepository } from '../MarkdownBoardRepository';
import { FileSystemManager } from '../FileSystemManager';
import { MarkdownParser } from '../MarkdownParser';
import { Board } from '../../../domain/entities/Board';
import { Column } from '../../../domain/entities/Column';
import { Item } from '../../../domain/entities/Item';
import { Parent } from '../../../domain/entities/Parent';
import { ParentColor } from '../../../core/enums';

// Mock FileSystemManager
class MockFileSystemManager {
  private files: Map<string, string> = new Map();
  private directories: Set<string> = new Set();

  getBoardsDirectory(): string {
    return '/test/boards/';
  }

  getBoardDirectory(boardName: string): string {
    return `/test/boards/${boardName}/`;
  }

  getColumnDirectory(boardName: string, columnName: string): string {
    return `/test/boards/${boardName}/${columnName}/`;
  }

  async ensureDirectoryExists(path: string): Promise<void> {
    this.directories.add(path);
  }

  async readFile(path: string): Promise<string> {
    const content = this.files.get(path);
    if (!content) {
      throw new Error(`File not found: ${path}`);
    }
    return content;
  }

  async writeFile(path: string, content: string): Promise<void> {
    this.files.set(path, content);
  }

  async deleteFile(path: string): Promise<boolean> {
    return this.files.delete(path);
  }

  async deleteDirectory(path: string): Promise<boolean> {
    // Delete all files in directory
    const toDelete: string[] = [];
    for (const [filePath] of this.files) {
      if (filePath.startsWith(path)) {
        toDelete.push(filePath);
      }
    }
    toDelete.forEach((p) => this.files.delete(p));
    this.directories.delete(path);
    return true;
  }

  async listFiles(directory: string, pattern?: string): Promise<string[]> {
    const files: string[] = [];
    for (const [path] of this.files) {
      if (path.startsWith(directory)) {
        const filename = path.substring(directory.length);
        if (!pattern || filename.endsWith(pattern.replace('*', ''))) {
          files.push(path);
        }
      }
    }
    return files;
  }

  async listDirectories(directory: string): Promise<string[]> {
    const dirs: Set<string> = new Set();
    for (const path of this.directories) {
      if (path.startsWith(directory) && path !== directory) {
        // Get first subdirectory
        const relative = path.substring(directory.length);
        const firstSlash = relative.indexOf('/');
        if (firstSlash > 0) {
          dirs.add(directory + relative.substring(0, firstSlash + 1));
        }
      }
    }
    return Array.from(dirs);
  }

  async fileExists(path: string): Promise<boolean> {
    return this.files.has(path);
  }

  async directoryExists(path: string): Promise<boolean> {
    return this.directories.has(path);
  }

  // Helper methods for testing
  reset() {
    this.files.clear();
    this.directories.clear();
  }

  addFile(path: string, content: string) {
    this.files.set(path, content);
  }

  addDirectory(path: string) {
    this.directories.add(path);
  }
}

describe('MarkdownBoardRepository', () => {
  let repository: MarkdownBoardRepository;
  let mockFsManager: MockFileSystemManager;
  let markdownParser: MarkdownParser;

  beforeEach(() => {
    mockFsManager = new MockFileSystemManager();
    markdownParser = new MarkdownParser(mockFsManager as any);
    repository = new MarkdownBoardRepository(mockFsManager as any, markdownParser);
  });

  describe('loadAllBoards', () => {
    it('should return empty array when no boards exist', async () => {
      const boards = await repository.loadAllBoards();
      expect(boards).toEqual([]);
    });

    it('should load all boards from directory', async () => {
      // Create board 1
      mockFsManager.addDirectory('/test/boards/board1/');
      mockFsManager.addFile(
        '/test/boards/board1/kanban.md',
        `---
id: board1
name: Board 1
description: Test board 1
parents: []
created_at: 2025-10-15T10:00:00.000Z
---

# Board 1`
      );

      // Create board 2
      mockFsManager.addDirectory('/test/boards/board2/');
      mockFsManager.addFile(
        '/test/boards/board2/kanban.md',
        `---
id: board2
name: Board 2
parents: []
created_at: 2025-10-15T11:00:00.000Z
---

# Board 2`
      );

      const boards = await repository.loadAllBoards();

      expect(boards).toHaveLength(2);
      expect(boards[0].name).toBe('Board 1');
      expect(boards[1].name).toBe('Board 2');
    });

    it('should skip directories without kanban.md', async () => {
      mockFsManager.addDirectory('/test/boards/invalid/');
      // No kanban.md file

      const boards = await repository.loadAllBoards();

      expect(boards).toEqual([]);
    });
  });

  describe('loadBoardById', () => {
    it('should load board by ID', async () => {
      mockFsManager.addDirectory('/test/boards/test-board/');
      mockFsManager.addFile(
        '/test/boards/test-board/kanban.md',
        `---
id: test-board
name: Test Board
parents: []
created_at: 2025-10-15T10:00:00.000Z
---

# Test Board`
      );

      const board = await repository.loadBoardById('test-board');

      expect(board).not.toBeNull();
      expect(board?.id).toBe('test-board');
      expect(board?.name).toBe('Test Board');
    });

    it('should return null for non-existent board', async () => {
      const board = await repository.loadBoardById('nonexistent');
      expect(board).toBeNull();
    });
  });

  describe('loadBoardByName', () => {
    it('should load board by name', async () => {
      mockFsManager.addDirectory('/test/boards/test-board/');
      mockFsManager.addFile(
        '/test/boards/test-board/kanban.md',
        `---
id: test-board
name: Test Board
parents: []
created_at: 2025-10-15T10:00:00.000Z
---

# Test Board`
      );

      const board = await repository.loadBoardByName('Test Board');

      expect(board).not.toBeNull();
      expect(board?.name).toBe('Test Board');
    });

    it('should return null for non-existent board name', async () => {
      const board = await repository.loadBoardByName('Nonexistent');
      expect(board).toBeNull();
    });
  });

  describe('saveBoard', () => {
    it('should save board with kanban.md', async () => {
      const board = new Board('test-board', 'Test Board', [], []);

      const result = await repository.saveBoard(board);

      expect(result).toBe(true);
      const savedContent = await mockFsManager.readFile('/test/boards/test-board/kanban.md');
      expect(savedContent).toContain('id: test-board');
      expect(savedContent).toContain('name: Test Board');
    });

    it('should save board with columns', async () => {
      const column1 = new Column('col1', 'To Do', [], 1);
      const column2 = new Column('col2', 'Done', [], 2);
      const board = new Board('test', 'Test', [column1, column2], []);

      const result = await repository.saveBoard(board);

      expect(result).toBe(true);
      // Check column directories created
      expect(mockFsManager.directoryExists('/test/boards/test/to-do/')).resolves.toBe(true);
      expect(mockFsManager.directoryExists('/test/boards/test/done/')).resolves.toBe(true);
    });

    it('should save board with items', async () => {
      const item = new Item(
        'item-1',
        'Test Item',
        'Description',
        null,
        {},
        '2025-10-15T10:00:00.000Z'
      );
      const column = new Column('col1', 'To Do', [item], 1);
      const board = new Board('test', 'Test', [column], []);

      const result = await repository.saveBoard(board);

      expect(result).toBe(true);
      // Check item file created
      const files = await mockFsManager.listFiles('/test/boards/test/to-do/', '*.md');
      expect(files.length).toBeGreaterThan(0);
    });

    it('should save board with parents', async () => {
      const parent = new Parent('p1', 'Feature X', ParentColor.BLUE, '2025-10-15T10:00:00.000Z');
      const board = new Board('test', 'Test', [], [parent]);

      const result = await repository.saveBoard(board);

      expect(result).toBe(true);
      const savedContent = await mockFsManager.readFile('/test/boards/test/kanban.md');
      expect(savedContent).toContain('Feature X');
      expect(savedContent).toContain('blue');
    });
  });

  describe('deleteBoard', () => {
    it('should delete board directory', async () => {
      mockFsManager.addDirectory('/test/boards/test-board/');
      mockFsManager.addFile('/test/boards/test-board/kanban.md', '# Test');

      const result = await repository.deleteBoard('test-board');

      expect(result).toBe(true);
      expect(await mockFsManager.fileExists('/test/boards/test-board/kanban.md')).toBe(false);
    });

    it('should return false for non-existent board', async () => {
      const result = await repository.deleteBoard('nonexistent');
      expect(result).toBe(false);
    });
  });

  describe('listBoardNames', () => {
    it('should return list of board names', async () => {
      // Create boards
      mockFsManager.addDirectory('/test/boards/board1/');
      mockFsManager.addFile(
        '/test/boards/board1/kanban.md',
        `---
id: board1
name: Board One
parents: []
created_at: 2025-10-15T10:00:00.000Z
---

# Board One`
      );

      mockFsManager.addDirectory('/test/boards/board2/');
      mockFsManager.addFile(
        '/test/boards/board2/kanban.md',
        `---
id: board2
name: Board Two
parents: []
created_at: 2025-10-15T11:00:00.000Z
---

# Board Two`
      );

      const names = await repository.listBoardNames();

      expect(names).toHaveLength(2);
      expect(names).toContain('Board One');
      expect(names).toContain('Board Two');
    });

    it('should return empty array when no boards exist', async () => {
      const names = await repository.listBoardNames();
      expect(names).toEqual([]);
    });
  });

  describe('loadBoardFromFile', () => {
    it('should load board with all components', async () => {
      // Create board with columns and items
      mockFsManager.addDirectory('/test/boards/complex/');
      mockFsManager.addDirectory('/test/boards/complex/to-do/');

      mockFsManager.addFile(
        '/test/boards/complex/kanban.md',
        `---
id: complex
name: Complex Board
description: Test description
parents:
  - id: p1
    name: Feature X
    color: blue
    created_at: 2025-10-15T10:00:00.000Z
created_at: 2025-10-15T10:00:00.000Z
---

# Complex Board`
      );

      mockFsManager.addFile(
        '/test/boards/complex/to-do/item-1.md',
        `---
id: item-1
title: Test Item
parent_id: p1
created_at: 2025-10-15T10:00:00.000Z
---

# Test Item

Description here`
      );

      const board = await repository.loadBoardById('complex');

      expect(board).not.toBeNull();
      expect(board?.name).toBe('Complex Board');
      expect(board?.description).toBe('Test description');
      expect(board?.parents).toHaveLength(1);
      expect(board?.parents[0].name).toBe('Feature X');
      expect(board?.columns).toHaveLength(1);
      expect(board?.columns[0].items).toHaveLength(1);
      expect(board?.columns[0].items[0].title).toBe('Test Item');
    });
  });
});
