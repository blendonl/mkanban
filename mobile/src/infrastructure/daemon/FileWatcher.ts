/**
 * FileWatcher.ts
 *
 * Background file watcher for detecting changes to board markdown files.
 * Polls the boards directory and emits events when files are added, modified, or deleted.
 *
 * Events:
 * - boardChanged: Board file (kanban.md) was modified
 * - boardAdded: New board directory was created
 * - boardDeleted: Board directory was deleted
 * - itemChanged: Item file was modified
 * - itemAdded: Item file was created
 * - itemDeleted: Item file was deleted
 * - columnChanged: Column metadata changed
 */

import { FileChangeDetector, FileChange } from './FileChangeDetector';
import { FileSystemManager } from '../storage/FileSystemManager';
import { KANBAN_FILE } from '../../core/constants';

export type FileWatcherEventType =
  | 'boardChanged'
  | 'boardAdded'
  | 'boardDeleted'
  | 'itemChanged'
  | 'itemAdded'
  | 'itemDeleted'
  | 'columnChanged';

export interface FileWatcherEvent {
  type: FileWatcherEventType;
  path: string;
  boardName?: string;
  columnName?: string;
  itemId?: string;
}

type EventListener = (event: FileWatcherEvent) => void;

export class FileWatcher {
  private detector: FileChangeDetector;
  private fileSystemManager: FileSystemManager;
  private listeners: Map<FileWatcherEventType, Set<EventListener>> = new Map();
  private pollingInterval: number = 3000; // 3 seconds default
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning: boolean = false;

  constructor(
    fileSystemManager: FileSystemManager,
    pollingInterval: number = 3000
  ) {
    this.fileSystemManager = fileSystemManager;
    this.detector = new FileChangeDetector();
    this.pollingInterval = pollingInterval;
  }

  /**
   * Start watching for file changes
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.warn('FileWatcher is already running');
      return;
    }

    this.isRunning = true;

    // Initial scan to establish baseline
    const boardsDir = await this.fileSystemManager.getBoardsDirectory();
    const initialState = await this.detector.scanDirectory(boardsDir);
    this.detector.updateState(initialState);

    // Start polling
    this.intervalId = setInterval(() => {
      this.checkForChanges();
    }, this.pollingInterval);

    console.log(`FileWatcher started (polling every ${this.pollingInterval}ms)`);
  }

  /**
   * Stop watching for file changes
   */
  stop(): void {
    if (!this.isRunning) {
      console.warn('FileWatcher is not running');
      return;
    }

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    this.isRunning = false;
    console.log('FileWatcher stopped');
  }

  /**
   * Check for changes in the boards directory
   */
  async checkForChanges(): Promise<void> {
    try {
      const boardsDir = await this.fileSystemManager.getBoardsDirectory();
      const currentState = await this.detector.scanDirectory(boardsDir);
      const changes = this.detector.detectChanges(currentState);

      if (changes.length > 0) {
        console.log(`Detected ${changes.length} file changes`);
        this.processChanges(changes);
      }

      // Update state for next check
      this.detector.updateState(currentState);
    } catch (error) {
      console.error('Error checking for file changes:', error);
    }
  }

  /**
   * Process file changes and emit appropriate events
   */
  private processChanges(changes: FileChange[]): void {
    for (const change of changes) {
      const event = this.parseFileChange(change);
      if (event) {
        this.emit(event.type, event);
      }
    }
  }

  /**
   * Parse a file change and determine the event type
   */
  private parseFileChange(change: FileChange): FileWatcherEvent | null {
    const { path, type, isDirectory } = change;

    // Parse path components: /path/to/boards/{boardName}/{columnName?}/{fileName?}
    const boardsDir = this.fileSystemManager.getBoardsDirectory();
    const relativePath = path.replace(`${boardsDir}/`, '');
    const parts = relativePath.split('/');

    if (parts.length === 0) {
      return null;
    }

    const boardName = parts[0];

    // Board directory change
    if (parts.length === 1 && isDirectory) {
      if (type === 'added') {
        return { type: 'boardAdded', path, boardName };
      } else if (type === 'deleted') {
        return { type: 'boardDeleted', path, boardName };
      }
      return null;
    }

    // Board file (kanban.md) change
    if (parts.length === 2 && parts[1] === KANBAN_FILE) {
      if (type === 'modified') {
        return { type: 'boardChanged', path, boardName };
      }
      return null;
    }

    // Column directory or item file change
    if (parts.length >= 2) {
      const columnName = parts[1];

      // Column metadata change (column.md)
      if (parts.length === 3 && parts[2] === 'column.md') {
        if (type === 'modified' || type === 'added') {
          return { type: 'columnChanged', path, boardName, columnName };
        }
        return null;
      }

      // Item file change
      if (parts.length === 3 && parts[2].endsWith('.md') && parts[2] !== 'column.md') {
        const fileName = parts[2];
        const itemId = fileName.replace('.md', '');

        if (type === 'added') {
          return { type: 'itemAdded', path, boardName, columnName, itemId };
        } else if (type === 'modified') {
          return { type: 'itemChanged', path, boardName, columnName, itemId };
        } else if (type === 'deleted') {
          return { type: 'itemDeleted', path, boardName, columnName, itemId };
        }
      }
    }

    return null;
  }

  /**
   * Register an event listener
   */
  on(eventType: FileWatcherEventType, listener: EventListener): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(listener);
  }

  /**
   * Unregister an event listener
   */
  off(eventType: FileWatcherEventType, listener: EventListener): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * Emit an event to all registered listeners
   */
  private emit(eventType: FileWatcherEventType, event: FileWatcherEvent): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(event);
        } catch (error) {
          console.error(`Error in ${eventType} listener:`, error);
        }
      });
    }
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(eventType?: FileWatcherEventType): void {
    if (eventType) {
      this.listeners.delete(eventType);
    } else {
      this.listeners.clear();
    }
  }

  /**
   * Get current running status
   */
  isActive(): boolean {
    return this.isRunning;
  }

  /**
   * Set polling interval (must be stopped first)
   */
  setPollingInterval(milliseconds: number): void {
    if (this.isRunning) {
      throw new Error('Cannot change polling interval while running. Stop the watcher first.');
    }
    this.pollingInterval = milliseconds;
  }

  /**
   * Get current polling interval
   */
  getPollingInterval(): number {
    return this.pollingInterval;
  }

  /**
   * Force a manual check (useful for testing)
   */
  async forceCheck(): Promise<void> {
    await this.checkForChanges();
  }

  /**
   * Reset the watcher state
   */
  reset(): void {
    this.stop();
    this.detector.reset();
    this.removeAllListeners();
  }
}
