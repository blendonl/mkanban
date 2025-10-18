/**
 * FileChangeDetector.ts
 *
 * Detects changes in the file system by comparing file modification times.
 * Used by FileWatcher to track board/column/item changes.
 */

import { File, Directory } from 'expo-file-system';

export interface FileState {
  path: string;
  modifiedTime: number;
  isDirectory: boolean;
}

export interface FileChange {
  path: string;
  type: 'added' | 'modified' | 'deleted';
  isDirectory: boolean;
}

export class FileChangeDetector {
  private previousState: Map<string, FileState> = new Map();

  /**
   * Scan a directory and return current file states
   */
  async scanDirectory(dirPath: string): Promise<Map<string, FileState>> {
    const fileStates = new Map<string, FileState>();

    try {
      const dir = new Directory(dirPath);

      if (!dir.exists) {
        return fileStates;
      }

      // Recursively scan directory
      await this._scanRecursive(dirPath, fileStates);
    } catch (error) {
      console.error(`Error scanning directory ${dirPath}:`, error);
    }

    return fileStates;
  }

  /**
   * Recursively scan directories and collect file states
   */
  private async _scanRecursive(
    dirPath: string,
    fileStates: Map<string, FileState>
  ): Promise<void> {
    try {
      const dir = new Directory(dirPath);
      const items = dir.list();

      for (const item of items) {
        const itemPath = item.uri;
        const isDirectory = item instanceof Directory;

        // Get modification time from file/directory
        let modifiedTime = 0;
        if (item instanceof File) {
          modifiedTime = item.modificationTime || 0;
        } else if (item instanceof Directory) {
          // For directories, we can try to get info, but may not have modificationTime
          // Use 0 as default for directories
          modifiedTime = 0;
        }

        fileStates.set(itemPath, {
          path: itemPath,
          modifiedTime,
          isDirectory,
        });

        // Recursively scan subdirectories
        if (isDirectory) {
          await this._scanRecursive(itemPath, fileStates);
        }
      }
    } catch (error) {
      console.error(`Error scanning directory ${dirPath}:`, error);
    }
  }

  /**
   * Compare current state with previous state and detect changes
   */
  detectChanges(currentState: Map<string, FileState>): FileChange[] {
    const changes: FileChange[] = [];

    // Find added and modified files
    for (const [path, current] of currentState.entries()) {
      const previous = this.previousState.get(path);

      if (!previous) {
        // File was added
        changes.push({
          path,
          type: 'added',
          isDirectory: current.isDirectory,
        });
      } else if (current.modifiedTime !== previous.modifiedTime) {
        // File was modified
        changes.push({
          path,
          type: 'modified',
          isDirectory: current.isDirectory,
        });
      }
    }

    // Find deleted files
    for (const [path, previous] of this.previousState.entries()) {
      if (!currentState.has(path)) {
        changes.push({
          path,
          type: 'deleted',
          isDirectory: previous.isDirectory,
        });
      }
    }

    return changes;
  }

  /**
   * Update the previous state to the current state
   */
  updateState(currentState: Map<string, FileState>): void {
    this.previousState = new Map(currentState);
  }

  /**
   * Reset the detector state
   */
  reset(): void {
    this.previousState.clear();
  }

  /**
   * Get the current tracked state
   */
  getState(): Map<string, FileState> {
    return new Map(this.previousState);
  }
}
