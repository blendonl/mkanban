/**
 * Storage Configuration Manager
 * Manages persistent configuration for boards directory and other storage settings
 */

import { File, Directory, Paths } from 'expo-file-system';
import { FileSystemManager } from '../infrastructure/storage/FileSystemManager';

interface StorageConfigData {
  boardsDirectory?: string;
  version: string;
}

const CONFIG_VERSION = '1.0';
const DEFAULT_BOARDS_SUBDIR = 'boards/';

export class StorageConfig {
  private configDir: string;
  private configFile: string;
  private cachedConfig: StorageConfigData | null = null;
  private fileSystemManager: FileSystemManager;

  constructor(baseDirectory?: string, fileSystemManager?: FileSystemManager) {
    // Store config in a .mkanban directory within the document directory
    const docDir = baseDirectory || Paths.document.uri;
    this.configDir = `${docDir}.mkanban/`;
    this.configFile = `${this.configDir}config.json`;
    this.fileSystemManager = fileSystemManager || new FileSystemManager();
  }

  /**
   * Get the configured boards directory path
   * Returns custom path if set, otherwise returns default
   */
  async getBoardsDirectory(): Promise<string> {
    const config = await this.loadConfig();

    if (config.boardsDirectory) {
      return config.boardsDirectory;
    }

    // Default: {documentDirectory}/boards/
    return `${Paths.document.uri}${DEFAULT_BOARDS_SUBDIR}`;
  }

  /**
   * Set a custom boards directory path
   * @param path The custom directory path (must be absolute)
   */
  async setBoardsDirectory(path: string): Promise<void> {
    // Validate path
    if (!path || typeof path !== 'string' || path.trim().length === 0) {
      throw new Error('Boards directory path cannot be empty');
    }

    // Ensure path ends with /
    const normalizedPath = path.endsWith('/') ? path : `${path}/`;

    // Validate that the path is accessible
    await this.validateDirectoryPath(normalizedPath);

    // Update config
    const config = await this.loadConfig();
    config.boardsDirectory = normalizedPath;
    await this.saveConfig(config);

    console.log('Boards directory updated to:', normalizedPath);
  }

  /**
   * Reset boards directory to default
   */
  async resetToDefault(): Promise<void> {
    const config = await this.loadConfig();
    delete config.boardsDirectory;
    await this.saveConfig(config);
    console.log('Boards directory reset to default');
  }

  /**
   * Check if using a custom boards directory
   */
  async isUsingCustomDirectory(): Promise<boolean> {
    const config = await this.loadConfig();
    return !!config.boardsDirectory;
  }

  /**
   * Get the default boards directory path
   */
  getDefaultBoardsDirectory(): string {
    return `${Paths.document.uri}${DEFAULT_BOARDS_SUBDIR}`;
  }

  /**
   * Validate that a directory path is accessible and writable
   */
  private async validateDirectoryPath(path: string): Promise<void> {
    try {
      const dir = new Directory(path);

      // Try to create the directory if it doesn't exist
      if (!dir.exists) {
        dir.create({ intermediates: true, idempotent: true });
      }

      // Verify directory exists after creation attempt
      if (!dir.exists) {
        throw new Error('Directory does not exist and could not be created');
      }

      // Try to write a test file to verify write permissions
      const testFile = new File(`${path}.test-write-${Date.now()}`);
      try {
        testFile.write('test');
        testFile.delete();
      } catch (error) {
        throw new Error('Directory is not writable');
      }
    } catch (error) {
      throw new Error(`Invalid directory path: ${error}`);
    }
  }

