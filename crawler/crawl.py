import json
import os
import time
from datetime import datetime, timezone

import yaml

from github_client import GitHubClient
from skill_parser import build_skill, is_skill_candidate, parse_frontmatter


def crawl_elastic_org(client: GitHubClient, seen: set) -> list:
    """Search the elastic org for skill files using GitHub Code Search."""
    skills = []

    queries = [
        "filename:SKILL.md org:elastic",
        "path:/skills extension:md org:elastic",
    ]

    for query in queries:
        items = client.search_code(query)
        for item in items:
            repo_full = item["repository"]["full_name"]
            path = item["path"]
            key = (repo_full, path)
            if key in seen:
                continue
            seen.add(key)

            owner, repo = repo_full.split("/", 1)
            try:
                content = client.get_file_content(owner, repo, path)
                fm = parse_frontmatter(content)
                if "name" not in fm:
                    continue
                default_branch = client.get_repo_default_branch(owner, repo)
                commit_info = client.get_file_last_commit(owner, repo, path)
                skills.append(build_skill(owner, repo, path, default_branch, fm, content, commit_info))
            except Exception as e:
                print(f"Warning: skipping {repo_full}/{path}: {e}")

            time.sleep(0.1)

    return skills


def crawl_personal_repos(client: GitHubClient, repos: list) -> list:
    """Walk each curated personal repo's file tree and extract skill files."""
    skills = []

    for repo_full in repos:
        owner, repo = repo_full.split("/", 1)
        try:
            default_branch = client.get_repo_default_branch(owner, repo)
            tree = client.get_repo_tree(owner, repo, default_branch)

            for item in tree:
                if item["type"] != "blob":
                    continue
                path = item["path"]
                if not is_skill_candidate(path):
                    continue
                try:
                    content = client.get_file_content(owner, repo, path)
                    fm = parse_frontmatter(content)
                    if "name" not in fm:
                        continue
                    commit_info = client.get_file_last_commit(owner, repo, path)
                    skills.append(build_skill(owner, repo, path, default_branch, fm, content, commit_info))
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Warning: skipping {repo_full}/{path}: {e}")

        except Exception as e:
            print(f"Warning: skipping repo {repo_full}: {e}")

    return skills


def crawl_targeted_repos(client: GitHubClient, repos: list, seen: set) -> list:
    """Run a targeted Code Search per repo for repos too large for org-wide search.
    Uses filename:SKILL.md repo:{repo} to reliably find all skills regardless of
    org-wide result caps."""
    skills = []

    for repo_full in repos:
        owner, repo = repo_full.split("/", 1)
        try:
            default_branch = client.get_repo_default_branch(owner, repo)
            items = client.search_code(f"filename:SKILL.md repo:{repo_full}")
            for item in items:
                path = item["path"]
                key = (repo_full, path)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    content = client.get_file_content(owner, repo, path)
                    fm = parse_frontmatter(content)
                    if "name" not in fm:
                        continue
                    commit_info = client.get_file_last_commit(owner, repo, path)
                    skills.append(build_skill(owner, repo, path, default_branch, fm, content, commit_info))
                except Exception as e:
                    print(f"Warning: skipping {repo_full}/{path}: {e}")
                time.sleep(0.1)
        except Exception as e:
            print(f"Warning: skipping targeted repo {repo_full}: {e}")

    return skills


def main():
    token = os.environ["GH_PAT"]
    client = GitHubClient(token)

    with open("repos.yml") as f:
        config = yaml.safe_load(f) or {}
    personal_repos = config.get("personal_repos", [])
    targeted_repos = config.get("targeted_repos", [])

    seen = set()  # shared across all passes to avoid re-fetching

    print("Pass 1: Crawling elastic org via Code Search...")
    org_skills = crawl_elastic_org(client, seen)
    print(f"  Found {len(org_skills)} skills")

    print("Pass 2: Crawling targeted repos via per-repo Code Search...")
    targeted_skills = crawl_targeted_repos(client, targeted_repos, seen)
    print(f"  Found {len(targeted_skills)} skills")

    print("Pass 3: Crawling personal repos...")
    personal_skills = crawl_personal_repos(client, personal_repos)
    print(f"  Found {len(personal_skills)} skills")

    all_skills = org_skills + targeted_skills + personal_skills

    # Deduplicate by (repo, name): keep the entry with the shortest path
    seen_name = {}
    for skill in all_skills:
        key = (skill["repo"], skill["name"])
        if key not in seen_name or len(skill["path"]) < len(seen_name[key]["path"]):
            seen_name[key] = skill
    deduped = list(seen_name.values())
    if len(deduped) < len(all_skills):
        print(f"Deduped {len(all_skills) - len(deduped)} duplicate skill names ({len(deduped)} unique)")
    all_skills = deduped

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_skills),
        "skills": all_skills,
    }

    with open("site/skills.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Done. Wrote {len(all_skills)} skills to site/skills.json")


if __name__ == "__main__":
    main()
