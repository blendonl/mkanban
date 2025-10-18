/**
 * Unit Tests for String Utilities
 */

import {
  generateIdFromName,
  getSafeFilename,
  getBoardPrefix,
  generateManualItemId,
  getTitleFilename,
} from '../stringUtils';

describe('stringUtils', () => {
  describe('generateIdFromName', () => {
    it('should convert name to lowercase', () => {
      expect(generateIdFromName('MyBoard')).toBe('myboard');
    });

    it('should replace spaces with hyphens', () => {
      expect(generateIdFromName('My Test Board')).toBe('my-test-board');
    });

    it('should remove special characters', () => {
      expect(generateIdFromName('Test@Board#123!')).toBe('testboard123');
    });

    it('should handle multiple spaces', () => {
      expect(generateIdFromName('Test   Board')).toBe('test-board');
    });

    it('should handle leading and trailing spaces', () => {
      expect(generateIdFromName('  Test Board  ')).toBe('test-board');
    });

    it('should handle empty string', () => {
      expect(generateIdFromName('')).toBe('');
    });

    it('should handle unicode characters', () => {
      expect(generateIdFromName('Test Board 日本語')).toBe('test-board-');
    });
  });

  describe('getSafeFilename', () => {
    it('should replace spaces with hyphens', () => {
      expect(getSafeFilename('My File')).toBe('my-file');
    });

    it('should convert to lowercase', () => {
      expect(getSafeFilename('MyFile')).toBe('myfile');
    });

    it('should remove special characters', () => {
      expect(getSafeFilename('test@file#123!')).toBe('testfile123');
    });

    it('should handle forward slashes', () => {
      expect(getSafeFilename('path/to/file')).toBe('pathtofile');
    });

    it('should handle empty string', () => {
      expect(getSafeFilename('')).toBe('');
    });

    it('should preserve hyphens and underscores', () => {
      expect(getSafeFilename('test-file_name')).toBe('test-file_name');
    });
  });

  describe('getBoardPrefix', () => {
    it('should generate three-letter prefix for short names', () => {
      expect(getBoardPrefix('abc')).toBe('ABC');
    });

    it('should generate three-letter prefix from longer names', () => {
      expect(getBoardPrefix('MyBoard')).toBe('MYB');
    });

    it('should handle names with spaces', () => {
      expect(getBoardPrefix('My Test Board')).toBe('MTB');
    });

    it('should handle single word', () => {
      expect(getBoardPrefix('Test')).toBe('TES');
    });

    it('should handle very short names', () => {
      expect(getBoardPrefix('A')).toBe('A');
      expect(getBoardPrefix('AB')).toBe('AB');
    });

    it('should handle empty string', () => {
      expect(getBoardPrefix('')).toBe('');
    });

    it('should use first letters of multiple words', () => {
      expect(getBoardPrefix('Project Management Board')).toBe('PMB');
    });

    it('should handle names with special characters', () => {
      expect(getBoardPrefix('Test-Board-123')).toBe('TES');
    });
  });

  describe('generateManualItemId', () => {
    it('should generate ID with board prefix and index', () => {
      expect(generateManualItemId('MYB', 1)).toBe('MYB-1');
    });

    it('should handle zero index', () => {
      expect(generateManualItemId('TEST', 0)).toBe('TEST-0');
    });

    it('should handle large indices', () => {
      expect(generateManualItemId('PRJ', 999)).toBe('PRJ-999');
    });

    it('should convert prefix to uppercase', () => {
      expect(generateManualItemId('abc', 1)).toBe('ABC-1');
    });

    it('should handle empty prefix', () => {
      expect(generateManualItemId('', 1)).toBe('-1');
    });

    it('should handle negative index', () => {
      expect(generateManualItemId('TEST', -1)).toBe('TEST--1');
    });
  });

  describe('getTitleFilename', () => {
    it('should generate filename from title', () => {
      expect(getTitleFilename('Test Item')).toBe('test-item');
    });

    it('should handle special characters', () => {
      expect(getTitleFilename('Fix bug #123')).toBe('fix-bug-123');
    });

    it('should truncate long titles', () => {
      const longTitle = 'This is a very long title that should be truncated to 50 characters';
      const result = getTitleFilename(longTitle);
      expect(result.length).toBeLessThanOrEqual(50);
    });

    it('should handle empty title', () => {
      expect(getTitleFilename('')).toBe('');
    });

    it('should handle unicode characters', () => {
      expect(getTitleFilename('Test 日本語')).toBe('test-');
    });

    it('should remove multiple consecutive hyphens', () => {
      expect(getTitleFilename('Test   Item')).toBe('test-item');
    });

    it('should remove leading and trailing hyphens', () => {
      expect(getTitleFilename('  Test Item  ')).toBe('test-item');
    });
  });
});
