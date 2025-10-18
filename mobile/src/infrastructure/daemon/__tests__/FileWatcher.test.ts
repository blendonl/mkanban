/**
 * FileWatcher.test.ts
 *
 * Integration tests for FileWatcher
 */

import { FileWatcher, FileWatcherEvent } from '../FileWatcher';
import { FileSystemManager } from '../../storage/FileSystemManager';

// Mock FileSystemManager
jest.mock('../../storage/FileSystemManager');

describe('FileWatcher', () => {
  let fileWatcher: FileWatcher;
  let mockFileSystemManager: jest.Mocked<FileSystemManager>;

  beforeEach(() => {
    mockFileSystemManager = new FileSystemManager() as jest.Mocked<FileSystemManager>;
    fileWatcher = new FileWatcher(mockFileSystemManager, 100); // Use short interval for testing
  });

  afterEach(() => {
    fileWatcher.stop();
    fileWatcher.reset();
    jest.clearAllMocks();
  });

  describe('lifecycle', () => {
    it('should start and stop successfully', async () => {
      mockFileSystemManager.getBoardsDirectory.mockResolvedValue('/path/to/boards');

      await fileWatcher.start();
      expect(fileWatcher.isActive()).toBe(true);

      fileWatcher.stop();
      expect(fileWatcher.isActive()).toBe(false);
    });

    it('should not start if already running', async () => {
      mockFileSystemManager.getBoardsDirectory.mockResolvedValue('/path/to/boards');

      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      await fileWatcher.start();
      await fileWatcher.start(); // Second start

      expect(consoleSpy).toHaveBeenCalledWith('FileWatcher is already running');

      consoleSpy.mockRestore();
    });

    it('should not stop if not running', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      fileWatcher.stop();

      expect(consoleSpy).toHaveBeenCalledWith('FileWatcher is not running');

      consoleSpy.mockRestore();
    });

    it('should reset state', () => {
      fileWatcher.reset();
      expect(fileWatcher.isActive()).toBe(false);
    });
  });

  describe('event emission', () => {
    it('should emit boardAdded event', async () => {
      const events: FileWatcherEvent[] = [];
      fileWatcher.on('boardAdded', (event) => events.push(event));

      // Simulate board detection
      const event: FileWatcherEvent = {
        type: 'boardAdded',
        path: '/path/to/boards/my-board',
        boardName: 'my-board',
      };

      // Trigger event manually (we'll test full flow in integration tests)
      fileWatcher['emit']('boardAdded', event);

      expect(events).toHaveLength(1);
      expect(events[0]).toEqual(event);
    });

    it('should emit itemChanged event', () => {
      const events: FileWatcherEvent[] = [];
      fileWatcher.on('itemChanged', (event) => events.push(event));

      const event: FileWatcherEvent = {
        type: 'itemChanged',
        path: '/path/to/boards/my-board/to-do/item-1.md',
        boardName: 'my-board',
        columnName: 'to-do',
        itemId: 'item-1',
      };

      fileWatcher['emit']('itemChanged', event);

      expect(events).toHaveLength(1);
      expect(events[0]).toEqual(event);
    });

    it('should emit multiple events to multiple listeners', () => {
      const events1: FileWatcherEvent[] = [];
      const events2: FileWatcherEvent[] = [];

      fileWatcher.on('boardChanged', (event) => events1.push(event));
      fileWatcher.on('boardChanged', (event) => events2.push(event));

      const event: FileWatcherEvent = {
        type: 'boardChanged',
        path: '/path/to/boards/my-board/kanban.md',
        boardName: 'my-board',
      };

      fileWatcher['emit']('boardChanged', event);

      expect(events1).toHaveLength(1);
      expect(events2).toHaveLength(1);
    });

    it('should handle listener errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      fileWatcher.on('boardChanged', () => {
        throw new Error('Listener error');
      });

      const event: FileWatcherEvent = {
        type: 'boardChanged',
        path: '/path/to/boards/my-board/kanban.md',
        boardName: 'my-board',
      };

      fileWatcher['emit']('boardChanged', event);

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('listener management', () => {
    it('should register and unregister listeners', () => {
      const listener = jest.fn();

      fileWatcher.on('boardChanged', listener);
      fileWatcher.off('boardChanged', listener);

      const event: FileWatcherEvent = {
        type: 'boardChanged',
        path: '/path/to/boards/my-board/kanban.md',
        boardName: 'my-board',
      };

      fileWatcher['emit']('boardChanged', event);

      expect(listener).not.toHaveBeenCalled();
    });

    it('should remove all listeners for a specific event type', () => {
      const listener1 = jest.fn();
      const listener2 = jest.fn();

      fileWatcher.on('boardChanged', listener1);
      fileWatcher.on('boardChanged', listener2);

      fileWatcher.removeAllListeners('boardChanged');

      const event: FileWatcherEvent = {
        type: 'boardChanged',
        path: '/path/to/boards/my-board/kanban.md',
        boardName: 'my-board',
      };

      fileWatcher['emit']('boardChanged', event);

      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).not.toHaveBeenCalled();
    });

    it('should remove all listeners for all events', () => {
      const listener1 = jest.fn();
      const listener2 = jest.fn();

      fileWatcher.on('boardChanged', listener1);
      fileWatcher.on('itemChanged', listener2);

      fileWatcher.removeAllListeners();

      fileWatcher['emit']('boardChanged', {
        type: 'boardChanged',
        path: '/path',
        boardName: 'board',
      });
      fileWatcher['emit']('itemChanged', {
        type: 'itemChanged',
        path: '/path',
        boardName: 'board',
      });

      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).not.toHaveBeenCalled();
    });
  });

  describe('configuration', () => {
    it('should get and set polling interval', () => {
      expect(fileWatcher.getPollingInterval()).toBe(100);

      fileWatcher.setPollingInterval(5000);
      expect(fileWatcher.getPollingInterval()).toBe(5000);
    });

    it('should not allow changing polling interval while running', async () => {
      mockFileSystemManager.getBoardsDirectory.mockResolvedValue('/path/to/boards');

      await fileWatcher.start();

      expect(() => {
        fileWatcher.setPollingInterval(5000);
      }).toThrow('Cannot change polling interval while running. Stop the watcher first.');

      fileWatcher.stop();
    });
  });

  describe('parseFileChange', () => {
    beforeEach(() => {
      // Mock getBoardsDirectory to return consistent path
      mockFileSystemManager.getBoardsDirectory.mockReturnValue('/boards');
    });

    it('should parse board directory addition', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board',
        type: 'added',
        isDirectory: true,
      });

      expect(result).toEqual({
        type: 'boardAdded',
        path: '/boards/my-board',
        boardName: 'my-board',
      });
    });

    it('should parse board directory deletion', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board',
        type: 'deleted',
        isDirectory: true,
      });

      expect(result).toEqual({
        type: 'boardDeleted',
        path: '/boards/my-board',
        boardName: 'my-board',
      });
    });

    it('should parse kanban.md modification', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board/kanban.md',
        type: 'modified',
        isDirectory: false,
      });

      expect(result).toEqual({
        type: 'boardChanged',
        path: '/boards/my-board/kanban.md',
        boardName: 'my-board',
      });
    });

    it('should parse column metadata change', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board/to-do/column.md',
        type: 'modified',
        isDirectory: false,
      });

      expect(result).toEqual({
        type: 'columnChanged',
        path: '/boards/my-board/to-do/column.md',
        boardName: 'my-board',
        columnName: 'to-do',
      });
    });

    it('should parse item file addition', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board/to-do/item-1.md',
        type: 'added',
        isDirectory: false,
      });

      expect(result).toEqual({
        type: 'itemAdded',
        path: '/boards/my-board/to-do/item-1.md',
        boardName: 'my-board',
        columnName: 'to-do',
        itemId: 'item-1',
      });
    });

    it('should parse item file modification', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board/in-progress/MKA-123.md',
        type: 'modified',
        isDirectory: false,
      });

      expect(result).toEqual({
        type: 'itemChanged',
        path: '/boards/my-board/in-progress/MKA-123.md',
        boardName: 'my-board',
        columnName: 'in-progress',
        itemId: 'MKA-123',
      });
    });

    it('should parse item file deletion', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards/my-board/done/task-done.md',
        type: 'deleted',
        isDirectory: false,
      });

      expect(result).toEqual({
        type: 'itemDeleted',
        path: '/boards/my-board/done/task-done.md',
        boardName: 'my-board',
        columnName: 'done',
        itemId: 'task-done',
      });
    });

    it('should return null for unrecognized paths', () => {
      const result = fileWatcher['parseFileChange']({
        path: '/boards',
        type: 'modified',
        isDirectory: true,
      });

      expect(result).toBeNull();
    });
  });
});
