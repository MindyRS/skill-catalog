import re

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


def classify_skill(path: str, description: str) -> str:
    """Classify a skill as 'dev_tool', 'feature', or 'unclear'.

    Rules derived from analysis of elastic/kibana skills:
    - dev_tool: helps a developer/tester work on the Kibana codebase
    - feature: part of Kibana's product functionality or an app-building guide
    - unclear: can't determine with confidence
    """
    path_lower = path.lower()
    desc_lower = (description or "").lower()

    # Path-based feature rules (high confidence)
    if "/.elasticsearch-agent/skills/recipes/" in path_lower:
        return "feature"
    if re.search(r"agent_builder/\.claude/skills/(create-agent|chat-with-agent)", path_lower):
        return "feature"
    if "workflows_management/.claude/skills/workflows-yaml-reference" in path_lower:
        return "feature"
    # skills/kibana/ path prefix signals a "how to use Kibana" skill library
    if re.search(r"(^|/)skills/kibana/", path_lower):
        return "feature"

    # Path-based dev_tool rules (high confidence)
    if path_lower.startswith(".agents/"):
        return "dev_tool"
    if re.search(r"(^|/)\.agents/skills/", path_lower):
        return "dev_tool"
    # Cursor editor skills, AI setup skills, and agent-config plugins are dev tools
    if re.search(r"(^|/)\.cursor/skills/", path_lower):
        return "dev_tool"
    if re.search(r"(^|/)\.ai-setup/agent-skills/skills/", path_lower):
        return "dev_tool"
    if re.search(r"(^|/)agent-config/plugins/[^/]+/skills/", path_lower):
        return "dev_tool"
    # .github/skills/ and .gemini/skills/ are always dev tools
    if re.search(r"(^|/)\.github/skills/", path_lower):
        return "dev_tool"
    if re.search(r"(^|/)\.gemini/skills/", path_lower):
        return "dev_tool"
    # DEX dev skills are always dev tools
    if re.search(r"(^|/)skills/dex-", path_lower):
        return "dev_tool"

    # Description-based feature rules (single phrases, high confidence)
    for phrase in [
        "guide for building",
        "in a running kibana",
        "use when a developer wants to build",
        "what can elastic do",
        "get started with elasticsearch",
        "vega-lite visualization",
        "vega and vega-lite",
        # Security product features
        "threat hunting",
        "detection rule",
        "ml anomaly",
        "anomaly detection result",
        "entity risk score",
        # Non-engineering use cases
        "catch up on weekend",
        "weekend slack",
        "humanizer",
        "remove signs of ai",
        "deal summary",
        "campaign brief",
        "consulting report",
        "generate a customer",
        "customer deck",
        # Elastic product skill indicators
        "execute es|ql",
        "translate natural language" ,
        "elastic distribution of opentelemetry",
        "elastic cloud serverless",
        "kibana alerting rules",
        "elasticsearch rbac",
    ]:
        if phrase in desc_lower:
            return "feature"

    # Compound feature rules for product skills
    if "instrument" in desc_lower and "opentelemetry" in desc_lower:
        return "feature"
    if "serverless" in desc_lower and "elastic cloud" in desc_lower:
        return "feature"
    if "elastic cloud" in desc_lower and re.search(r"\b(authentication|environment|configure|project)\b", desc_lower):
        return "feature"

    # Compound feature rules
    if "triage" in desc_lower and "alert" in desc_lower:
        return "feature"
    if "slo" in desc_lower and re.search(r"\belastic\b", desc_lower) and re.search(r"\b(create|manage)\b", desc_lower):
        return "feature"
    if "ingest" in desc_lower and "into elasticsearch" in desc_lower:
        return "feature"
    if "authenticate" in desc_lower and "elasticsearch" in desc_lower and "realm" in desc_lower:
        return "feature"
    if "alert rule" in desc_lower and "kibana" in desc_lower:
        return "feature"
    if "migrate" in desc_lower and "grafana" in desc_lower and "kibana" in desc_lower:
        return "feature"
    if "renewal" in desc_lower and re.search(r"\b(review|prep)\b", desc_lower):
        return "feature"

    # Strong single-keyword/phrase dev_tool signals
    for kw in [
        "flaky", "functional test runner", "scaffold", "bundle size",
        "codeowners", "buildkite", "enzyme", "react testing library",
        "renovate", "pr review", "pull request review", "review pr", "review prs",
        "oncall", "on-call", "shift-left",
        # New dev_tool signals
        " lint", "linting", "auto-fix formatting",
        "git commit", "commit message",
        "github cli",
        "snyk",
        "performance investigation", "profiling data",
        " cve", "common vulnerabilities",
        "vpn",
        "indexed codebase", "search codebase", "codebase",
        "code simplification", "simplifies code",
        "spec-driven development", "creates specs before coding",
        "tcpdump",
        "pagerduty",
        "n+1 queries",
        "owasp",
        "module boundaries",
        "algorithmic complexity",
        "operational kpi",
        "board hygiene",
        "velocity report",
        "bulk-fetches",
        "gh api graphql",
        "readability, naming",
        "code scanning stats",
        "dead code",
        "claude code",
        "pre-commit",
        "jupyter notebook",
    ]:
        if kw in desc_lower:
            return "dev_tool"

    # Score-based fallback
    dev_score = sum(1 for kw in [
        "test", "debug", "validate", " pr ", "jest",
        "playwright", "cypress", "scout", "accessibility", "a11y",
        "i18n", "eslint", "github issue", "branch", "eval", "ci ",
        "contribution", "release", "deploy", "troubleshoot", "audit",
        "cluster", "sre", "oncall", "incident", "diagnose",
        "migrate", "migration", "refactor", "coverage", "benchmark",
        "ci/cd", "helm chart", "kubernetes", "argo", "crossplane",
        "teleport", "devctl", "runbook",
    ] if kw in desc_lower)

    feature_score = sum(1 for kw in [
        "yaml syntax", "onboarding", "what to build", "use case",
        "visualization", "dashboard", "kibana streams", "kibana canvas",
        "security solution", "endpoint security", "cloud security",
    ] if kw in desc_lower)

    if dev_score >= 2 and dev_score > feature_score:
        return "dev_tool"
    if feature_score >= 2 and feature_score > dev_score:
        return "feature"
    if dev_score == 1 and feature_score == 0:
        return "dev_tool"

    return "unclear"


def build_skill(owner: str, repo: str, path: str, default_branch: str,
                frontmatter: dict, content: str, commit_info: dict) -> dict:
    """Assemble a skill record from its parsed parts."""
    description = frontmatter.get("description", "")
    return {
        "name": frontmatter["name"],
        "description": description,
        "repo": f"{owner}/{repo}",
        "path": path,
        "url": f"https://github.com/{owner}/{repo}/blob/{default_branch}/{path}",
        "last_updated": commit_info.get("date"),
        "author": commit_info.get("author"),
        "platforms": detect_platforms(frontmatter, content),
        "tags": frontmatter.get("tags", []),
        "category": classify_skill(path, description),
    }
