import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crawler'))

import base64
from unittest.mock import MagicMock, patch, call
from github_client import GitHubClient


def make_client():
    return GitHubClient("fake-token")


def test_client_sets_auth_header():
    client = make_client()
    assert client.session.headers["Authorization"] == "Bearer fake-token"


def test_get_file_content_decodes_base64():
    client = make_client()
    raw = "---\nname: test\n---\n"
    encoded = base64.b64encode(raw.encode()).decode()

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"content": encoded + "\n", "encoding": "base64"}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', return_value=mock_resp):
        content = client.get_file_content("elastic", "kibana", "SKILL.md")

    assert content == raw


def test_get_repo_default_branch():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"default_branch": "main", "name": "kibana"}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', return_value=mock_resp):
        branch = client.get_repo_default_branch("elastic", "kibana")

    assert branch == "main"


def test_get_file_last_commit_returns_date_and_author():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{
        "commit": {"committer": {"date": "2026-05-17T10:00:00Z"}, "author": {"name": "moose"}},
        "author": {"login": "moose"}
    }]
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', return_value=mock_resp):
        info = client.get_file_last_commit("elastic", "kibana", "SKILL.md")

    assert info["date"] == "2026-05-17"
    assert info["author"] == "moose"


def test_get_file_last_commit_no_commits():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', return_value=mock_resp):
        info = client.get_file_last_commit("elastic", "kibana", "SKILL.md")

    assert info == {"date": None, "author": None}


def test_get_repo_tree_returns_blob_list():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "tree": [
            {"type": "blob", "path": "SKILL.md"},
            {"type": "tree", "path": "skills"},
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', return_value=mock_resp):
        tree = client.get_repo_tree("org", "repo", "main")

    assert {"type": "blob", "path": "SKILL.md"} in tree


def test_search_code_paginates():
    client = make_client()

    page1 = MagicMock()
    page1.json.return_value = {"total_count": 2, "items": [{"path": "a/SKILL.md", "repository": {"full_name": "e/r"}}]}
    page1.raise_for_status = MagicMock()

    page2 = MagicMock()
    page2.json.return_value = {"total_count": 2, "items": [{"path": "b/SKILL.md", "repository": {"full_name": "e/r"}}]}
    page2.raise_for_status = MagicMock()

    page3 = MagicMock()
    page3.json.return_value = {"total_count": 2, "items": []}
    page3.raise_for_status = MagicMock()

    with patch.object(client.session, 'get', side_effect=[page1, page2, page3]):
        with patch('github_client.time.sleep'):
            results = client.search_code("filename:SKILL.md org:elastic")

    assert len(results) == 2
