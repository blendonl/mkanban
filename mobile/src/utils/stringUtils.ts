/**
 * String utility functions for MKanban mobile app
 * Ported from Python: src/utils/string_utils.py
 */

/**
 * Generate an ID from a name by making it filesystem-safe
 * Converts to lowercase, replaces spaces with underscores
 */
export function generateIdFromName(name: string): string {
  // Remove all non-alphanumeric except spaces and dashes
  let safeName = name.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, "");
  // Replace spaces with underscores
  safeName = safeName.trim().replace(/\s+/g, "_");
  return safeName || "unnamed";
}

/**
 * Generate a safe filename from a name
 * Converts to lowercase, replaces spaces with dashes, removes special chars
 */
export function getSafeFilename(name: string): string {
  // Replace path separators with dashes
  let safeName = name.replace(/\//g, "-").replace(/\\/g, "-");
  // Remove all non-alphanumeric except spaces and dashes
  safeName = safeName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, "");
  // Replace multiple spaces with single dash
  safeName = safeName.trim().replace(/\s+/g, "-");
  // Replace multiple consecutive dashes with single dash
  safeName = safeName.replace(/-+/g, "-");
  // Remove leading/trailing dashes
  safeName = safeName.replace(/^-+|-+$/g, "");
  return safeName || "unnamed";
}

/**
 * Extract title from markdown content (looks for # Header)
 */
export function extractTitleFromContent(content: string, fallback: string = ""): string {
  const lines = content.trim().split("\n");
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("# ")) {
      return stripped.substring(2).trim();
    }
  }
  return fallback;
}

/**
 * Update the title (# Header) in markdown content
 */
export function updateTitleInContent(content: string, newTitle: string): string {
  const lines = content.split("\n");
  const updatedLines: string[] = [];
  let titleUpdated = false;

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("# ") && !titleUpdated) {
      updatedLines.push(`# ${newTitle}`);
      titleUpdated = true;
    } else {
      updatedLines.push(line);
    }
  }

  if (!titleUpdated && content) {
    return `# ${newTitle}\n\n${content}`;
  } else if (!titleUpdated) {
    return `# ${newTitle}`;
  }

  return updatedLines.join("\n");
}

/**
 * Ensure markdown content has a title header
 */
export function ensureTitleHeader(content: string, title: string): string {
  if (!content) {
    return `# ${title}`;
  }

  const lines = content.split("\n");
  const hasTitleHeader = lines.some((line) => line.trim().startsWith("# "));

  if (hasTitleHeader) {
    return updateTitleInContent(content, title);
  } else {
    return `# ${title}\n\n${content}`;
  }
}

/**
 * Generate a 3-character prefix from board name
 *
 * Examples:
 *   "mkanban" -> "MKA"
 *   "my-project" -> "MPR" (first letter of first word + first 2 of second)
 *   "RecipeApp" -> "RAP" (camelCase treated as 2 words)
 *   "git-branches" -> "GBR"
 */
export function getBoardPrefix(boardName: string): string {
  // Remove special characters
  const cleanName = boardName.replace(/[^a-zA-Z0-9\s-]/g, "");

  // Split by spaces, hyphens, underscores
  let words = cleanName.split(/[\s\-_]+/).filter((w) => w.length > 0);

  if (words.length === 0) {
    return "XXX";
  }

  // If single word, check for camelCase
  if (words.length === 1) {
    const camelParts = words[0].match(/[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)/g);
    if (camelParts && camelParts.length > 1) {
      words = camelParts;
    }
  }

  let prefix: string;

  // Generate prefix based on number of words/parts
  if (words.length >= 3) {
    // 3 or more words: take first letter of each
    prefix = words
      .slice(0, 3)
      .map((w) => w[0])
      .join("")
      .toUpperCase();
  } else if (words.length === 2) {
    // 2 words: first letter of first word + first 2 letters of second word
    prefix = (words[0][0] + words[1].substring(0, 2)).toUpperCase();
  } else {
    // Single word: take first 3 chars
    prefix = words[0].substring(0, 3).toUpperCase();
  }

  // Ensure exactly 3 characters
  if (prefix.length < 3) {
    // Pad with more characters from the last word if possible
    if (words.length > 0 && words[words.length - 1].length > prefix.length) {
      const charsNeeded = 3 - prefix.length;
      const remainingChars = words[words.length - 1].substring(1, 1 + charsNeeded);
      prefix = (prefix + remainingChars).toUpperCase();
    }
    // Still not enough? Pad with X
    if (prefix.length < 3) {
      prefix = prefix.padEnd(3, "X");
    }
  } else if (prefix.length > 3) {
    prefix = prefix.substring(0, 3);
  }

  return prefix;
}

/**
 * Generate an ID for a manually created item
 *
 * Examples:
 *   ("mkanban", 1) -> "MKA-1"
 *   ("my-project", 42) -> "MPR-42"
 */
export function generateManualItemId(boardName: string, index: number): string {
  const prefix = getBoardPrefix(boardName);
  return `${prefix}-${index}`;
}

/**
 * Generate a safe filename from a title for use in item filenames
 * Converts to lowercase, replaces spaces with underscores, removes special chars
 * Used for the title portion of item filenames: {id}-{title}.md
 */
export function getTitleFilename(title: string): string {
  // Remove all non-alphanumeric except spaces and dashes
  let safeTitle = title.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, "");
  // Replace spaces with underscores
  safeTitle = safeTitle.trim().replace(/\s+/g, "_");
  return safeTitle || "unnamed";
}
