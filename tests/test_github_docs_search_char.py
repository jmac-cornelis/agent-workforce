##########
# Module:      test_github_docs_search_char.py
# Description: Characterization tests for GitHub documentation search capabilities.
#              Covers get_repo_readme(), list_repo_docs(), search_repo_docs() in
#              github_utils.py and their tool wrappers in tools/github_tools.py.
# Author:      Cornelis Networks Engineering Tools
##########

import sys
from types import SimpleNamespace
from typing import Any, Optional

import pytest

import github_utils


def _silent_output(_message: str = '') -> None:
    return None


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github_utils, 'output', _silent_output)


@pytest.fixture(autouse=True)
def reset_github_utils_state():
    github_utils.reset_connection()
    github_utils._quiet_mode = False
    yield
    github_utils.reset_connection()
    github_utils._quiet_mode = False


# ===========================================================================
# A) get_repo_readme()
# ===========================================================================

def test_get_repo_readme_returns_content(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    fake_readme = SimpleNamespace(
        decoded_content=b'# OPA PSM2\nPerformance Scaled Messaging 2',
        name='README.md',
        size=42,
        sha='abc123',
        html_url='https://github.com/cornelisnetworks/opa-psm2/blob/main/README.md',
    )
    fake_repo = SimpleNamespace(get_readme=lambda: fake_readme)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    result = github_utils.get_repo_readme('cornelisnetworks/opa-psm2')

    assert result['repo'] == 'cornelisnetworks/opa-psm2'
    assert result['filename'] == 'README.md'
    assert 'OPA PSM2' in result['content']
    assert result['size'] == 42
    assert result['sha'] == 'abc123'
    assert 'html_url' in result or 'url' in result


def test_get_repo_readme_not_found(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    def _raise_github_exc():
        raise github_utils.GithubException(404, 'Not Found', None)

    fake_repo = SimpleNamespace(get_readme=_raise_github_exc)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    result = github_utils.get_repo_readme('cornelisnetworks/opa-psm2')

    assert result['repo'] == 'cornelisnetworks/opa-psm2'
    assert 'error' in result


# ===========================================================================
# B) list_repo_docs()
# ===========================================================================

def test_list_repo_docs_returns_files(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    fake_files = [
        SimpleNamespace(
            type='file', name='guide.md', path='docs/guide.md',
            size=1024, sha='sha1', html_url='https://github.com/org/repo/blob/main/docs/guide.md',
        ),
        SimpleNamespace(
            type='file', name='notes.txt', path='docs/notes.txt',
            size=512, sha='sha2', html_url='https://github.com/org/repo/blob/main/docs/notes.txt',
        ),
    ]
    fake_repo = SimpleNamespace(
        get_contents=lambda path: fake_files,
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    docs = github_utils.list_repo_docs('cornelisnetworks/opa-psm2', path='docs')

    assert len(docs) == 2
    assert docs[0]['name'] == 'guide.md'
    assert docs[0]['type'] == 'file'
    assert 'path' in docs[0]
    assert 'size' in docs[0]


def test_list_repo_docs_recursive(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    subdir_file = SimpleNamespace(
        type='file', name='deep.md', path='docs/sub/deep.md',
        size=256, sha='sha3', html_url='https://github.com/org/repo/blob/main/docs/sub/deep.md',
    )
    subdir = SimpleNamespace(type='dir', name='sub', path='docs/sub')
    top_file = SimpleNamespace(
        type='file', name='top.md', path='docs/top.md',
        size=128, sha='sha4', html_url='https://github.com/org/repo/blob/main/docs/top.md',
    )

    def _get_contents(path):
        if path == 'docs':
            return [top_file, subdir]
        elif path == 'docs/sub':
            return [subdir_file]
        return []

    fake_repo = SimpleNamespace(get_contents=_get_contents)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    docs = github_utils.list_repo_docs('cornelisnetworks/opa-psm2', path='docs')

    assert len(docs) == 2
    paths = [d['path'] for d in docs]
    assert 'docs/top.md' in paths
    assert 'docs/sub/deep.md' in paths


def test_list_repo_docs_path_not_found(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    def _raise_github_exc(path):
        raise github_utils.GithubException(404, 'Not Found', None)

    fake_repo = SimpleNamespace(get_contents=_raise_github_exc)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    docs = github_utils.list_repo_docs('cornelisnetworks/opa-psm2', path='nonexistent')

    assert docs == []


# ===========================================================================
# C) search_repo_docs()
# ===========================================================================

def test_search_repo_docs_returns_results(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    fake_item = SimpleNamespace(
        path='docs/guide.md',
        name='guide.md',
        repository=SimpleNamespace(full_name='cornelisnetworks/opa-psm2'),
        html_url='https://github.com/cornelisnetworks/opa-psm2/blob/main/docs/guide.md',
        score=1.0,
        text_matches=[SimpleNamespace(fragment='PSM2 architecture overview')],
    )

    fake_gh = SimpleNamespace(
        get_repo=lambda name: SimpleNamespace(),
        search_code=lambda q: [fake_item],
    )
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    results = github_utils.search_repo_docs('cornelisnetworks/opa-psm2', 'PSM2')

    assert len(results) == 1
    assert results[0]['path'] == 'docs/guide.md'
    assert results[0]['name'] == 'guide.md'
    assert results[0]['repo'] == 'cornelisnetworks/opa-psm2'


def test_search_repo_docs_empty(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    fake_gh = SimpleNamespace(
        get_repo=lambda name: SimpleNamespace(),
        search_code=lambda q: [],
    )
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    results = github_utils.search_repo_docs('cornelisnetworks/opa-psm2', 'nonexistent')

    assert results == []


# ===========================================================================
# D) Tool wrappers — tools/github_tools.py
# ===========================================================================

def test_get_repo_readme_tool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    from tools.base import ToolStatus

    fake_readme_result = {
        'repo': 'cornelisnetworks/opa-psm2',
        'filename': 'README.md',
        'content': '# PSM2',
        'size': 10,
        'sha': 'abc',
        'url': 'https://github.com/cornelisnetworks/opa-psm2/blob/main/README.md',
    }
    monkeypatch.setattr(
        'tools.github_tools._get_repo_readme',
        lambda repo_name: fake_readme_result,
    )
    monkeypatch.setattr(
        'tools.github_tools.get_github',
        lambda: SimpleNamespace(),
    )

    from tools.github_tools import get_repo_readme
    result = get_repo_readme('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert result.status == ToolStatus.SUCCESS
    assert result.data['filename'] == 'README.md'


def test_list_repo_docs_tool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    from tools.base import ToolStatus

    fake_docs = [
        {'path': 'docs/guide.md', 'name': 'guide.md', 'size': 100, 'sha': 's1', 'url': 'u1', 'type': 'file'},
    ]
    monkeypatch.setattr(
        'tools.github_tools._list_repo_docs',
        lambda repo_name, path='docs', extensions=None: fake_docs,
    )
    monkeypatch.setattr(
        'tools.github_tools.get_github',
        lambda: SimpleNamespace(),
    )

    from tools.github_tools import list_repo_docs
    result = list_repo_docs('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert result.status == ToolStatus.SUCCESS
    assert result.metadata.get('count') == 1


def test_search_repo_docs_tool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    from tools.base import ToolStatus

    fake_results = [
        {'path': 'docs/guide.md', 'name': 'guide.md', 'repo': 'org/repo', 'url': 'u1', 'score': 1.0, 'text_matches': []},
    ]
    monkeypatch.setattr(
        'tools.github_tools._search_repo_docs',
        lambda repo_name, query, extensions=None: fake_results,
    )
    monkeypatch.setattr(
        'tools.github_tools.get_github',
        lambda: SimpleNamespace(),
    )

    from tools.github_tools import search_repo_docs
    result = search_repo_docs('cornelisnetworks/opa-psm2', 'PSM2')

    assert result.is_success
    assert result.status == ToolStatus.SUCCESS
    assert result.metadata.get('count') == 1
    assert result.metadata.get('query') == 'PSM2'
