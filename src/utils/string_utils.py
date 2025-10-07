import re


def generate_id_from_name(name: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    safe_name = re.sub(r"\s+", "_", safe_name.strip())
    return safe_name or "unnamed"


def get_safe_filename(name: str) -> str:
    # Replace forward slashes and other path separators with dashes first
    safe_name = name.replace("/", "-").replace("\\", "-")
    # Remove all characters except alphanumeric, spaces, and dashes
    safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", safe_name.lower())
    # Replace multiple spaces with single dashes
    safe_name = re.sub(r"\s+", "-", safe_name.strip())
    # Replace multiple consecutive dashes with single dash
    safe_name = re.sub(r"-+", "-", safe_name)
    # Remove leading/trailing dashes
    safe_name = safe_name.strip("-")
    return safe_name or "unnamed"


def get_title_filename(title: str) -> str:
    safe_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    safe_title = re.sub(r"\s+", "_", safe_title.strip())
    return safe_title or "unnamed"


def extract_title_from_content(content: str, fallback: str = "") -> str:
    content_lines = content.strip().split("\n")
    for line in content_lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def update_title_in_content(content: str, new_title: str) -> str:
    lines = content.split("\n")
    updated_lines = []
    title_updated = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not title_updated:
            updated_lines.append(f"# {new_title}")
            title_updated = True
        else:
            updated_lines.append(line)

    if not title_updated and content:
        return f"# {new_title}\n\n{content}"
    elif not title_updated:
        return f"# {new_title}"

    return "\n".join(updated_lines)


def ensure_title_header(content: str, title: str) -> str:
    if not content:
        return f"# {title}"

    lines = content.split("\n")
    has_title_header = any(line.strip().startswith("# ") for line in lines)

    if has_title_header:
        return update_title_in_content(content, title)
    else:
        return f"# {title}\n\n{content}"


def get_board_prefix(board_name: str) -> str:
    """Generate a 3-character prefix from board name.

    Args:
        board_name: The name of the board

    Returns:
        A 3-character uppercase prefix

    Examples:
        "mkanban" -> "MKA"
        "my-project" -> "MPR" (first letter of first word + first 2 of second)
        "RecipeApp" -> "RAP" (camelCase treated as 2 words)
        "git-branches" -> "GBR"
    """
    # Remove special characters
    clean_name = re.sub(r"[^a-zA-Z0-9\s-]", "", board_name)

    # Split by spaces, hyphens, underscores
    words = re.split(r'[\s\-_]+', clean_name)
    # Filter out empty strings
    words = [w for w in words if w]

    if not words:
        return "XXX"

    # If single word, check for camelCase
    if len(words) == 1:
        # Handle camelCase by splitting on capital letters
        camel_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', words[0])
        if len(camel_parts) > 1:
            # Multiple parts from camelCase, treat as multiple words
            words = camel_parts

    # Generate prefix based on number of words/parts
    if len(words) >= 3:
        # 3 or more words: take first letter of each
        prefix = "".join(word[0] for word in words[:3]).upper()
    elif len(words) == 2:
        # 2 words: take first letter of first word + first 2 letters of second word
        prefix = (words[0][0] + words[1][:2]).upper()
    elif len(words) == 1:
        # Single word: take first 3 chars
        prefix = words[0][:3].upper()
    else:
        # Fallback (shouldn't happen)
        prefix = "XXX"

    # Ensure exactly 3 characters
    if len(prefix) < 3:
        # Pad with more characters from the last word if possible
        if words and len(words[-1]) > len(prefix):
            chars_needed = 3 - len(prefix)
            remaining_chars = words[-1][1:1+chars_needed]
            prefix = (prefix + remaining_chars).upper()
        # Still not enough? Pad with X
        if len(prefix) < 3:
            prefix = prefix.ljust(3, 'X')
    elif len(prefix) > 3:
        prefix = prefix[:3]

    return prefix


def generate_manual_item_id(board_name: str, index: int) -> str:
    """Generate an ID for a manually created item.

    Args:
        board_name: The name of the board
        index: The sequential index for this item

    Returns:
        An ID in format "{BOARD_PREFIX}-{INDEX}"

    Examples:
        "mkanban", 1 -> "MKA-1"
        "my-project", 42 -> "MYP-42"
    """
    prefix = get_board_prefix(board_name)
    return f"{prefix}-{index}"
