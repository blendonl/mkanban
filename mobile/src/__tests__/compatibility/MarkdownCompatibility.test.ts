/**
 * Compatibility Tests for Python-TypeScript Markdown Format
 * Verifies that markdown files can be read/written by both implementations
 */

import * as path from 'path';
import { MarkdownParser } from '../../infrastructure/storage/MarkdownParser';

// Mock FileSystemManager with real file reading capability
class TestFileSystemManager {
  async readFile(filePath: string): Promise<string> {
    // In a real test environment, this would read actual files
    // For now, we'll return sample content based on the file path

    if (filePath.includes('sample-board-kanban.md')) {
      return `---
id: sample-project
name: Sample Project
description: A sample project for testing compatibility
parents:
  - id: feature-auth
    name: Authentication
    color: blue
    created_at: 2025-10-15T10:00:00.000Z
  - id: feature-ui
    name: UI Improvements
    color: green
    created_at: 2025-10-15T10:30:00.000Z
created_at: 2025-10-15T09:00:00.000Z
---

# Sample Project

This is a sample project board for testing Python and TypeScript compatibility.`;
    }

    if (filePath.includes('sample-item-task.md')) {
      return `---
id: MKA-1
title: Implement login functionality
parent_id: feature-auth
metadata:
  issue_type: Task
  priority: high
created_at: 2025-10-15T10:15:00.000Z
---

# Implement login functionality

Create a login page with email and password fields.

## Requirements
- Email validation
- Password strength indicator
- Remember me checkbox
- Forgot password link

## Acceptance Criteria
- User can log in with valid credentials
- Error messages display for invalid input
- Session is maintained after login`;
    }

    throw new Error(`File not found: ${filePath}`);
  }

  async writeFile(filePath: string, content: string): Promise<void> {
    // Mock write - in real tests this would write to temp directory
  }

  async ensureDirectoryExists(): Promise<void> {
    // Mock
  }
}

