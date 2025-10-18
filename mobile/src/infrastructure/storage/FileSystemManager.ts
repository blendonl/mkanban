/**
 * File System Manager for MKanban mobile app
 * Wraps expo-file-system operations and provides utility methods
 * Ported from Python: src/utils/file_utils.py and pathlib.Path operations
 */

import { File, Directory, Paths } from "expo-file-system";
import { getSafeFilename } from "../../utils/stringUtils";

export class FileSystemManager {
  private baseDirectory: string;

  constructor(baseDirectory?: string) {
    // Use expo's document directory as base, or custom directory for testing
    this.baseDirectory = baseDirectory || Paths.document.uri;
  }

  /**
   * Get the boards root directory path
   */
  getBoardsDirectory(): string {
    return `${this.baseDirectory}boards/`;
  }

  /**
   * Get a specific board's directory path
   */
  getBoardDirectory(boardName: string): string {
    const safeFilename = getSafeFilename(boardName);
    return `${this.getBoardsDirectory()}${safeFilename}/`;
  }

  /**
   * Get a column directory path within a board
   */
  getColumnDirectory(boardName: string, columnName: string): string {
    const boardDir = this.getBoardDirectory(boardName);
    const safeFilename = getSafeFilename(columnName);
    return `${boardDir}${safeFilename}/`;
  }

  /**
   * Ensure a directory exists, creating it recursively if needed
   * Equivalent to Python's Path.mkdir(parents=True, exist_ok=True)
   */
  async ensureDirectoryExists(path: string): Promise<void> {
    try {
      const dir = new Directory(path);
      if (!dir.exists) {
        dir.create({ intermediates: true, idempotent: true });
      }
    } catch (error) {
      throw new Error(`Failed to create directory ${path}: ${error}`);
    }
  }

  /**
   * Read file contents as a string
   * Equivalent to Python's open(file, 'r').read()
   */
  async readFile(path: string): Promise<string> {
    try {
      const file = new File(path);
      if (!file.exists) {
        throw new Error(`File does not exist: ${path}`);
      }
      return await file.text();
    } catch (error) {
      throw new Error(`Failed to read file ${path}: ${error}`);
    }
  }

  /**
   * Write content to a file
   * Equivalent to Python's open(file, 'w').write(content)
   */
  async writeFile(path: string, content: string): Promise<void> {
    try {
      // Ensure parent directory exists
      const parentDir = this.getParentDirectory(path);
      await this.ensureDirectoryExists(parentDir);

      const file = new File(path);
      file.write(content, { encoding: 'utf8' });
    } catch (error) {
      throw new Error(`Failed to write file ${path}: ${error}`);
    }
  }

  /**
   * Delete a file
   * Equivalent to Python's Path.unlink()
   */
  async deleteFile(path: string): Promise<boolean> {
    try {
      const file = new File(path);
      if (file.exists) {
        file.delete();
        return true;
      }
      return false;
    } catch (error) {
      console.error(`Failed to delete file ${path}:`, error);
      return false;
    }
  }

  /**
   * Rename/move a file
   * Equivalent to Python's Path.rename()
   */
  async renameFile(oldPath: string, newPath: string): Promise<boolean> {
    try {
      const file = new File(oldPath);
      if (!file.exists) {
        return false;
      }

      // Ensure parent directory of new path exists
      const newParentDir = this.getParentDirectory(newPath);
      await this.ensureDirectoryExists(newParentDir);

      const destination = new File(newPath);
      file.move(destination);
      return true;
    } catch (error) {
      console.error(`Failed to rename file ${oldPath} to ${newPath}:`, error);
      return false;
    }
  }

  /**
   * Delete a directory and all its contents
   * Equivalent to Python's shutil.rmtree()
   */
  async deleteDirectory(path: string): Promise<boolean> {
    try {
      const dir = new Directory(path);
      if (dir.exists) {
        dir.delete();
        return true;
      }
      return false;
    } catch (error) {
      console.error(`Failed to delete directory ${path}:`, error);
      return false;
    }
  }

  /**
   * List files in a directory, optionally filtering by pattern
   * Equivalent to Python's Path.glob(pattern)
   */
  async listFiles(directory: string, pattern?: string): Promise<string[]> {
    try {
      const dir = new Directory(directory);
      if (!dir.exists) {
        return [];
      }

      const items = dir.list();
      // Filter to only files (not directories)
      const files = items.filter(item => item instanceof File);

      if (!pattern) {
        return files.map((file) => file.uri);
      }

      // Simple glob pattern matching (supports *.md, *.txt, etc.)
      const regexPattern = this.globToRegex(pattern);
      const filteredFiles = files.filter((file) => {
        const fileName = file.uri.split('/').pop() || '';
        return regexPattern.test(fileName);
      });

      return filteredFiles.map((file) => file.uri);
    } catch (error) {
      throw new Error(`Failed to list files in ${directory}: ${error}`);
    }
  }

  /**
   * List directories in a directory
   */
  async listDirectories(directory: string): Promise<string[]> {
    try {
      const dir = new Directory(directory);
      if (!dir.exists) {
        return [];
      }

      const items = dir.list();
      // Filter to only directories (not files)
      const directories = items.filter(item => item instanceof Directory);

      return directories.map(d => d.uri);
    } catch (error) {
      throw new Error(`Failed to list directories in ${directory}: ${error}`);
    }
  }

  /**
   * Check if a file exists
   */
  async fileExists(path: string): Promise<boolean> {
    try {
      const file = new File(path);
      return file.exists;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if a directory exists
   */
  async directoryExists(path: string): Promise<boolean> {
    try {
      const dir = new Directory(path);
      return dir.exists;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get parent directory path from a file path
   * Equivalent to Python's Path.parent
   */
  private getParentDirectory(path: string): string {
    const parts = path.split("/");
    parts.pop(); // Remove filename
    return parts.join("/") + "/";
  }

  /**
   * Convert a glob pattern to a regular expression
   * Supports basic glob patterns: *, ?, [abc]
   */
  private globToRegex(pattern: string): RegExp {
    // Escape special regex characters except glob wildcards
    let regexPattern = pattern
      .replace(/[.+^${}()|[\]\\]/g, "\\$&") // Escape special chars
      .replace(/\*/g, ".*") // * matches any characters
      .replace(/\?/g, "."); // ? matches single character

    return new RegExp(`^${regexPattern}$`);
  }

  /**
   * Get file information (size, modification time, etc.)
   */
  async getFileInfo(path: string): Promise<any> {
    const file = new File(path);
    return file.info();
  }

  /**
   * Get the base directory used by this manager
   */
  getBaseDirectory(): string {
    return this.baseDirectory;
  }
}

// Export a singleton instance for convenience
export const fileSystemManager = new FileSystemManager();
