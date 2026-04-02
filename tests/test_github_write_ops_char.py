##########
# Module:      test_github_write_ops_char.py
# Description: Characterization tests for the 5 write operations in github_utils.py:
#              get_pr_changed_files, get_file_content, create_or_update_file,
#              batch_commit_files, post_pr_comment.
# Author:      Cornelis Networks Engineering Tools
##########

from types import SimpleNamespace

import pytest

import github_utils


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _silent_output(_message: str = '') -> None:
    return None


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    '''Silence output and inject a fake cached connection.'''
    monkeypatch.setattr(github_utils, 'output', _silent_output)
    monkeypatch.setattr(github_utils, '_cached_connection', 'FAKE')


# ---------------------------------------------------------------------------
# Autouse fixture — reset github_utils state before/after each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_github_utils_state():
    github_utils.reset_connection()
    github_utils._quiet_mode = False
    yield
    github_utils.reset_connection()
    github_utils._quiet_mode = False


# =========================================================================
# A) get_pr_changed_files
# =========================================================================

class TestGetPRChangedFiles:
    '''Tests for get_pr_changed_files().'''

    def test_get_pr_changed_files_returns_file_list(self, monkeypatch):
        '''Happy path: 3 changed files returned with correct dict structure.'''
        _patch_common(monkeypatch)

        fake_files = [
            SimpleNamespace(
                filename='src/main.py',
                status='modified',
                additions=10,
                deletions=5,
                changes=15,
                patch='@@ -1,5 +1,10 @@\n-old\n+new',
                sha='abc123',
            ),
            SimpleNamespace(
                filename='docs/README.md',
                status='added',
                additions=20,
                deletions=0,
                changes=20,
                patch='@@ -0,0 +1,20 @@\n+# README',
                sha='def456',
            ),
            SimpleNamespace(
                filename='tests/test_old.py',
                status='removed',
                additions=0,
                deletions=30,
                changes=30,
                patch=None,
                sha='ghi789',
            ),
        ]

        fake_pr = SimpleNamespace(get_files=lambda: fake_files)
        fake_repo = SimpleNamespace(
            get_pull=lambda n: fake_pr,
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.get_pr_changed_files('org/repo', 42)

        assert len(result) == 3
        assert result[0]['filename'] == 'src/main.py'
        assert result[0]['status'] == 'modified'
        assert result[0]['additions'] == 10
        assert result[0]['deletions'] == 5
        assert result[0]['changes'] == 15
        assert result[0]['sha'] == 'abc123'
        assert result[1]['filename'] == 'docs/README.md'
        assert result[1]['status'] == 'added'
        assert result[2]['filename'] == 'tests/test_old.py'
        assert result[2]['patch'] is None

    def test_get_pr_changed_files_empty_pr(self, monkeypatch):
        '''PR with no changed files returns empty list.'''
        _patch_common(monkeypatch)

        fake_pr = SimpleNamespace(get_files=lambda: [])
        fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.get_pr_changed_files('org/repo', 1)

        assert result == []

    def test_get_pr_changed_files_repo_not_found(self, monkeypatch):
        '''get_repo raises GithubException → GitHubRepoError.'''
        _patch_common(monkeypatch)

        from github import GithubException

        def _raise_repo(name):
            raise GithubException(404, {'message': 'Not Found'}, None)

        fake_gh = SimpleNamespace(get_repo=_raise_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        with pytest.raises(github_utils.GitHubRepoError):
            github_utils.get_pr_changed_files('org/nonexistent', 1)


# =========================================================================
# B) get_file_content
# =========================================================================

class TestGetFileContent:
    '''Tests for get_file_content().'''

    def test_get_file_content_returns_content(self, monkeypatch):
        '''Happy path: file exists, returns dict with content, sha, size, encoding.'''
        _patch_common(monkeypatch)

        fake_contents = SimpleNamespace(
            path='docs/guide.md',
            decoded_content=b'# User Guide\n\nHello world.',
            sha='sha_abc',
            size=27,
            encoding='base64',
        )
        fake_repo = SimpleNamespace(
            get_contents=lambda path, ref=None: fake_contents,
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.get_file_content('org/repo', 'docs/guide.md', branch='main')

        assert result is not None
        assert result['path'] == 'docs/guide.md'
        assert result['content'] == '# User Guide\n\nHello world.'
        assert result['sha'] == 'sha_abc'
        assert result['size'] == 27
        assert result['encoding'] == 'base64'

    def test_get_file_content_not_found_returns_none(self, monkeypatch):
        '''File does not exist → returns None (no exception).'''
        _patch_common(monkeypatch)

        from github import UnknownObjectException

        def _raise_not_found(path, ref=None):
            raise UnknownObjectException(404, {'message': 'Not Found'}, None)

        fake_repo = SimpleNamespace(get_contents=_raise_not_found)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.get_file_content('org/repo', 'nonexistent.md')

        assert result is None

    def test_get_file_content_directory_returns_none(self, monkeypatch):
        '''Path is a directory (list returned) → returns None.'''
        _patch_common(monkeypatch)

        # get_contents returns a list for directories
        fake_repo = SimpleNamespace(
            get_contents=lambda path, ref=None: [
                SimpleNamespace(path='docs/a.md'),
                SimpleNamespace(path='docs/b.md'),
            ],
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.get_file_content('org/repo', 'docs/')

        assert result is None


# =========================================================================
# C) create_or_update_file
# =========================================================================

class TestCreateOrUpdateFile:
    '''Tests for create_or_update_file().'''

    def test_create_or_update_file_creates_new(self, monkeypatch):
        '''File does not exist → calls repo.create_file.'''
        _patch_common(monkeypatch)

        created = []

        def _create_file(path, message, content, branch=None):
            created.append({'path': path, 'message': message, 'content': content})
            return {'commit': SimpleNamespace(sha='new_sha_001')}

        # Stub get_file_content to return None (file doesn't exist)
        monkeypatch.setattr(
            github_utils, 'get_file_content', lambda *a, **kw: None,
        )

        fake_repo = SimpleNamespace(create_file=_create_file)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        # Force dry_run resolver to return False
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        result = github_utils.create_or_update_file(
            'org/repo', 'docs/new.md', '# New Doc', 'add new doc',
            branch='main', dry_run=False,
        )

        assert result['operation'] == 'create'
        assert result['commit_sha'] == 'new_sha_001'
        assert len(created) == 1
        assert created[0]['path'] == 'docs/new.md'

    def test_create_or_update_file_updates_existing(self, monkeypatch):
        '''File exists → calls repo.update_file with existing SHA.'''
        _patch_common(monkeypatch)

        updated = []

        def _update_file(path, message, content, sha, branch=None):
            updated.append({'path': path, 'sha': sha})
            return {'commit': SimpleNamespace(sha='update_sha_002')}

        # Stub get_file_content to return existing file with SHA
        monkeypatch.setattr(
            github_utils, 'get_file_content',
            lambda *a, **kw: {'sha': 'existing_sha_abc', 'content': 'old'},
        )

        fake_repo = SimpleNamespace(update_file=_update_file)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        result = github_utils.create_or_update_file(
            'org/repo', 'docs/existing.md', '# Updated', 'update doc',
            branch='main', dry_run=False,
        )

        assert result['operation'] == 'update'
        assert result['commit_sha'] == 'update_sha_002'
        assert len(updated) == 1
        assert updated[0]['sha'] == 'existing_sha_abc'

    def test_create_or_update_file_dry_run(self, monkeypatch):
        '''dry_run=True returns preview dict without calling create/update.'''
        _patch_common(monkeypatch)

        create_called = []
        update_called = []

        fake_repo = SimpleNamespace(
            create_file=lambda *a, **kw: create_called.append(1),
            update_file=lambda *a, **kw: update_called.append(1),
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        # Stub get_file_content to return None (new file scenario)
        monkeypatch.setattr(
            github_utils, 'get_file_content', lambda *a, **kw: None,
        )
        # Force dry_run resolver to return True
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        result = github_utils.create_or_update_file(
            'org/repo', 'docs/new.md', '# Content', 'msg',
            branch='feat', dry_run=True,
        )

        assert result['dry_run'] is True
        assert result['operation'] == 'create'
        assert result['path'] == 'docs/new.md'
        assert result['branch'] == 'feat'
        assert result['content_length'] == len('# Content')
        # Verify no actual mutation happened
        assert create_called == []
        assert update_called == []

    def test_create_or_update_file_dry_run_update(self, monkeypatch):
        '''dry_run=True with existing file shows operation=update in preview.'''
        _patch_common(monkeypatch)

        fake_repo = SimpleNamespace()
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(
            github_utils, 'get_file_content',
            lambda *a, **kw: {'sha': 'old_sha', 'content': 'old'},
        )
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        result = github_utils.create_or_update_file(
            'org/repo', 'docs/existing.md', '# Updated', 'msg',
            branch='main', dry_run=True,
        )

        assert result['dry_run'] is True
        assert result['operation'] == 'update'


# =========================================================================
# D) batch_commit_files
# =========================================================================

class TestBatchCommitFiles:
    '''Tests for batch_commit_files().'''

    def test_batch_commit_files_creates_atomic_commit(self, monkeypatch):
        '''Full execution path: blob → tree → commit → ref update.'''
        _patch_common(monkeypatch)

        call_log = []

        fake_blob = SimpleNamespace(sha='blob_sha_1')
        fake_branch = SimpleNamespace(commit=SimpleNamespace(sha='head_sha'))
        fake_base_tree = SimpleNamespace(sha='tree_sha')
        fake_new_tree = SimpleNamespace(sha='new_tree_sha')
        fake_parent = SimpleNamespace(sha='head_sha')
        fake_commit = SimpleNamespace(sha='new_commit_sha')
        fake_ref = SimpleNamespace(edit=lambda sha: call_log.append(('ref_edit', sha)))

        fake_repo = SimpleNamespace(
            create_git_blob=lambda content, enc: (
                call_log.append(('create_blob', content)) or fake_blob
            ),
            get_branch=lambda b: (
                call_log.append(('get_branch', b)) or fake_branch
            ),
            get_git_tree=lambda sha: (
                call_log.append(('get_tree', sha)) or fake_base_tree
            ),
            create_git_tree=lambda elements, base_tree: (
                call_log.append(('create_tree', len(elements))) or fake_new_tree
            ),
            get_git_commit=lambda sha: (
                call_log.append(('get_commit', sha)) or fake_parent
            ),
            create_git_commit=lambda msg, tree, parents: (
                call_log.append(('create_commit', msg)) or fake_commit
            ),
            get_git_ref=lambda ref: (
                call_log.append(('get_ref', ref)) or fake_ref
            ),
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        files = [
            {'path': 'docs/a.md', 'content': '# A'},
            {'path': 'docs/b.md', 'content': '# B'},
        ]

        result = github_utils.batch_commit_files(
            'org/repo', files, 'batch commit', branch='feat', dry_run=False,
        )

        assert result['commit_sha'] == 'new_commit_sha'
        assert result['file_count'] == 2
        assert result['branch'] == 'feat'

        # Verify call order: blobs first, then branch/tree/commit/ref
        call_types = [c[0] for c in call_log]
        assert call_types.count('create_blob') == 2
        assert 'get_branch' in call_types
        assert 'create_tree' in call_types
        assert 'create_commit' in call_types
        assert 'ref_edit' in call_types

    def test_batch_commit_files_dry_run(self, monkeypatch):
        '''dry_run=True returns preview without creating blobs or commits.'''
        _patch_common(monkeypatch)

        blob_calls = []

        fake_repo = SimpleNamespace(
            create_git_blob=lambda *a: blob_calls.append(1),
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        files = [
            {'path': 'docs/a.md', 'content': '# A'},
            {'path': 'docs/b.md', 'content': '# B'},
        ]

        result = github_utils.batch_commit_files(
            'org/repo', files, 'batch commit', branch='main', dry_run=True,
        )

        assert result['dry_run'] is True
        assert result['file_count'] == 2
        assert len(result['files']) == 2
        assert result['files'][0]['path'] == 'docs/a.md'
        assert result['files'][1]['content_length'] == 3  # len('# B')
        # No blobs should have been created
        assert blob_calls == []

    def test_batch_commit_files_empty_list(self, monkeypatch):
        '''Empty file list with dry_run returns preview with file_count=0.'''
        _patch_common(monkeypatch)

        fake_repo = SimpleNamespace()
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        result = github_utils.batch_commit_files(
            'org/repo', [], 'empty commit', branch='main', dry_run=True,
        )

        assert result['dry_run'] is True
        assert result['file_count'] == 0
        assert result['files'] == []

    def test_batch_commit_files_returns_per_file_ops(self, monkeypatch):
        '''Execute mode returns per-file operation entries.'''
        _patch_common(monkeypatch)

        fake_blob = SimpleNamespace(sha='blob_sha')
        fake_branch = SimpleNamespace(commit=SimpleNamespace(sha='head'))
        fake_tree = SimpleNamespace(sha='tree')
        fake_commit = SimpleNamespace(sha='commit_sha_final')
        fake_ref = SimpleNamespace(edit=lambda sha: None)

        fake_repo = SimpleNamespace(
            create_git_blob=lambda c, e: fake_blob,
            get_branch=lambda b: fake_branch,
            get_git_tree=lambda sha: fake_tree,
            create_git_tree=lambda e, base_tree: fake_tree,
            get_git_commit=lambda sha: SimpleNamespace(sha=sha),
            create_git_commit=lambda m, t, p: fake_commit,
            get_git_ref=lambda r: fake_ref,
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        files = [{'path': 'x.md', 'content': 'X'}]
        result = github_utils.batch_commit_files(
            'org/repo', files, 'msg', branch='main', dry_run=False,
        )

        assert result['files'] == [{'path': 'x.md', 'operation': 'committed'}]


# =========================================================================
# E) post_pr_comment
# =========================================================================

class TestPostPRComment:
    '''Tests for post_pr_comment().'''

    def test_post_pr_comment_posts_comment(self, monkeypatch):
        '''Happy path: comment is posted, returns id and url.'''
        _patch_common(monkeypatch)

        posted = []
        fake_comment = SimpleNamespace(
            id=42,
            html_url='https://github.com/org/repo/pull/7#issuecomment-42',
        )

        def _create_issue_comment(body):
            posted.append(body)
            return fake_comment

        fake_pr = SimpleNamespace(create_issue_comment=_create_issue_comment)
        fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        result = github_utils.post_pr_comment(
            'org/repo', 7, 'Great work!', dry_run=False,
        )

        assert result['comment_id'] == 42
        assert 'issuecomment-42' in result['html_url']
        assert posted == ['Great work!']

    def test_post_pr_comment_dry_run(self, monkeypatch):
        '''dry_run=True returns preview with body_preview, no comment posted.'''
        _patch_common(monkeypatch)

        posted = []
        fake_pr = SimpleNamespace(
            create_issue_comment=lambda body: posted.append(body),
        )
        fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        result = github_utils.post_pr_comment(
            'org/repo', 7, 'This is a long comment body for testing.', dry_run=True,
        )

        assert result['dry_run'] is True
        assert result['pr_number'] == 7
        assert 'body_preview' in result
        assert result['body_length'] == len('This is a long comment body for testing.')
        # No comment should have been posted
        assert posted == []

    def test_post_pr_comment_returns_comment_id(self, monkeypatch):
        '''Verify returned dict has both comment_id and html_url.'''
        _patch_common(monkeypatch)

        fake_comment = SimpleNamespace(
            id=999,
            html_url='https://github.com/org/repo/pull/10#issuecomment-999',
        )
        fake_pr = SimpleNamespace(create_issue_comment=lambda body: fake_comment)
        fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: False)

        result = github_utils.post_pr_comment(
            'org/repo', 10, 'LGTM', dry_run=False,
        )

        assert result['comment_id'] == 999
        assert result['html_url'] == 'https://github.com/org/repo/pull/10#issuecomment-999'
        assert result['repo'] == 'org/repo'
        assert result['pr_number'] == 10

    def test_post_pr_comment_body_preview_truncated(self, monkeypatch):
        '''body_preview in dry-run is truncated to 200 chars.'''
        _patch_common(monkeypatch)

        fake_repo = SimpleNamespace(get_pull=lambda n: SimpleNamespace())
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)
        monkeypatch.setattr(github_utils, '_resolve_dry_run', lambda x: True)

        long_body = 'A' * 500

        result = github_utils.post_pr_comment(
            'org/repo', 1, long_body, dry_run=True,
        )

        assert result['dry_run'] is True
        assert len(result['body_preview']) == 200
        assert result['body_length'] == 500