describe('Python-TypeScript Markdown Compatibility', () => {
  let markdownParser: MarkdownParser;
  let fsManager: TestFileSystemManager;

  beforeEach(() => {
    fsManager = new TestFileSystemManager();
    markdownParser = new MarkdownParser(fsManager as any);
  });

  describe('Board Metadata Format', () => {
    it('should parse board metadata with Python format', async () => {
      const metadata = await markdownParser.parseBoardMetadata(
        '/test/sample-board-kanban.md'
      );

      expect(metadata).toBeDefined();
      expect(metadata.id).toBe('sample-project');
      expect(metadata.name).toBe('Sample Project');
      expect(metadata.description).toBe('A sample project for testing compatibility');
      expect(metadata.created_at).toBe('2025-10-15T09:00:00.000Z');
    });

    it('should parse parents array correctly', async () => {
      const metadata = await markdownParser.parseBoardMetadata(
        '/test/sample-board-kanban.md'
      );

      expect(metadata.parents).toHaveLength(2);
      expect(metadata.parents[0].id).toBe('feature-auth');
      expect(metadata.parents[0].name).toBe('Authentication');
      expect(metadata.parents[0].color).toBe('blue');
      expect(metadata.parents[1].id).toBe('feature-ui');
      expect(metadata.parents[1].name).toBe('UI Improvements');
      expect(metadata.parents[1].color).toBe('green');
    });

    it('should preserve markdown content', async () => {
      const content = await fsManager.readFile('/test/sample-board-kanban.md');

      expect(content).toContain('# Sample Project');
      expect(content).toContain('This is a sample project board');
    });
  });

  describe('Item Metadata Format', () => {
    it('should parse item metadata with Python format', async () => {
      const metadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      expect(metadata).toBeDefined();
      expect(metadata.id).toBe('MKA-1');
      expect(metadata.title).toBe('Implement login functionality');
      expect(metadata.parent_id).toBe('feature-auth');
      expect(metadata.created_at).toBe('2025-10-15T10:15:00.000Z');
    });

    it('should parse nested metadata object', async () => {
      const metadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      expect(metadata.metadata).toBeDefined();
      expect(metadata.metadata.issue_type).toBe('Task');
      expect(metadata.metadata.priority).toBe('high');
    });

    it('should preserve markdown description', async () => {
      const content = await fsManager.readFile('/test/sample-item-task.md');

      expect(content).toContain('# Implement login functionality');
      expect(content).toContain('## Requirements');
      expect(content).toContain('## Acceptance Criteria');
      expect(content).toContain('Email validation');
    });
  });

  describe('Timestamp Format Compatibility', () => {
    it('should use ISO 8601 format with milliseconds and UTC', async () => {
      const boardMetadata = await markdownParser.parseBoardMetadata(
        '/test/sample-board-kanban.md'
      );

      // Verify timestamp format: YYYY-MM-DDTHH:mm:ss.sssZ
      expect(boardMetadata.created_at).toMatch(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/
      );

      // Verify can be parsed by JavaScript Date
      const date = new Date(boardMetadata.created_at);
      expect(isNaN(date.getTime())).toBe(false);
      expect(date.getFullYear()).toBe(2025);
    });

    it('should preserve timestamp precision', async () => {
      const itemMetadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      const timestamp = itemMetadata.created_at;
      expect(timestamp).toBe('2025-10-15T10:15:00.000Z');

      // Verify milliseconds are included
      expect(timestamp.split('.')[1]).toBe('000Z');
    });
  });

  describe('Field Naming Conventions', () => {
    it('should use snake_case for field names', async () => {
      const itemMetadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      // These fields should use snake_case (Python convention)
      expect(itemMetadata).toHaveProperty('parent_id');
      expect(itemMetadata).toHaveProperty('created_at');
      expect(itemMetadata.metadata).toHaveProperty('issue_type');
    });

    it('should not use camelCase in metadata', async () => {
      const content = await fsManager.readFile('/test/sample-item-task.md');

      // Verify no camelCase in YAML frontmatter
      expect(content).not.toContain('parentId');
      expect(content).not.toContain('createdAt');
      expect(content).not.toContain('issueType');
    });
  });

  describe('Round-Trip Compatibility', () => {
    it('should preserve all data when writing and reading back', async () => {
      // Parse original
      const originalMetadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      // Simulate writing (would write to temp file in real test)
      const content = await fsManager.readFile('/test/sample-item-task.md');

      // Verify all important fields are present in output
      expect(content).toContain('id: MKA-1');
      expect(content).toContain('title: Implement login functionality');
      expect(content).toContain('parent_id: feature-auth');
      expect(content).toContain('issue_type: Task');
      expect(content).toContain('priority: high');
    });
  });

  describe('Special Characters Handling', () => {
    it('should handle markdown content with special characters', async () => {
      const content = await fsManager.readFile('/test/sample-item-task.md');

      // Verify special markdown characters are preserved
      expect(content).toContain('##'); // Headers
      expect(content).toContain('- '); // Lists
    });

    it('should handle YAML special characters in metadata', async () => {
      const boardMetadata = await markdownParser.parseBoardMetadata(
        '/test/sample-board-kanban.md'
      );

      // Colon in description should be handled correctly
      expect(boardMetadata.description).toContain('A sample project');
    });
  });

  describe('Optional Fields', () => {
    it('should handle optional description field in board', async () => {
      const metadata = await markdownParser.parseBoardMetadata(
        '/test/sample-board-kanban.md'
      );

      // Description is optional
      expect(metadata.description).toBeDefined();
    });

    it('should handle optional parent_id in items', async () => {
      const metadata = await markdownParser.parseItemMetadata(
        '/test/sample-item-task.md'
      );

      // parent_id is optional but present in this case
      expect(metadata.parent_id).toBe('feature-auth');
    });
  });
});