  /**
   * Load configuration from file
   */
  private async loadConfig(): Promise<StorageConfigData> {
    // Return cached config if available
    if (this.cachedConfig !== null) {
      return { ...this.cachedConfig };
    }

    try {
      // Ensure config directory exists
      const configDirObj = new Directory(this.configDir);
      if (!configDirObj.exists) {
        configDirObj.create({ intermediates: true, idempotent: true });
      }

      // Check if config file exists
      const configFileObj = new File(this.configFile);
      if (!configFileObj.exists) {
        // Create default config
        const defaultConfig: StorageConfigData = {
          version: CONFIG_VERSION,
        };
        await this.saveConfig(defaultConfig);
        return defaultConfig;
      }

      // Read and parse config file
      const content = await configFileObj.text();
      const config: StorageConfigData = JSON.parse(content);

      // Cache the config
      this.cachedConfig = config;

      return { ...config };
    } catch (error) {
      console.error('Failed to load storage config:', error);
      // Return default config on error
      return { version: CONFIG_VERSION };
    }
  }

  /**
   * Save configuration to file
   */
  private async saveConfig(config: StorageConfigData): Promise<void> {
    try {
      // Ensure config directory exists
      const configDirObj = new Directory(this.configDir);
      if (!configDirObj.exists) {
        configDirObj.create({ intermediates: true, idempotent: true });
      }

      // Write config file
      const configFileObj = new File(this.configFile);
      const content = JSON.stringify(config, null, 2);
      configFileObj.write(content);

      // Update cache
      this.cachedConfig = { ...config };

      console.log('Storage config saved:', this.configFile);
    } catch (error) {
      console.error('Failed to save storage config:', error);
      throw new Error(`Failed to save configuration: ${error}`);
    }
  }

  /**
   * Clear cached configuration (useful for testing)
   */
  clearCache(): void {
    this.cachedConfig = null;
  }

  /**
   * Get the full configuration object (for debugging/display)
   */
  async getFullConfig(): Promise<StorageConfigData> {
    return await this.loadConfig();
  }

  /**
   * Check if a directory has any boards
   * @param boardsDirectory Path to check for boards
   */
  async hasExistingBoards(boardsDirectory: string): Promise<boolean> {
    return await this.fileSystemManager.hasBoards(boardsDirectory);
  }

  /**
   * Migrate boards from one directory to another
   * @param oldPath Source directory with boards
   * @param newPath Destination directory for boards
   * @param onProgress Optional callback for progress updates
   * @returns Migration result with success status and details
   */
  async migrateBoards(
    oldPath: string,
    newPath: string,
    onProgress?: (current: number, total: number) => void
  ): Promise<{ success: boolean; message: string; copiedFiles?: number; errors?: string[] }> {
    try {
      // Validate paths
      if (!oldPath || !newPath) {
        return {
          success: false,
          message: 'Source and destination paths are required',
        };
      }

      if (oldPath === newPath) {
        return {
          success: false,
          message: 'Source and destination paths cannot be the same',
        };
      }

      // Check if source has boards
      const hasBoards = await this.hasExistingBoards(oldPath);
      if (!hasBoards) {
        return {
          success: true,
          message: 'No boards found in source directory, nothing to migrate',
          copiedFiles: 0,
        };
      }

      // Validate destination is writable
      const isWritable = await this.fileSystemManager.isDirectoryWritable(newPath);
      if (!isWritable) {
        return {
          success: false,
          message: 'Destination directory is not writable',
        };
      }

      // Perform the migration
      console.log(`Starting board migration from ${oldPath} to ${newPath}`);
      const result = await this.fileSystemManager.copyDirectory(
        oldPath,
        newPath,
        onProgress
      );

      if (!result.success) {
        return {
          success: false,
          message: `Migration failed: ${result.errors.length} errors occurred`,
          copiedFiles: result.copiedFiles,
          errors: result.errors,
        };
      }

      console.log(`Migration completed: ${result.copiedFiles} files copied`);
      return {
        success: true,
        message: `Successfully migrated ${result.copiedFiles} files`,
        copiedFiles: result.copiedFiles,
      };
    } catch (error) {
      console.error('Migration error:', error);
      return {
        success: false,
        message: `Migration error: ${error}`,
      };
    }
  }

  /**
   * Get list of boards in a directory
   * @param boardsDirectory Optional directory path, uses current config if not provided
   */
  async listBoards(boardsDirectory?: string): Promise<string[]> {
    const dir = boardsDirectory || await this.getBoardsDirectory();
    return await this.fileSystemManager.listBoards(dir);
  }
}
