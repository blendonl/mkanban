/**
 * FileChangeDetector.test.ts
 *
 * Unit tests for FileChangeDetector
 */

import { FileChangeDetector, FileState } from '../FileChangeDetector';

describe('FileChangeDetector', () => {
  let detector: FileChangeDetector;

  beforeEach(() => {
    detector = new FileChangeDetector();
  });

  describe('detectChanges', () => {
    it('should detect added files', () => {
      const previousState = new Map<string, FileState>();
      const currentState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
        [
          '/path/to/file2.md',
          { path: '/path/to/file2.md', modifiedTime: 2000, isDirectory: false },
        ],
      ]);

      detector.updateState(previousState);
      const changes = detector.detectChanges(currentState);

      expect(changes).toHaveLength(2);
      expect(changes[0]).toEqual({
        path: '/path/to/file1.md',
        type: 'added',
        isDirectory: false,
      });
      expect(changes[1]).toEqual({
        path: '/path/to/file2.md',
        type: 'added',
        isDirectory: false,
      });
    });

    it('should detect modified files', () => {
      const previousState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);
      const currentState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 2000, isDirectory: false },
        ],
      ]);

      detector.updateState(previousState);
      const changes = detector.detectChanges(currentState);

      expect(changes).toHaveLength(1);
      expect(changes[0]).toEqual({
        path: '/path/to/file1.md',
        type: 'modified',
        isDirectory: false,
      });
    });

    it('should detect deleted files', () => {
      const previousState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
        [
          '/path/to/file2.md',
          { path: '/path/to/file2.md', modifiedTime: 2000, isDirectory: false },
        ],
      ]);
      const currentState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(previousState);
      const changes = detector.detectChanges(currentState);

      expect(changes).toHaveLength(1);
      expect(changes[0]).toEqual({
        path: '/path/to/file2.md',
        type: 'deleted',
        isDirectory: false,
      });
    });

    it('should detect mixed changes', () => {
      const previousState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
        [
          '/path/to/file2.md',
          { path: '/path/to/file2.md', modifiedTime: 2000, isDirectory: false },
        ],
      ]);
      const currentState = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 3000, isDirectory: false }, // Modified
        ],
        [
          '/path/to/file3.md',
          { path: '/path/to/file3.md', modifiedTime: 4000, isDirectory: false }, // Added
        ],
        // file2.md is deleted
      ]);

      detector.updateState(previousState);
      const changes = detector.detectChanges(currentState);

      expect(changes).toHaveLength(3);

      const modifiedChange = changes.find((c) => c.type === 'modified');
      const addedChange = changes.find((c) => c.type === 'added');
      const deletedChange = changes.find((c) => c.type === 'deleted');

      expect(modifiedChange).toEqual({
        path: '/path/to/file1.md',
        type: 'modified',
        isDirectory: false,
      });
      expect(addedChange).toEqual({
        path: '/path/to/file3.md',
        type: 'added',
        isDirectory: false,
      });
      expect(deletedChange).toEqual({
        path: '/path/to/file2.md',
        type: 'deleted',
        isDirectory: false,
      });
    });

    it('should detect no changes when state is identical', () => {
      const state = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(state);
      const changes = detector.detectChanges(state);

      expect(changes).toHaveLength(0);
    });

    it('should handle directory changes', () => {
      const previousState = new Map<string, FileState>();
      const currentState = new Map<string, FileState>([
        [
          '/path/to/board',
          { path: '/path/to/board', modifiedTime: 1000, isDirectory: true },
        ],
      ]);

      detector.updateState(previousState);
      const changes = detector.detectChanges(currentState);

      expect(changes).toHaveLength(1);
      expect(changes[0]).toEqual({
        path: '/path/to/board',
        type: 'added',
        isDirectory: true,
      });
    });
  });

  describe('updateState', () => {
    it('should update internal state', () => {
      const state = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(state);
      const internalState = detector.getState();

      expect(internalState.size).toBe(1);
      expect(internalState.get('/path/to/file1.md')).toEqual({
        path: '/path/to/file1.md',
        modifiedTime: 1000,
        isDirectory: false,
      });
    });

    it('should create a copy of the state', () => {
      const state = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(state);

      // Modify original state
      state.set('/path/to/file2.md', {
        path: '/path/to/file2.md',
        modifiedTime: 2000,
        isDirectory: false,
      });

      // Internal state should not be affected
      const internalState = detector.getState();
      expect(internalState.size).toBe(1);
    });
  });

  describe('reset', () => {
    it('should clear all state', () => {
      const state = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(state);
      detector.reset();

      const internalState = detector.getState();
      expect(internalState.size).toBe(0);
    });
  });

  describe('getState', () => {
    it('should return a copy of the state', () => {
      const state = new Map<string, FileState>([
        [
          '/path/to/file1.md',
          { path: '/path/to/file1.md', modifiedTime: 1000, isDirectory: false },
        ],
      ]);

      detector.updateState(state);
      const returnedState = detector.getState();

      // Modify returned state
      returnedState.set('/path/to/file2.md', {
        path: '/path/to/file2.md',
        modifiedTime: 2000,
        isDirectory: false,
      });

      // Internal state should not be affected
      const internalState = detector.getState();
      expect(internalState.size).toBe(1);
    });
  });
});
