/**
 * Observer interface for FileSystemManager changes
 *
 * Components that need to respond to file system configuration changes
 * (such as boards directory changes) should implement this interface
 * and register themselves with FileSystemManager.
 */
export interface FileSystemObserver {
  /**
   * Called when the boards directory path changes
   * @param newPath The new boards directory path
   */
  onBoardsDirectoryChanged(newPath: string): void;
}
