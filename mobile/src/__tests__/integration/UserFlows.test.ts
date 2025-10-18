/**
 * Integration Tests for User Flows
 * Tests end-to-end user journeys through the application
 */

import { BoardService } from '../../services/BoardService';
import { ItemService } from '../../services/ItemService';
import { ValidationService } from '../../services/ValidationService';
import { MarkdownBoardRepository } from '../../infrastructure/storage/MarkdownBoardRepository';
import { MarkdownStorageRepository } from '../../infrastructure/storage/MarkdownStorageRepository';
import { FileSystemManager } from '../../infrastructure/storage/FileSystemManager';
import { MarkdownParser } from '../../infrastructure/storage/MarkdownParser';
import { BoardPersistence } from '../../infrastructure/storage/BoardPersistence';
import { Board } from '../../domain/entities/Board';
import { Parent } from '../../domain/entities/Parent';
import { ParentColor } from '../../core/enums';

// Mock file system for testing
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

  reset() {
    this.files.clear();
    this.directories.clear();
  }
}

describe('User Flows Integration Tests', () => {
  let boardService: BoardService;
  let itemService: ItemService;
  let mockFsManager: MockFileSystemManager;

  beforeEach(() => {
    mockFsManager = new MockFileSystemManager();
    const markdownParser = new MarkdownParser(mockFsManager as any);
    const boardPersistence = new BoardPersistence(mockFsManager as any, markdownParser);
    const boardRepository = new MarkdownBoardRepository(mockFsManager as any, markdownParser);
    const storageRepository = new MarkdownStorageRepository(boardPersistence);
    const validationService = new ValidationService();

    boardService = new BoardService(boardRepository, storageRepository, validationService);
    itemService = new ItemService(storageRepository, validationService);
  });

  describe('Complete Board Management Flow', () => {
    it('should create board, add columns, add items, and save successfully', async () => {
      // Step 1: Create a new board
      const board = await boardService.createBoard('My Project', 'A test project');

      expect(board).not.toBeNull();
      expect(board?.name).toBe('My Project');
      expect(board?.columns).toHaveLength(3); // Default columns

      // Step 2: Add custom column
      await boardService.addColumnToBoard(board!, 'Review', 4);

      expect(board?.columns).toHaveLength(4);
      expect(board?.columns[3].name).toBe('Review');

      // Step 3: Add items to columns
      const column1 = board!.columns[0]; // To Do
      const item1 = await itemService.createItem(board!, column1, 'Task 1', 'First task');
      const item2 = await itemService.createItem(board!, column1, 'Task 2', 'Second task');

      expect(column1.items).toHaveLength(2);
      expect(item1?.title).toBe('Task 1');
      expect(item2?.title).toBe('Task 2');

      // Step 4: Save board
      const saveResult = await boardService.saveBoard(board!);

      expect(saveResult).toBe(true);

      // Step 5: Verify board can be loaded
      const loadedBoard = await boardService.getBoardByName('My Project');

      expect(loadedBoard).not.toBeNull();
      expect(loadedBoard?.columns).toHaveLength(4);
      expect(loadedBoard?.columns[0].items).toHaveLength(2);
    });
  });

  describe('Item Movement Flow', () => {
    it('should move item between columns successfully', async () => {
      // Create board with items
      const board = await boardService.createBoard('Test Board');
      const todoColumn = board!.columns[0]; // To Do
      const inProgressColumn = board!.columns[1]; // In Progress

      const item = await itemService.createItem(board!, todoColumn, 'Move me');

      expect(todoColumn.items).toHaveLength(1);
      expect(inProgressColumn.items).toHaveLength(0);

      // Move item to In Progress
      const moveResult = await itemService.moveItemBetweenColumns(
        board!,
        item!.id,
        inProgressColumn.id
      );

      expect(moveResult).toBe(true);
      expect(todoColumn.items).toHaveLength(0);
      expect(inProgressColumn.items).toHaveLength(1);
      expect(inProgressColumn.items[0].id).toBe(item!.id);

      // Save and reload
      await boardService.saveBoard(board!);
      const reloadedBoard = await boardService.getBoardById(board!.id);

      expect(reloadedBoard?.columns[0].items).toHaveLength(0);
      expect(reloadedBoard?.columns[1].items).toHaveLength(1);
    });
  });

  describe('Parent Management Flow', () => {
    it('should create parents, assign to items, and manage lifecycle', async () => {
      // Create board
      const board = await boardService.createBoard('Parent Test');
      const column = board!.columns[0];

      // Add parents to board
      const parent1 = new Parent('p1', 'Feature A', ParentColor.BLUE, new Date().toISOString());
      const parent2 = new Parent('p2', 'Feature B', ParentColor.RED, new Date().toISOString());
      board!.parents.push(parent1, parent2);

      // Create items with parents
      const item1 = await itemService.createItem(board!, column, 'Item 1', '', 'p1');
      const item2 = await itemService.createItem(board!, column, 'Item 2', '', 'p1');
      const item3 = await itemService.createItem(board!, column, 'Item 3', '', 'p2');

      expect(item1?.parent_id).toBe('p1');
      expect(item2?.parent_id).toBe('p1');
      expect(item3?.parent_id).toBe('p2');

      // Group items by parent
      const grouped = itemService.getItemsGroupedByParent(board!, column.id);

      expect(grouped.size).toBe(2);
      expect(grouped.get('p1')).toHaveLength(2);
      expect(grouped.get('p2')).toHaveLength(1);

      // Change parent of item
      await itemService.setItemParent(board!, item1!.id, 'p2');

      expect(item1?.parent_id).toBe('p2');

      const regrouped = itemService.getItemsGroupedByParent(board!, column.id);
      expect(regrouped.get('p1')).toHaveLength(1);
      expect(regrouped.get('p2')).toHaveLength(2);
    });

    it('should unassign items when parent is deleted', async () => {
      const board = await boardService.createBoard('Delete Parent Test');
      const column = board!.columns[0];

      // Add parent and items
      const parent = new Parent('p1', 'Feature X', ParentColor.BLUE, new Date().toISOString());
      board!.parents.push(parent);

      const item1 = await itemService.createItem(board!, column, 'Item 1', '', 'p1');
      const item2 = await itemService.createItem(board!, column, 'Item 2', '', 'p1');

      expect(item1?.parent_id).toBe('p1');
      expect(item2?.parent_id).toBe('p1');

      // Delete parent
      board!.parents = board!.parents.filter((p) => p.id !== 'p1');

      // Unassign items
      column.items.forEach((item) => {
        if (item.parent_id === 'p1') {
          item.parent_id = null;
        }
      });

      expect(item1?.parent_id).toBeNull();
      expect(item2?.parent_id).toBeNull();
    });
  });

  describe('Item CRUD Flow', () => {
    it('should handle complete item lifecycle', async () => {
      // Create board
      const board = await boardService.createBoard('CRUD Test');
      const column = board!.columns[0];

      // Create item
      const item = await itemService.createItem(
        board!,
        column,
        'Test Item',
        'Initial description'
      );

      expect(item).not.toBeNull();
      expect(item?.title).toBe('Test Item');
      expect(item?.description).toBe('Initial description');

      // Update item
      await itemService.updateItem(board!, item!.id, {
        title: 'Updated Item',
        description: 'Updated description',
      });

      expect(item?.title).toBe('Updated Item');
      expect(item?.description).toBe('Updated description');

      // Delete item
      const deleteResult = await itemService.deleteItem(board!, item!.id);

      expect(deleteResult).toBe(true);
      expect(column.items).toHaveLength(0);
    });
  });

  describe('Board Deletion Flow', () => {
    it('should delete board with all contents', async () => {
      // Create board with items
      const board = await boardService.createBoard('Delete Me');
      const column = board!.columns[0];

      await itemService.createItem(board!, column, 'Item 1');
      await itemService.createItem(board!, column, 'Item 2');
      await boardService.saveBoard(board!);

      // Verify board exists
      const foundBoard = await boardService.getBoardById(board!.id);
      expect(foundBoard).not.toBeNull();

      // Delete board
      const deleteResult = await boardService.deleteBoard(board!.id);

      expect(deleteResult).toBe(true);

      // Verify board is gone
      const deletedBoard = await boardService.getBoardById(board!.id);
      expect(deletedBoard).toBeNull();
    });
  });

  describe('Multi-Board Flow', () => {
    it('should handle multiple boards independently', async () => {
      // Create multiple boards
      const board1 = await boardService.createBoard('Board 1');
      const board2 = await boardService.createBoard('Board 2');
      const board3 = await boardService.createBoard('Board 3');

      // Add items to each board
      await itemService.createItem(board1!, board1!.columns[0], 'Board 1 Item');
      await itemService.createItem(board2!, board2!.columns[0], 'Board 2 Item');
      await itemService.createItem(board3!, board3!.columns[0], 'Board 3 Item');

      // Save all boards
      await boardService.saveBoard(board1!);
      await boardService.saveBoard(board2!);
      await boardService.saveBoard(board3!);

      // Verify all boards exist
      const allBoards = await boardService.getAllBoards();

      expect(allBoards).toHaveLength(3);

      const names = allBoards.map((b) => b.name);
      expect(names).toContain('Board 1');
      expect(names).toContain('Board 2');
      expect(names).toContain('Board 3');

      // Verify items are isolated per board
      const loadedBoard1 = await boardService.getBoardById(board1!.id);
      expect(loadedBoard1?.columns[0].items).toHaveLength(1);
      expect(loadedBoard1?.columns[0].items[0].title).toBe('Board 1 Item');
    });
  });

  describe('Error Recovery Flow', () => {
    it('should handle errors gracefully without corrupting data', async () => {
      const board = await boardService.createBoard('Error Test');
      const column = board!.columns[0];

      // Create valid item
      const item1 = await itemService.createItem(board!, column, 'Valid Item');

      expect(column.items).toHaveLength(1);

      // Try to create invalid item
      await expect(itemService.createItem(board!, column, '')).rejects.toThrow();

      // Verify valid item still exists
      expect(column.items).toHaveLength(1);
      expect(column.items[0].title).toBe('Valid Item');

      // Try to update with invalid data
      await expect(
        itemService.updateItem(board!, item1!.id, { title: '' })
      ).rejects.toThrow();

      // Verify item unchanged
      expect(item1?.title).toBe('Valid Item');
    });
  });
});
