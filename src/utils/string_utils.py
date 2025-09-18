import re


def generate_id_from_name(name: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    safe_name = re.sub(r"\s+", "_", safe_name.strip())
    return safe_name or "unnamed"


def get_safe_filename(name: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    safe_name = re.sub(r"\s+", "-", safe_name.strip())
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
