##########################################################################################
#
# Module: config/env_loader.py
#
# Description: Environment variable loader with credential-domain file support.
#              Loads config/env/*.env files for local dev parity with Docker Compose,
#              falling back to a single .env at the repository root.
#
# Author: Cornelis Networks
#
##########################################################################################

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Canonical load order mirrors Docker Compose env_file stacking:
# shared first (defaults), then credential domains (override shared if overlap).
_ENV_FILE_ORDER = [
    'shared.env',
    'jira.env',
    'llm.env',
    'github.env',
    'teams.env',
]


def _find_env_dir() -> Optional[Path]:
    '''Locate config/env/ by walking up from CWD to the repo root.'''
    cwd = Path.cwd()
    for ancestor in [cwd] + list(cwd.parents):
        candidate = ancestor / 'config' / 'env'
        # Require pyproject.toml to confirm we're at the repo root,
        # not some random config/env/ elsewhere on disk.
        if candidate.is_dir() and (ancestor / 'pyproject.toml').exists():
            return candidate
    return None


def load_env(
    env_path: Optional[str] = None,
    override: bool = False,
) -> List[str]:
    '''
    Load env vars: explicit path → config/env/*.env → root .env fallback.
    Process env always wins unless override=True.
    Returns list of loaded file paths.
    '''
    loaded: List[str] = []

    if env_path:
        path = Path(env_path).expanduser()
        if path.is_file():
            load_dotenv(dotenv_path=str(path), override=override)
            loaded.append(str(path))
            log.debug('Loaded env from explicit path: %s', path)
        else:
            log.warning('Explicit env path does not exist: %s', path)
        return loaded

    # Path 2: credential-domain files in config/env/
    env_dir = _find_env_dir()
    if env_dir is not None:
        for filename in _ENV_FILE_ORDER:
            filepath = env_dir / filename
            if filepath.is_file():
                load_dotenv(dotenv_path=str(filepath), override=override)
                loaded.append(str(filepath))
                log.debug('Loaded env domain file: %s', filepath)
        if loaded:
            return loaded

    # Path 3: fallback to repo-root .env (legacy pattern)
    # Walk from CWD upward to find .env explicitly — do NOT rely on
    # load_dotenv()'s internal find_dotenv() which starts from the
    # calling module's directory, not CWD.
    cwd = Path.cwd()
    for ancestor in [cwd] + list(cwd.parents):
        root_env = ancestor / '.env'
        if root_env.is_file():
            load_dotenv(dotenv_path=str(root_env), override=override)
            loaded.append(str(root_env))
            log.debug('Loaded env from root .env: %s', root_env)
            break

    if not loaded:
        log.debug('No .env files found; relying on process environment')

    return loaded
