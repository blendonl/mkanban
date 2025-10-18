/**
 * File Operations helper utilities
 * Ported from Python: src/infrastructure/storage/file_operations.py
 */

import { FileSystemManager } from "./FileSystemManager";
import { MarkdownParser, Metadata } from "./MarkdownParser";
import { ItemId } from "../../core/types";
import { getSafeFilename } from "../../utils/stringUtils";
import { COLUMN_METADATA_FILENAME } from "../../core/constants";

/**
 * Find an item file by its ID in a column directory
 * Supports both old format (title.md) and new format (id-title.md)
 */
export async function findItemFileById(
  fileSystem: FileSystemManager,
  parser: MarkdownParser,
  columnDir: string,
  itemId: ItemId
): Promise<string | null> {
  try {
    const exists = await fileSystem.directoryExists(columnDir);
    if (!exists) {
      return null;
    }

    // List all markdown files in the column
    const mdFiles = await fileSystem.listFiles(columnDir, "*.md");
    const itemIdLower = itemId.toLowerCase();

    for (const itemFile of mdFiles) {
      // Skip column.md
      if (itemFile.endsWith(COLUMN_METADATA_FILENAME)) {
        continue;
      }

      // Check if filename starts with item ID (new format, case-insensitive)
      const filename = getFileStem(itemFile).toLowerCase();
      if (filename.startsWith(`${itemIdLower}-`)) {
        return itemFile;
      }

      // Fallback: Check frontmatter (old format or verification)
      try {
        const parsed = await parser.parseItemMetadata(itemFile);
        const fileId = parsed.metadata.id || getFileStem(itemFile);
        if (fileId === itemId) {
          return itemFile;
        }
      } catch (error) {
        // Skip corrupted files
        continue;
      }
    }

    return null;
  } catch (error) {
    throw new Error(`Failed to search for item ${itemId} in ${columnDir}: ${error}`);
  }
}

/**
 * Get board directory path from board name
 */
export function getBoardDirectoryPath(boardsDir: string, boardName: string): string {
  const safeName = getSafeFilename(boardName);
  return `${boardsDir}${safeName}/`;
}

/**
 * Get column directory path from board directory and column name
 */
export function getColumnDirectoryPath(boardDir: string, columnName: string): string {
  const safeName = getSafeFilename(columnName);
  return `${boardDir}${safeName}/`;
}

/**
 * Clean up orphaned and duplicate files in a column
 * Removes files for items not in currentItemIds and duplicate files for same item
 */
export async function cleanupColumnFiles(
  fileSystem: FileSystemManager,
  parser: MarkdownParser,
  columnDir: string,
  currentItemIds: Set<ItemId>
): Promise<void> {
  try {
    const exists = await fileSystem.directoryExists(columnDir);
    if (!exists) {
      return;
    }

    const mdFiles = await fileSystem.listFiles(columnDir, "*.md");
    const itemIdToFiles: Map<ItemId, string[]> = new Map();

    for (const itemFile of mdFiles) {
      // Skip column.md
      if (itemFile.endsWith(COLUMN_METADATA_FILENAME)) {
        continue;
      }

      try {
        const parsed = await parser.parseItemMetadata(itemFile);
        const fileItemId = parsed.metadata.id || getFileStem(itemFile);

        if (fileItemId) {
          // If item is not in current items, delete it
          if (!currentItemIds.has(fileItemId)) {
            await fileSystem.deleteFile(itemFile);
          } else {
            // Track files for this item ID
            if (!itemIdToFiles.has(fileItemId)) {
              itemIdToFiles.set(fileItemId, []);
            }
            itemIdToFiles.get(fileItemId)!.push(itemFile);
          }
        }
      } catch (error) {
        // Skip corrupted files but don't throw
        console.warn(`Skipping corrupted file ${itemFile}:`, error);
        continue;
      }
    }

    // Handle duplicates: keep newest, delete older files
    for (const [itemId, files] of itemIdToFiles.entries()) {
      if (files.length > 1) {
        // Sort by modification time (newest first)
        const fileInfos = await Promise.all(
          files.map(async (file) => ({
            file,
            info: await fileSystem.getFileInfo(file),
          }))
        );

        fileInfos.sort((a, b) => {
          const aTime = a.info.modificationTime || 0;
          const bTime = b.info.modificationTime || 0;
          return bTime - aTime; // Descending order (newest first)
        });

        // Delete all but the first (newest) file
        for (let i = 1; i < fileInfos.length; i++) {
          await fileSystem.deleteFile(fileInfos[i].file);
        }
      }
    }
  } catch (error) {
    console.error(`Failed to cleanup column files in ${columnDir}:`, error);
  }
}

/**
 * Get unique filename to avoid collisions
 * If file exists with different item ID, append counter or item ID
 */
export async function getUniqueFilename(
  fileSystem: FileSystemManager,
  parser: MarkdownParser,
  basePath: string,
  itemId: ItemId,
  maxRetries: number = 100
): Promise<string> {
  const baseName = getFileStem(basePath);
  const extension = ".md";
  const directory = getParentDirectory(basePath);

  // Check if base path is available
  const baseFullPath = `${directory}${baseName}${extension}`;
  const baseExists = await fileSystem.fileExists(baseFullPath);

  if (!baseExists) {
    return baseName;
  }

  // Check if existing file has the same item ID
  try {
    const parsed = await parser.parseItemMetadata(baseFullPath);
    const existingItemId = parsed.metadata.id || baseName;
    if (existingItemId === itemId) {
      return baseName; // Same item, can use this filename
    }
  } catch (error) {
    // If we can't read the file, treat it as a collision
  }

  // Try with counter suffix
  for (let counter = 1; counter <= maxRetries; counter++) {
    const testName = `${baseName}_${counter}`;
    const testPath = `${directory}${testName}${extension}`;
    const testExists = await fileSystem.fileExists(testPath);

    if (!testExists) {
      return testName;
    }

    // Check if this file has the same item ID
    try {
      const parsed = await parser.parseItemMetadata(testPath);
      const existingItemId = parsed.metadata.id || testName;
      if (existingItemId === itemId) {
        return testName;
      }
    } catch (error) {
      // Continue to next attempt
    }
  }

  // Last resort: use item ID in filename
  return `${baseName}_${itemId.substring(0, 8)}`;
}

/**
 * Get file stem (filename without extension)
 */
function getFileStem(filePath: string): string {
  const parts = filePath.split("/");
  const filename = parts[parts.length - 1];
  return filename.replace(/\.md$/, "");
}

/**
 * Get parent directory from path
 */
function getParentDirectory(filePath: string): string {
  const parts = filePath.split("/");
  parts.pop(); // Remove filename
  return parts.join("/") + "/";
}
