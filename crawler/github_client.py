import base64
import time
import requests


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def search_code(self, query: str) -> list:
        """Search code across GitHub, handling pagination. Rate-limited to 30 req/min.
        GitHub Code Search caps at 1,000 results (10 pages of 100) — stops cleanly at that limit."""
        results = []
        page = 1
        while page <= 10:  # GitHub hard cap: 1,000 results max
            resp = self.session.get(
                f"{self.BASE}/search/code",
                params={"q": query, "per_page": 100, "page": page},
            )
            if resp.status_code == 403:
                print(f"Warning: Code Search cap hit at page {page} for query: {query!r}")
                break
            resp.raise_for_status()
            data = resp.json()
            results.extend(data["items"])
            if not data["items"] or len(results) >= data["total_count"]:
                break
            page += 1
            time.sleep(2)  # Code Search: 30 req/min authenticated
        if len(results) >= 900:
            print(f"Warning: Code Search near/at result cap for query: {query!r}")
        return results

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch and decode a file's content from the Contents API."""
        resp = self.session.get(f"{self.BASE}/repos/{owner}/{repo}/contents/{path}")
        resp.raise_for_status()
        data = resp.json()
        return base64.b64decode(data["content"]).decode("utf-8")

    def get_repo_default_branch(self, owner: str, repo: str) -> str:
        """Return the default branch name for a repo."""
        resp = self.session.get(f"{self.BASE}/repos/{owner}/{repo}")
        resp.raise_for_status()
        return resp.json()["default_branch"]

    def get_file_last_commit(self, owner: str, repo: str, path: str) -> dict:
        """Return the date and author login of the most recent commit touching path."""
        resp = self.session.get(
            f"{self.BASE}/repos/{owner}/{repo}/commits",
            params={"path": path, "per_page": 1},
        )
        resp.raise_for_status()
        commits = resp.json()
        if not commits:
            return {"date": None, "author": None}
        commit = commits[0]
        date = commit["commit"]["committer"]["date"][:10]
        author = (commit.get("author") or {}).get("login") or commit["commit"]["author"]["name"]
        return {"date": date, "author": author}

    def get_repo_tree(self, owner: str, repo: str, branch: str) -> list:
        """Return the full recursive file tree for a repo."""
        resp = self.session.get(
            f"{self.BASE}/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "1"},
        )
        resp.raise_for_status()
        return resp.json().get("tree", [])
