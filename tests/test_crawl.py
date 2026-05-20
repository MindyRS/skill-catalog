import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crawler'))

from unittest.mock import MagicMock, patch
from crawl import crawl_elastic_org, crawl_personal_repos


def make_mock_client(search_results=None, file_content="", default_branch="main", commit_info=None, tree=None):
    client = MagicMock()
    client.search_code.return_value = search_results or []
    client.get_file_content.return_value = file_content
    client.get_repo_default_branch.return_value = default_branch
    client.get_file_last_commit.return_value = commit_info or {"date": "2026-05-17", "author": "moose"}
    client.get_repo_tree.return_value = tree or []
    return client


SKILL_MD = "---\nname: debugging\ndescription: For bugs\n---\n\n# Body"
NOT_A_SKILL_MD = "# No frontmatter here"
NO_NAME_MD = "---\ndescription: Missing name\n---\n"


def test_crawl_elastic_org_returns_skill():
    search_item = {"path": "skills/SKILL.md", "repository": {"full_name": "elastic/kibana"}}
    client = make_mock_client(search_results=[search_item], file_content=SKILL_MD)

    with patch('crawl.time.sleep'):
        skills = crawl_elastic_org(client)

    assert len(skills) == 1
    assert skills[0]["name"] == "debugging"
    assert skills[0]["repo"] == "elastic/kibana"


def test_crawl_elastic_org_deduplicates():
    item = {"path": "skills/SKILL.md", "repository": {"full_name": "elastic/kibana"}}
    # Same item returned by both queries
    client = make_mock_client(search_results=[item, item], file_content=SKILL_MD)

    with patch('crawl.time.sleep'):
        skills = crawl_elastic_org(client)

    assert len(skills) == 1


def test_crawl_elastic_org_skips_no_name():
    item = {"path": "SKILL.md", "repository": {"full_name": "elastic/kibana"}}
    client = make_mock_client(search_results=[item], file_content=NO_NAME_MD)

    with patch('crawl.time.sleep'):
        skills = crawl_elastic_org(client)

    assert skills == []


def test_crawl_elastic_org_skips_on_api_error():
    item = {"path": "SKILL.md", "repository": {"full_name": "elastic/kibana"}}
    client = make_mock_client(search_results=[item])
    client.get_file_content.side_effect = Exception("404 Not Found")

    with patch('crawl.time.sleep'):
        skills = crawl_elastic_org(client)

    assert skills == []


def test_crawl_personal_repos_finds_skill_md():
    tree = [
        {"type": "blob", "path": "SKILL.md"},
        {"type": "tree", "path": "docs"},
    ]
    client = make_mock_client(tree=tree, file_content=SKILL_MD)

    with patch('crawl.time.sleep'):
        skills = crawl_personal_repos(client, ["moose/dotfiles"])

    assert len(skills) == 1
    assert skills[0]["repo"] == "moose/dotfiles"


def test_crawl_personal_repos_skips_non_skill_paths():
    tree = [{"type": "blob", "path": "README.md"}]
    client = make_mock_client(tree=tree, file_content=SKILL_MD)

    with patch('crawl.time.sleep'):
        skills = crawl_personal_repos(client, ["moose/dotfiles"])

    assert skills == []


def test_crawl_personal_repos_empty_list():
    client = make_mock_client()

    with patch('crawl.time.sleep'):
        skills = crawl_personal_repos(client, [])

    assert skills == []
    client.get_repo_tree.assert_not_called()


def test_crawl_personal_repos_skips_failed_repo():
    client = make_mock_client()
    client.get_repo_default_branch.side_effect = Exception("403 Forbidden")

    with patch('crawl.time.sleep'):
        skills = crawl_personal_repos(client, ["private/repo"])

    assert skills == []
