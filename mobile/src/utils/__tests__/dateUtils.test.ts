/**
 * Unit Tests for Date Utilities
 */

import { now, formatTimestamp, parseTimestamp } from '../dateUtils';

describe('dateUtils', () => {
  describe('now', () => {
    it('should return ISO 8601 formatted timestamp', () => {
      const timestamp = now();

      // Should match ISO 8601 format: YYYY-MM-DDTHH:mm:ss.sssZ
      expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    });

    it('should return current time', () => {
      const before = Date.now();
      const timestamp = now();
      const after = Date.now();

      const timestampMs = new Date(timestamp).getTime();
      expect(timestampMs).toBeGreaterThanOrEqual(before);
      expect(timestampMs).toBeLessThanOrEqual(after);
    });

    it('should return UTC time', () => {
      const timestamp = now();
      expect(timestamp.endsWith('Z')).toBe(true);
    });

    it('should return parseable timestamp', () => {
      const timestamp = now();
      const parsed = new Date(timestamp);
      expect(isNaN(parsed.getTime())).toBe(false);
    });
  });

  describe('formatTimestamp', () => {
    it('should format valid timestamp to readable string', () => {
      const timestamp = '2025-10-15T12:30:45.000Z';
      const formatted = formatTimestamp(timestamp);

      // Should contain date and time components
      expect(formatted).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/); // Date part
      expect(formatted).toContain(':'); // Time part
    });

    it('should handle timestamps without milliseconds', () => {
      const timestamp = '2025-10-15T12:30:45Z';
      const formatted = formatTimestamp(timestamp);

      expect(formatted).toBeTruthy();
      expect(typeof formatted).toBe('string');
    });

    it('should return "Invalid Date" for invalid timestamp', () => {
      const formatted = formatTimestamp('invalid-date');
      expect(formatted).toBe('Invalid Date');
    });

    it('should return "Invalid Date" for empty string', () => {
      const formatted = formatTimestamp('');
      expect(formatted).toBe('Invalid Date');
    });

    it('should format Unix epoch correctly', () => {
      const timestamp = '1970-01-01T00:00:00.000Z';
      const formatted = formatTimestamp(timestamp);

      expect(formatted).toBeTruthy();
      expect(formatted).not.toBe('Invalid Date');
    });

    it('should handle different timezones', () => {
      const timestamp1 = '2025-10-15T12:00:00Z';
      const timestamp2 = '2025-10-15T12:00:00+05:00';

      const formatted1 = formatTimestamp(timestamp1);
      const formatted2 = formatTimestamp(timestamp2);

      expect(formatted1).toBeTruthy();
      expect(formatted2).toBeTruthy();
      expect(formatted1).not.toBe(formatted2); // Should be different due to timezone
    });
  });

  describe('parseTimestamp', () => {
    it('should parse valid ISO 8601 timestamp', () => {
      const timestamp = '2025-10-15T12:30:45.000Z';
      const parsed = parseTimestamp(timestamp);

      expect(parsed).toBeInstanceOf(Date);
      expect(parsed.getFullYear()).toBe(2025);
      expect(parsed.getMonth()).toBe(9); // October is month 9 (0-indexed)
      expect(parsed.getDate()).toBe(15);
    });

    it('should parse timestamp without milliseconds', () => {
      const timestamp = '2025-10-15T12:30:45Z';
      const parsed = parseTimestamp(timestamp);

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(false);
    });

    it('should parse timestamp with timezone offset', () => {
      const timestamp = '2025-10-15T12:30:45+05:00';
      const parsed = parseTimestamp(timestamp);

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(false);
    });

    it('should return Invalid Date for invalid timestamp', () => {
      const parsed = parseTimestamp('invalid-date');

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(true);
    });

    it('should return Invalid Date for empty string', () => {
      const parsed = parseTimestamp('');

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(true);
    });

    it('should handle Unix timestamp in milliseconds', () => {
      const timestamp = '1697376645000'; // Unix timestamp
      const parsed = parseTimestamp(timestamp);

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(false);
    });

    it('should parse current timestamp correctly', () => {
      const timestamp = now();
      const parsed = parseTimestamp(timestamp);

      expect(parsed).toBeInstanceOf(Date);
      expect(isNaN(parsed.getTime())).toBe(false);

      // Should be within last second
      const diff = Date.now() - parsed.getTime();
      expect(diff).toBeLessThan(1000);
    });
  });

  describe('round-trip conversion', () => {
    it('should preserve timestamp through format and parse', () => {
      const original = now();
      const parsed = parseTimestamp(original);
      const formatted = parsed.toISOString();

      expect(formatted).toBe(original);
    });

    it('should handle multiple conversions', () => {
      const timestamp1 = now();
      const parsed1 = parseTimestamp(timestamp1);
      const timestamp2 = parsed1.toISOString();
      const parsed2 = parseTimestamp(timestamp2);

      expect(parsed1.getTime()).toBe(parsed2.getTime());
    });
  });
});
