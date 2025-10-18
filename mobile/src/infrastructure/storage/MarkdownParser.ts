/**
 * Markdown Parser for MKanban mobile app
 * Handles parsing and saving markdown files with YAML frontmatter
 * Ported from Python: src/infrastructure/storage/markdown_parser.py
 */

import matter from "gray-matter";
import * as yaml from "js-yaml";
import { FileSystemManager } from "./FileSystemManager";
import { extractTitleFromContent, ensureTitleHeader } from "../../utils/stringUtils";

export type Metadata = Record<string, any>;

export interface ParsedItem {
  title: string;
  content: string;
  metadata: Metadata;
}

export interface ParsedBoard {
  name: string;
  metadata: Metadata;
}

export class MarkdownParser {
  constructor(private fileSystem: FileSystemManager) {}

  /**
   * Parse board metadata from kanban.md file
   * Returns board name and metadata
   */
  async parseBoardMetadata(filePath: string): Promise<ParsedBoard> {
    try {
      const fileContent = await this.fileSystem.readFile(filePath);
      const parsed = matter(fileContent);

      // Extract board name from metadata, fallback to directory name
      const boardName = parsed.data.name || this.getBoardNameFromPath(filePath);

      return {
        name: boardName,
        metadata: parsed.data,
      };
    } catch (error) {
      throw new Error(`Failed to parse board metadata from ${filePath}: ${error}`);
    }
  }

  /**
   * Parse item metadata from item .md file
   * Returns title, content, and metadata
   */
  async parseItemMetadata(filePath: string): Promise<ParsedItem> {
    try {
      const fileContent = await this.fileSystem.readFile(filePath);
      const parsed = matter(fileContent);

      // Get title from metadata or extract from content
      const metadataTitle = parsed.data.title;
      const contentTitle = extractTitleFromContent(parsed.content, metadataTitle);

      return {
        title: contentTitle || metadataTitle || this.getFileStem(filePath),
        content: parsed.content,
        metadata: parsed.data,
      };
    } catch (error) {
      throw new Error(`Failed to parse item metadata from ${filePath}: ${error}`);
    }
  }

  /**
   * Parse column metadata from column.md file
   * Returns metadata or null if file doesn't exist
   */
  async parseColumnMetadata(filePath: string): Promise<Metadata | null> {
    try {
      const exists = await this.fileSystem.fileExists(filePath);
      if (!exists) {
        return null;
      }

      const fileContent = await this.fileSystem.readFile(filePath);
      const parsed = matter(fileContent);
      return parsed.data;
    } catch (error) {
      console.warn(`Failed to parse column metadata from ${filePath}:`, error);
      return null;
    }
  }

  /**
   * Save board metadata to kanban.md file
   */
  async saveBoardMetadata(
    filePath: string,
    boardName: string,
    metadata: Metadata
  ): Promise<void> {
    try {
      // Create content with title header
      const content = `# ${boardName}\n`;

      // Organize metadata with proper ordering
      const organizedMetadata = this.organizeMetadata(metadata);

      // Create frontmatter document
      const yamlStr = yaml.dump(organizedMetadata, {
        sortKeys: false,
        lineWidth: -1, // Disable line wrapping
      });

      // Build full content: frontmatter + content
      const fullContent = `---\n${yamlStr}---\n\n${content}`;

      await this.fileSystem.writeFile(filePath, fullContent);
    } catch (error) {
      throw new Error(`Failed to save board metadata to ${filePath}: ${error}`);
    }
  }

  /**
   * Save item with metadata to .md file
   */
  async saveItemWithMetadata(
    filePath: string,
    title: string,
    content: string,
    metadata: Metadata
  ): Promise<void> {
    try {
      // Ensure content has title header
      const updatedContent = ensureTitleHeader(content, title);

      // Organize metadata with proper ordering
      const organizedMetadata = this.organizeMetadata(metadata);

      // Create frontmatter document
      const yamlStr = yaml.dump(organizedMetadata, {
        sortKeys: false,
        lineWidth: -1,
      });

      // Build full content
      const fullContent = `---\n${yamlStr}---\n\n${updatedContent}`;

      await this.fileSystem.writeFile(filePath, fullContent);
    } catch (error) {
      throw new Error(`Failed to save item to ${filePath}: ${error}`);
    }
  }

  /**
   * Save column metadata to column.md file
   */
  async saveColumnMetadata(
    filePath: string,
    columnName: string,
    metadata: Metadata
  ): Promise<void> {
    try {
      const content = `# ${columnName}\n\nColumn metadata and configuration.`;

      // Organize metadata
      const organizedMetadata = this.organizeMetadata(metadata);

      // Create frontmatter document
      const yamlStr = yaml.dump(organizedMetadata, {
        sortKeys: false,
        lineWidth: -1,
      });

      const fullContent = `---\n${yamlStr}---\n\n${content}`;

      await this.fileSystem.writeFile(filePath, fullContent);
    } catch (error) {
      throw new Error(`Failed to save column metadata to ${filePath}: ${error}`);
    }
  }

  /**
   * Organize metadata with a logical order
   * Priority fields first, then alphabetically, timestamps at bottom
   */
  private organizeMetadata(metadata: Metadata): Metadata {
    const ordered: Metadata = {};

    // Priority fields (in order)
    const priorityFields = ["id", "title", "parent_id"];

    // Timestamp fields (should be at bottom)
    const timestampFields = [
      "moved_in_progress_at",
      "moved_in_done_at",
      "worked_on_for",
      "created_at",
    ];

    // Add priority fields first
    for (const field of priorityFields) {
      if (field in metadata) {
        ordered[field] = metadata[field];
      }
    }

    // Add other fields alphabetically (excluding timestamps and priority)
    const otherFields = Object.keys(metadata)
      .filter((key) => !priorityFields.includes(key) && !timestampFields.includes(key))
      .sort();

    for (const field of otherFields) {
      ordered[field] = metadata[field];
    }

    // Add timestamp fields at the end (except created_at)
    for (const field of timestampFields.slice(0, -1)) {
      if (field in metadata) {
        ordered[field] = metadata[field];
      }
    }

    // Add created_at last
    if ("created_at" in metadata) {
      ordered["created_at"] = metadata["created_at"];
    }

    return ordered;
  }

  /**
   * Extract board name from file path
   * Gets the parent directory name
   */
  private getBoardNameFromPath(filePath: string): string {
    const parts = filePath.split("/").filter((p) => p.length > 0);
    // Get second to last part (parent directory)
    return parts.length >= 2 ? parts[parts.length - 2] : "unnamed";
  }

  /**
   * Get file stem (filename without extension)
   */
  private getFileStem(filePath: string): string {
    const parts = filePath.split("/");
    const filename = parts[parts.length - 1];
    return filename.replace(/\.md$/, "");
  }
}
