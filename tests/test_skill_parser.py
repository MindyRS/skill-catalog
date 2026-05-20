import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crawler'))

from skill_parser import parse_frontmatter, detect_platforms, is_skill_candidate, build_skill


def test_parse_frontmatter_valid():
    content = "---\nname: test-skill\ndescription: Does things\n---\n\n# Body"
    assert parse_frontmatter(content) == {"name": "test-skill", "description": "Does things"}


def test_parse_frontmatter_no_frontmatter():
    assert parse_frontmatter("# Just a heading\nNo frontmatter") == {}


def test_parse_frontmatter_missing_closing_delimiter():
    assert parse_frontmatter("---\nname: broken\n") == {}


def test_parse_frontmatter_invalid_yaml():
    assert parse_frontmatter("---\nname: [unclosed\n---\n") == {}


def test_parse_frontmatter_empty_body():
    assert parse_frontmatter("---\n---\n") == {}


def test_detect_platforms_from_frontmatter_key():
    fm = {"name": "x", "claude": "yes"}
    assert "claude" in detect_platforms(fm, "")


def test_detect_platforms_from_description():
    fm = {"name": "x", "description": "Use this with Gemini CLI"}
    assert "gemini" in detect_platforms(fm, "Use this with Gemini CLI")


def test_detect_platforms_none():
    fm = {"name": "x", "description": "Generic skill"}
    assert detect_platforms(fm, "Generic skill") == []


def test_detect_platforms_multiple():
    fm = {"name": "x", "description": "Works with claude and copilot"}
    platforms = detect_platforms(fm, "Works with claude and copilot")
    assert "claude" in platforms
    assert "copilot" in platforms


def test_is_skill_candidate_skill_md():
    assert is_skill_candidate("src/deep/path/SKILL.md") is True


def test_is_skill_candidate_md_in_skills_dir():
    assert is_skill_candidate("x-pack/solutions/security/skills/debugging.md") is True


def test_is_skill_candidate_nested_skills_dir():
    assert is_skill_candidate("plugins/skills/brainstorming/SKILL.md") is True


def test_is_skill_candidate_readme():
    assert is_skill_candidate("README.md") is False


def test_is_skill_candidate_skills_in_filename_not_dir():
    # "skills.md" at root — not inside a skills/ dir
    assert is_skill_candidate("skills.md") is False


def test_is_skill_candidate_doc_in_non_skills_dir():
    assert is_skill_candidate("docs/debugging.md") is False


def test_build_skill_structure():
    fm = {"name": "debugging", "description": "For bugs", "tags": ["debug"]}
    commit_info = {"date": "2026-05-17", "author": "moose"}
    skill = build_skill("elastic", "kibana", "skills/SKILL.md", "main", fm, "", commit_info)
    assert skill["name"] == "debugging"
    assert skill["description"] == "For bugs"
    assert skill["repo"] == "elastic/kibana"
    assert skill["url"] == "https://github.com/elastic/kibana/blob/main/skills/SKILL.md"
    assert skill["last_updated"] == "2026-05-17"
    assert skill["author"] == "moose"
    assert skill["tags"] == ["debug"]


def test_build_skill_non_main_branch():
    fm = {"name": "x"}
    skill = build_skill("org", "repo", "SKILL.md", "master", fm, "", {})
    assert "/blob/master/" in skill["url"]


def test_build_skill_missing_description():
    fm = {"name": "x"}
    skill = build_skill("org", "repo", "SKILL.md", "main", fm, "", {})
    assert skill["description"] == ""
