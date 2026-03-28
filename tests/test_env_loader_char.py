##########################################################################################
#
# Module: tests/test_env_loader_char.py
#
# Description: Characterization tests for config/env_loader.py.
#              Validates three-tier env resolution: explicit path, config/env/ dir, .env fallback.
#
# Author: Cornelis Networks
#
##########################################################################################

import os
from pathlib import Path

import pytest

from config.env_loader import _find_env_dir, load_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    '''Remove env vars that tests may set, restoring original state.'''
    for key in ('TEST_SHARED_VAR', 'TEST_JIRA_VAR', 'TEST_GITHUB_VAR'):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def env_tree(tmp_path):
    '''Create a fake repo tree with config/env/ and pyproject.toml.'''
    (tmp_path / 'pyproject.toml').write_text('[project]\nname = "test"\n')
    env_dir = tmp_path / 'config' / 'env'
    env_dir.mkdir(parents=True)

    (env_dir / 'shared.env').write_text('TEST_SHARED_VAR=from_shared\n')
    (env_dir / 'jira.env').write_text('TEST_JIRA_VAR=from_jira\n')
    (env_dir / 'github.env').write_text('TEST_GITHUB_VAR=from_github\n')

    return tmp_path


# ---------------------------------------------------------------------------
# A) Explicit path
# ---------------------------------------------------------------------------

def test_load_env_explicit_path(tmp_path, monkeypatch):
    env_file = tmp_path / 'custom.env'
    env_file.write_text('TEST_SHARED_VAR=from_explicit\n')

    loaded = load_env(env_path=str(env_file))

    assert len(loaded) == 1
    assert str(env_file) in loaded[0]
    assert os.environ.get('TEST_SHARED_VAR') == 'from_explicit'


def test_load_env_explicit_path_missing(tmp_path):
    loaded = load_env(env_path=str(tmp_path / 'nonexistent.env'))

    assert loaded == []


# ---------------------------------------------------------------------------
# B) config/env/ directory discovery
# ---------------------------------------------------------------------------

def test_load_env_config_dir(env_tree, monkeypatch):
    monkeypatch.chdir(env_tree)

    loaded = load_env()

    assert len(loaded) == 3
    assert any('shared.env' in p for p in loaded)
    assert any('jira.env' in p for p in loaded)
    assert any('github.env' in p for p in loaded)
    assert os.environ.get('TEST_SHARED_VAR') == 'from_shared'
    assert os.environ.get('TEST_JIRA_VAR') == 'from_jira'
    assert os.environ.get('TEST_GITHUB_VAR') == 'from_github'


def test_load_env_config_dir_load_order(env_tree, monkeypatch):
    '''shared.env is loaded first; domain files can override shared values.'''
    shared = env_tree / 'config' / 'env' / 'shared.env'
    shared.write_text('TEST_SHARED_VAR=from_shared\nOVERLAP=shared_val\n')
    github = env_tree / 'config' / 'env' / 'github.env'
    github.write_text('TEST_GITHUB_VAR=from_github\nOVERLAP=github_val\n')

    monkeypatch.chdir(env_tree)
    monkeypatch.delenv('OVERLAP', raising=False)

    load_env(override=True)

    # github.env is loaded after shared.env, so its OVERLAP value wins
    assert os.environ.get('OVERLAP') == 'github_val'


def test_find_env_dir_walks_up(env_tree, monkeypatch):
    nested = env_tree / 'src' / 'agents'
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = _find_env_dir()

    assert result is not None
    assert result == env_tree / 'config' / 'env'


def test_find_env_dir_returns_none_without_pyproject(tmp_path, monkeypatch):
    env_dir = tmp_path / 'config' / 'env'
    env_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    result = _find_env_dir()

    assert result is None


# ---------------------------------------------------------------------------
# C) Root .env fallback
# ---------------------------------------------------------------------------

def test_load_env_root_dotenv_fallback(tmp_path, monkeypatch):
    (tmp_path / '.env').write_text('TEST_SHARED_VAR=from_root\n')
    monkeypatch.chdir(tmp_path)

    loaded = load_env()

    assert len(loaded) == 1
    assert '.env' in loaded[0]
    assert os.environ.get('TEST_SHARED_VAR') == 'from_root'


def test_load_env_no_files_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    loaded = load_env()

    assert loaded == []


# ---------------------------------------------------------------------------
# D) Process env precedence
# ---------------------------------------------------------------------------

def test_process_env_wins_over_file(tmp_path, monkeypatch):
    env_file = tmp_path / 'test.env'
    env_file.write_text('TEST_SHARED_VAR=from_file\n')
    monkeypatch.setenv('TEST_SHARED_VAR', 'from_process')

    load_env(env_path=str(env_file), override=False)

    assert os.environ.get('TEST_SHARED_VAR') == 'from_process'


def test_override_beats_process_env(tmp_path, monkeypatch):
    env_file = tmp_path / 'test.env'
    env_file.write_text('TEST_SHARED_VAR=from_file\n')
    monkeypatch.setenv('TEST_SHARED_VAR', 'from_process')

    load_env(env_path=str(env_file), override=True)

    assert os.environ.get('TEST_SHARED_VAR') == 'from_file'
