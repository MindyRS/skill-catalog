import yaml


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown. Returns {} if absent or invalid."""
    if not content.startswith('---'):
        return {}
    end = content.find('\n---', 3)
    if end == -1:
        return {}
    try:
        result = yaml.safe_load(content[3:end])
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}


def detect_platforms(frontmatter: dict, content: str) -> list:
    """Detect which AI platforms a skill supports from frontmatter keys and content."""
    platforms = []
    fm_keys = {k.lower() for k in frontmatter}
    content_lower = content.lower()
    for platform in ("claude", "gemini", "copilot"):
        if platform in fm_keys or platform in content_lower:
            platforms.append(platform)
    return platforms


def is_skill_candidate(path: str) -> bool:
    """Return True if the file path matches skill detection rules:
    - Named SKILL.md anywhere, OR
    - Any .md inside a skills/ directory (at any depth)
    """
    parts = path.split("/")
    filename = parts[-1]
    if filename == "SKILL.md":
        return True
    if filename.endswith(".md") and "skills" in parts[:-1]:
        return True
    return False


def build_skill(owner: str, repo: str, path: str, default_branch: str,
                frontmatter: dict, content: str, commit_info: dict) -> dict:
    """Assemble a skill record from its parsed parts."""
    return {
        "name": frontmatter["name"],
        "description": frontmatter.get("description", ""),
        "repo": f"{owner}/{repo}",
        "path": path,
        "url": f"https://github.com/{owner}/{repo}/blob/{default_branch}/{path}",
        "last_updated": commit_info.get("date"),
        "author": commit_info.get("author"),
        "platforms": detect_platforms(frontmatter, content),
        "tags": frontmatter.get("tags", []),
    }
