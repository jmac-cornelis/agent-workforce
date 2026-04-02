##########################################################################################
#
# Script name: github_utils.py
#
# Description: GitHub utilities for interacting with Cornelis Networks GitHub repositories.
#
# Author: John Macdonald
#
# Credentials:
#   This script uses GitHub Personal Access Tokens for authentication. To set up:
#   1. Generate a PAT at: https://github.com/settings/tokens
#   2. Set environment variables:
#      export GITHUB_TOKEN="your_personal_access_token_here"
#   
#   NEVER commit credentials to version control.
#
##########################################################################################

import argparse
import logging
import re
import sys
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

# Load environment variables from the default .env if present.
#
# CLI users can override this at runtime with --env; see handle_args().
# We use override=False here so real process environment variables (e.g. set by CI)
# still take precedence.
load_dotenv(override=False)

try:
    from github import Github, Auth, GithubException, RateLimitExceededException, UnknownObjectException
    from github import InputGitTreeElement
except ImportError:
    Github = None

    class Auth:  # type: ignore[no-redef]
        @staticmethod
        def Token(token):
            return token

    class GithubException(Exception):  # type: ignore[no-redef]
        pass

    class RateLimitExceededException(GithubException):  # type: ignore[no-redef]
        pass

    class UnknownObjectException(GithubException):  # type: ignore[no-redef]
        pass

# ****************************************************************************************
# Global data and configuration
# ****************************************************************************************
# Set global variables here and log.debug them below

DEFAULT_GITHUB_URL = 'https://api.github.com'

# GitHub configuration (allow override via env / .env)
GITHUB_URL = os.getenv('GITHUB_API_URL', DEFAULT_GITHUB_URL)

# Logging config
log = logging.getLogger(os.path.basename(sys.argv[0]))
log.setLevel(logging.DEBUG)

# File handler for logging
fh = logging.FileHandler('github_utils.log', mode='w')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)-15s [%(funcName)25s:%(lineno)-5s] %(levelname)-8s %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)  # Add file handler to logger

log.debug(f'Global data and configuration for this script...')
log.debug(f'GITHUB_URL: {GITHUB_URL}')

# Output control - set by handle_args()
_quiet_mode = False

# Public API surface — used by `from github_utils import *` and tooling introspection.
__all__ = [
    # Connection
    'connect_to_github', 'get_connection', 'reset_connection',
    'get_github_credentials',
    # Repositories
    'list_repos', 'get_repo_info', 'validate_repo',
    # Pull Requests
    'list_pull_requests', 'get_pull_request',
    'get_pr_reviews', 'get_pr_review_requests',
    # Hygiene Analysis
    'analyze_pr_staleness', 'analyze_missing_reviews',
    'analyze_repo_pr_hygiene',
    # Extended Hygiene
    'analyze_naming_compliance', 'analyze_merge_conflicts',
    'analyze_ci_failures', 'analyze_stale_branches',
    'analyze_extended_hygiene',
    # Documentation Search
    'get_repo_readme', 'list_repo_docs', 'search_repo_docs',
    # Write Operations
    'get_pr_changed_files', 'get_file_content',
    'create_or_update_file', 'batch_commit_files',
    'post_pr_comment', 'post_commit_status',
    # Rate Limit
    'get_rate_limit', 'check_rate_limit',
    # Display helpers
    'output',
    # Exceptions
    'Error', 'GitHubConnectionError', 'GitHubCredentialsError',
    'GitHubRepoError', 'GitHubPRError',
]


def output(message=''):
    '''
    Print user-facing output, respecting quiet mode.
    Always logs to file regardless of quiet mode.

    For tables and user-facing output:
    - stdout: Clean output without logger prefix (via print)
    - log file: Full logger format with timestamps (written directly to file handler)

    Input:
        message: String to output (default empty for blank line).

    Output:
        None; prints to stdout unless in quiet mode.

    Side Effects:
        Always logs message to log file at INFO level.
    '''
    # Log to file only (bypass stdout handler by writing directly to file handler)
    if message:
        record = logging.LogRecord(
            name=log.name,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg=f'OUTPUT: {message}',
            args=(),
            exc_info=None,
            func='output'
        )
        fh.emit(record)

    # Only print to stdout if not in quiet mode (clean output)
    if not _quiet_mode:
        print(message)


# ****************************************************************************************
# Display helpers — PR table formatting
# ****************************************************************************************

def print_pr_table_header():
    '''Print the header row for PR tables.'''
    output('-' * 170)
    output(f'{"#":<8} {"State":<10} {"Author":<18} {"Created":<12} {"Updated":<12} {"Reviews":<9} {"Draft":<7} {"Base":<18} {"Head":<18} {"Title":<50}')
    output('-' * 170)


def print_pr_row(pr):
    '''
    Print a single PR row in the standard table format.

    Input:
        pr: PR dict from _normalize_pr().
    '''
    number = str(pr.get('number', 'N/A'))
    state = pr.get('state', 'N/A')
    author = pr.get('author', 'N/A')
    created = pr.get('created_at', 'N/A')
    if created and created != 'N/A':
        created = created[:10]
    updated = pr.get('updated_at', 'N/A')
    if updated and updated != 'N/A':
        updated = updated[:10]
    review_count = str(pr.get('review_count', 0))
    draft = 'Yes' if pr.get('draft', False) else 'No'
    base_branch = pr.get('base_branch', 'N/A')
    head_branch = pr.get('head_branch', 'N/A')
    title = pr.get('title', 'N/A')

    # Truncate for display
    if len(author) > 16:
        author = author[:16] + '..'
    if len(base_branch) > 16:
        base_branch = base_branch[:16] + '..'
    if len(head_branch) > 16:
        head_branch = head_branch[:16] + '..'
    if len(title) > 48:
        title = title[:48] + '..'

    output(f'{number:<8} {state:<10} {author:<18} {created:<12} {updated:<12} {review_count:<9} {draft:<7} {base_branch:<18} {head_branch:<18} {title:<50}')


def print_pr_table_footer(count):
    '''Print the footer row for PR tables.'''
    output('=' * 170)
    output(f'Total: {count} pull requests')
    output('')


# ****************************************************************************************
# Exceptions
# ****************************************************************************************

class Error(Exception):
    '''
    Base class for exceptions in this module.
    '''
    pass


class GitHubConnectionError(Error):
    '''
    Exception raised when GitHub connection fails.
    '''
    def __init__(self, message):
        self.message = f'GitHub connection failed: {message}'
        super().__init__(self.message)


class GitHubCredentialsError(Error):
    '''
    Exception raised when GitHub credentials are missing or invalid.
    '''
    def __init__(self, message):
        self.message = f'GitHub credentials error: {message}'
        super().__init__(self.message)


class GitHubRepoError(Error):
    '''
    Exception raised when GitHub repository operations fail.
    '''
    def __init__(self, message):
        self.message = f'GitHub repository error: {message}'
        super().__init__(self.message)


class GitHubPRError(Error):
    '''
    Exception raised when GitHub PR operations fail.
    '''
    def __init__(self, message):
        self.message = f'GitHub PR error: {message}'
        super().__init__(self.message)


# ****************************************************************************************
# Functions
# ****************************************************************************************

def get_github_credentials():
    '''
    Retrieve GitHub token from environment variables.

    Input:
        None directly; reads from environment variable GITHUB_TOKEN.

    Output:
        String containing the GitHub personal access token.

    Raises:
        GitHubCredentialsError: If required environment variable is not set.
    '''
    log.debug('Entering get_github_credentials()')
    token = os.environ.get('GITHUB_TOKEN')

    if not token:
        raise GitHubCredentialsError('GITHUB_TOKEN environment variable not set')

    log.debug('Retrieved GitHub token (redacted)')
    return token


def connect_to_github():
    '''
    Establish connection to GitHub using PAT authentication.

    Input:
        None directly; uses credentials from environment variables.

    Output:
        Github object connected to the GitHub API (or GitHub Enterprise).

    Raises:
        GitHubConnectionError: If connection to GitHub fails.
        GitHubCredentialsError: If credentials are missing.
    '''
    log.debug('Entering connect_to_github()')
    if Github is None:
        raise GitHubConnectionError(
            'PyGithub package not installed. Run: pip install PyGithub'
        )

    token = get_github_credentials()

    log.info(f'Connecting to GitHub at {GITHUB_URL}...')
    try:
        kwargs = {'auth': Auth.Token(token)}
        if GITHUB_URL != DEFAULT_GITHUB_URL:
            kwargs['base_url'] = GITHUB_URL
        gh = Github(**kwargs)
        # Verify connection by fetching authenticated user
        user = gh.get_user().login
        log.info(f'Successfully connected to GitHub as {user}')
        return gh
    except Exception as e:
        raise GitHubConnectionError(str(e))


# ---------------------------------------------------------------------------
# Cached connection management
# ---------------------------------------------------------------------------

_cached_connection = None
_graphql_session = None


def get_connection():
    '''
    Get or create a cached GitHub connection.

    Returns the same Github object on repeated calls, avoiding redundant
    authentication.  Call reset_connection() to force a fresh connection
    (e.g. after changing credentials or for testing).

    Output:
        Github object with active connection.

    Raises:
        GitHubConnectionError: If connection fails.
    '''
    global _cached_connection
    if _cached_connection is None:
        _cached_connection = connect_to_github()
    return _cached_connection


def _get_graphql_session():
    '''Return a reusable requests.Session configured for GitHub GraphQL.'''
    global _graphql_session
    if _graphql_session is None:
        import requests as _req
        token = get_github_credentials()
        _graphql_session = _req.Session()
        _graphql_session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        })
    return _graphql_session


def _graphql_list_open_prs(owner, name):
    '''Fetch all open PRs via GraphQL (single HTTP request per 100 PRs).

    Returns a list of normalised PR dicts identical in shape to those
    returned by list_pull_requests(), but fetched in O(1) API calls
    instead of O(N).
    '''
    query = '''
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 100, states: OPEN,
                     orderBy: {field: UPDATED_AT, direction: DESC},
                     after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number title isDraft url
            createdAt updatedAt mergedAt closedAt
            headRefName baseRefName
            author { login }
            labels(first: 20)         { nodes { name } }
            reviewRequests(first: 20) {
              nodes { requestedReviewer {
                ... on User { login }
                ... on Team { slug }
              }}
            }
            reviews(last: 30)         { totalCount nodes { state } }
          }
        }
      }
    }
    '''
    session = _get_graphql_session()
    all_prs = []
    cursor = None
    while True:
        resp = session.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {
                'owner': owner, 'name': name, 'cursor': cursor,
            }},
        )
        body = resp.json()
        if 'errors' in body:
            raise GitHubPRError(f'GraphQL error: {body["errors"]}')

        pr_data = body['data']['repository']['pullRequests']
        for node in pr_data['nodes']:
            reviewer_users = []
            reviewer_teams = []
            for rr in node.get('reviewRequests', {}).get('nodes', []):
                rrev = rr.get('requestedReviewer') or {}
                if 'login' in rrev:
                    reviewer_users.append(rrev['login'])
                elif 'slug' in rrev:
                    reviewer_teams.append(rrev['slug'])

            reviews_data = node.get('reviews', {})
            review_count = reviews_data.get('totalCount', 0)
            approved = any(
                r.get('state') == 'APPROVED'
                for r in reviews_data.get('nodes', [])
            )

            all_prs.append({
                'number': node['number'],
                'title': node['title'],
                'author': (node.get('author') or {}).get('login', 'unknown'),
                'state': 'open',
                'created_at': node['createdAt'],
                'updated_at': node['updatedAt'],
                'merged_at': node.get('mergedAt'),
                'closed_at': node.get('closedAt'),
                'head_branch': node['headRefName'],
                'base_branch': node['baseRefName'],
                'draft': node['isDraft'],
                'mergeable': None,
                'html_url': node['url'],
                'requested_reviewers': reviewer_users,
                'requested_teams': reviewer_teams,
                'labels': [l['name'] for l in node.get('labels', {}).get('nodes', [])],
                'review_count': review_count,
                'approved': approved,
            })

        page_info = pr_data['pageInfo']
        if not page_info['hasNextPage']:
            break
        cursor = page_info['endCursor']

    log.info(f'GraphQL fetched {len(all_prs)} open PRs for {owner}/{name}')
    return all_prs


def _graphql_pr_mergeability(owner, name):
    '''Fetch mergeability status for all open PRs via GraphQL.

    Returns a list of dicts with keys: number, title, author, url,
    head_ref, base_ref, draft, mergeable.
    '''
    query = '''
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 100, states: OPEN, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number title isDraft url
            headRefName baseRefName
            author { login }
            mergeable
          }
        }
      }
    }
    '''
    session = _get_graphql_session()
    results = []
    cursor = None
    while True:
        resp = session.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {
                'owner': owner, 'name': name, 'cursor': cursor,
            }},
        )
        body = resp.json()
        if 'errors' in body:
            raise GitHubPRError(f'GraphQL error: {body["errors"]}')

        pr_data = body['data']['repository']['pullRequests']
        for node in pr_data['nodes']:
            results.append({
                'number': node['number'],
                'title': node['title'],
                'author': (node.get('author') or {}).get('login', 'unknown'),
                'url': node['url'],
                'head_ref': node['headRefName'],
                'base_ref': node['baseRefName'],
                'draft': node['isDraft'],
                'mergeable': node.get('mergeable'),
            })

        page_info = pr_data['pageInfo']
        if not page_info['hasNextPage']:
            break
        cursor = page_info['endCursor']

    log.info(f'GraphQL fetched mergeability for {len(results)} open PRs in {owner}/{name}')
    return results


def _graphql_pr_ci_status(owner, name):
    '''Fetch CI check rollup status for all open PRs via GraphQL.

    Returns a list of dicts with keys: number, title, author, url,
    head_ref, base_ref, draft, rollup_state, failed_checks.
    '''
    query = '''
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 100, states: OPEN, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number title isDraft url
            headRefName baseRefName
            author { login }
            commits(last: 1) {
              nodes {
                commit {
                  statusCheckRollup {
                    state
                    contexts(first: 30) {
                      nodes {
                        ... on CheckRun {
                          name
                          conclusion
                          status
                        }
                        ... on StatusContext {
                          context
                          state
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    '''
    session = _get_graphql_session()
    results = []
    cursor = None
    while True:
        resp = session.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {
                'owner': owner, 'name': name, 'cursor': cursor,
            }},
        )
        body = resp.json()
        if 'errors' in body:
            raise GitHubPRError(f'GraphQL error: {body["errors"]}')

        pr_data = body['data']['repository']['pullRequests']
        for node in pr_data['nodes']:
            rollup_state = None
            failed_checks = []

            commits = node.get('commits', {}).get('nodes', [])
            if commits:
                rollup = commits[0].get('commit', {}).get('statusCheckRollup')
                if rollup:
                    rollup_state = rollup.get('state')
                    for ctx in rollup.get('contexts', {}).get('nodes', []):
                        # CheckRun nodes have 'name' and 'conclusion'
                        if 'name' in ctx and ctx.get('conclusion') in ('FAILURE', 'ERROR', 'TIMED_OUT'):
                            failed_checks.append({
                                'name': ctx['name'],
                                'conclusion': ctx['conclusion'],
                            })
                        # StatusContext nodes have 'context' and 'state'
                        elif 'context' in ctx and ctx.get('state') in ('FAILURE', 'ERROR'):
                            failed_checks.append({
                                'name': ctx['context'],
                                'conclusion': ctx['state'],
                            })

            results.append({
                'number': node['number'],
                'title': node['title'],
                'author': (node.get('author') or {}).get('login', 'unknown'),
                'url': node['url'],
                'head_ref': node['headRefName'],
                'base_ref': node['baseRefName'],
                'draft': node['isDraft'],
                'rollup_state': rollup_state,
                'failed_checks': failed_checks,
            })

        page_info = pr_data['pageInfo']
        if not page_info['hasNextPage']:
            break
        cursor = page_info['endCursor']

    log.info(f'GraphQL fetched CI status for {len(results)} open PRs in {owner}/{name}')
    return results


def _graphql_stale_branches(owner, name, stale_cutoff):
    '''Fetch branches with last commit info and open PR association via GraphQL.

    Args:
        owner: Repository owner.
        name: Repository name.
        stale_cutoff: ISO datetime string; branches with last commit before
            this cutoff are candidates for staleness.

    Returns a list of dicts with keys: name, last_commit_date,
    last_commit_author, is_protected, open_pr_count.
    '''
    query = '''
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        refs(refPrefix: "refs/heads/", first: 100, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          totalCount
          nodes {
            name
            target {
              ... on Commit {
                committedDate
                author { name }
              }
            }
            associatedPullRequests(states: OPEN, first: 1) {
              totalCount
            }
          }
        }
        branchProtectionRules(first: 20) {
          nodes {
            pattern
          }
        }
      }
    }
    '''
    session = _get_graphql_session()
    results = []
    protection_patterns = []
    cursor = None
    total_count = 0
    while True:
        resp = session.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {
                'owner': owner, 'name': name, 'cursor': cursor,
            }},
        )
        body = resp.json()
        if 'errors' in body:
            raise GitHubPRError(f'GraphQL error: {body["errors"]}')

        repo_data = body['data']['repository']
        refs_data = repo_data['refs']
        total_count = refs_data.get('totalCount', 0)

        # Collect branch protection patterns (only on first page)
        if not protection_patterns:
            for rule in repo_data.get('branchProtectionRules', {}).get('nodes', []):
                protection_patterns.append(rule.get('pattern', ''))

        for node in refs_data['nodes']:
            target = node.get('target') or {}
            committed_date = target.get('committedDate')
            commit_author = (target.get('author') or {}).get('name', 'unknown')
            open_pr_count = node.get('associatedPullRequests', {}).get('totalCount', 0)

            # Check if branch matches any protection pattern
            is_protected = False
            for pattern in protection_patterns:
                if _branch_matches_protection(node['name'], pattern):
                    is_protected = True
                    break

            results.append({
                'name': node['name'],
                'last_commit_date': committed_date,
                'last_commit_author': commit_author,
                'is_protected': is_protected,
                'open_pr_count': open_pr_count,
            })

        page_info = refs_data['pageInfo']
        if not page_info['hasNextPage']:
            break
        cursor = page_info['endCursor']

    log.info(f'GraphQL fetched {len(results)} branches for {owner}/{name}')
    return results, total_count, protection_patterns


def _branch_matches_protection(branch_name, pattern):
    '''Check if a branch name matches a GitHub branch protection pattern.

    GitHub patterns use fnmatch-style wildcards (e.g. "main", "release-*").
    '''
    import fnmatch
    return fnmatch.fnmatch(branch_name, pattern)


def reset_connection():
    '''
    Clear the cached GitHub connection.

    The next call to get_connection() will create a fresh connection.
    Useful for testing or after credential changes.
    '''
    global _cached_connection, _graphql_session
    _cached_connection = None
    _graphql_session = None


# ****************************************************************************************
# Normalization helpers — convert PyGithub objects to clean dicts
# ****************************************************************************************

def _normalize_repo(repo):
    '''
    Convert a PyGithub Repository object to a clean dict.

    Input:
        repo: PyGithub Repository object.

    Output:
        Dict with repo metadata fields.
    '''
    return {
        'full_name': repo.full_name,
        'name': repo.name,
        'description': repo.description or '',
        'default_branch': repo.default_branch,
        'visibility': 'private' if repo.private else 'public',
        'archived': repo.archived,
        'fork': repo.fork,
        'open_issues_count': repo.open_issues_count,
        'stargazers_count': repo.stargazers_count,
        'language': repo.language or '',
        'html_url': repo.html_url,
        'created_at': repo.created_at.isoformat() if repo.created_at else None,
        'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
        'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None,
    }


def _normalize_pr(pr, include_reviews=False):
    '''
    Convert a PyGithub PullRequest object to a clean dict.

    Includes all metadata fields needed for hygiene analysis:
    number, title, author, state, timestamps, branches, draft status,
    mergeable state, reviewers, labels, and optionally review summary.

    Input:
        pr: PyGithub PullRequest object.
        include_reviews: If True, fetch review count and approval status
            via an extra API call per PR.  Default False to avoid N+1
            queries when listing many PRs.

    Output:
        Dict with PR metadata fields.
    '''
    # Collect requested reviewers (users) — available without extra API call
    try:
        requested_reviewers = [u.login for u in pr.requested_reviewers]
    except Exception:
        requested_reviewers = []

    # Collect requested teams — available without extra API call
    try:
        requested_teams = [t.slug for t in pr.requested_teams]
    except Exception:
        requested_teams = []

    # Collect labels — available without extra API call
    try:
        labels = [l.name for l in pr.labels]
    except Exception:
        labels = []

    # Only fetch reviews when explicitly requested (costs 1 API call per PR)
    review_count = 0
    approved = False
    if include_reviews:
        try:
            reviews = pr.get_reviews()
            review_count = reviews.totalCount
            for review in reviews:
                if review.state == 'APPROVED':
                    approved = True
                    break
        except Exception:
            pass

    # pr.mergeable triggers a lazy GET /pulls/{n} per PR in PyGithub when
    # accessed on list-fetched objects.  Only fetch it in detail context
    # (include_reviews=True) to avoid N+1 API calls when listing.
    mergeable = None
    if include_reviews:
        try:
            mergeable = pr.mergeable
        except Exception:
            mergeable = None

    return {
        'number': pr.number,
        'title': pr.title,
        'author': pr.user.login if pr.user else 'unknown',
        'state': pr.state,
        'created_at': pr.created_at.isoformat() if pr.created_at else None,
        'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
        'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
        'closed_at': pr.closed_at.isoformat() if pr.closed_at else None,
        'head_branch': pr.head.ref if pr.head else 'unknown',
        'base_branch': pr.base.ref if pr.base else 'unknown',
        'draft': pr.draft,
        'mergeable': mergeable,
        'html_url': pr.html_url,
        'requested_reviewers': requested_reviewers,
        'requested_teams': requested_teams,
        'labels': labels,
        'review_count': review_count,
        'approved': approved,
    }


def _normalize_review(review):
    '''
    Convert a PyGithub PullRequestReview object to a clean dict.

    Input:
        review: PyGithub PullRequestReview object.

    Output:
        Dict with review metadata fields.
    '''
    return {
        'id': review.id,
        'user': review.user.login if review.user else 'unknown',
        'state': review.state,
        'body': review.body or '',
        'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None,
        'html_url': review.html_url,
    }


# ****************************************************************************************
# Repository operations
# ****************************************************************************************

def list_repos(org):
    '''
    List repositories in a GitHub organization.

    Input:
        org: GitHub organization name (e.g. 'cornelisnetworks').

    Output:
        List of dicts, each containing repo metadata.

    Raises:
        GitHubRepoError: If the organization cannot be found or accessed.
    '''
    log.debug(f'Entering list_repos(org={org})')
    gh = get_connection()

    try:
        organization = gh.get_organization(org)
        repos = []
        for repo in organization.get_repos():
            repos.append(_normalize_repo(repo))
        log.info(f'Found {len(repos)} repos in org {org}')
        return repos
    except UnknownObjectException:
        raise GitHubRepoError(f'Organization not found: {org}')
    except GithubException as e:
        raise GitHubRepoError(f'Failed to list repos for org {org}: {e}')


def get_repo_info(repo_name):
    '''
    Get metadata for a specific repository.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').

    Output:
        Dict containing repo metadata.

    Raises:
        GitHubRepoError: If the repository cannot be found or accessed.
    '''
    log.debug(f'Entering get_repo_info(repo_name={repo_name})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        result = _normalize_repo(repo)
        log.info(f'Retrieved info for repo {repo_name}')
        return result
    except UnknownObjectException:
        raise GitHubRepoError(f'Repository not found: {repo_name}')
    except GithubException as e:
        raise GitHubRepoError(f'Failed to get repo info for {repo_name}: {e}')


def validate_repo(repo_name):
    '''
    Check if a repository exists and is accessible.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').

    Output:
        True if the repository exists and is accessible, False otherwise.
    '''
    log.debug(f'Entering validate_repo(repo_name={repo_name})')
    try:
        get_repo_info(repo_name)
        return True
    except (GitHubRepoError, GitHubConnectionError):
        return False


# ****************************************************************************************
# Pull Request operations
# ****************************************************************************************

def list_pull_requests(repo_name, state='open', sort='created', direction='desc', limit=100):
    '''
    List pull requests for a repository with full metadata.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        state: PR state filter — 'open', 'closed', or 'all' (default: 'open').
        sort: Sort field — 'created', 'updated', or 'popularity' (default: 'created').
        direction: Sort direction — 'asc' or 'desc' (default: 'desc').
        limit: Maximum number of PRs to return (default: 100).

    Output:
        List of dicts, each containing PR metadata from _normalize_pr().

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR listing fails.
    '''
    log.debug(f'Entering list_pull_requests(repo_name={repo_name}, state={state}, '
              f'sort={sort}, direction={direction}, limit={limit})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        pulls = repo.get_pulls(state=state, sort=sort, direction=direction)

        results = []
        count = 0
        for pr in pulls:
            if count >= limit:
                break
            results.append(_normalize_pr(pr))
            count += 1

        log.info(f'Found {len(results)} PRs for {repo_name} (state={state})')
        return results
    except UnknownObjectException:
        raise GitHubRepoError(f'Repository not found: {repo_name}')
    except GithubException as e:
        raise GitHubPRError(f'Failed to list PRs for {repo_name}: {e}')


def get_pull_request(repo_name, pr_number):
    '''
    Get a single pull request with full detail.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: PR number (integer).

    Output:
        Dict containing PR metadata from _normalize_pr().

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If the PR cannot be found or accessed.
    '''
    log.debug(f'Entering get_pull_request(repo_name={repo_name}, pr_number={pr_number})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        result = _normalize_pr(pr, include_reviews=True)
        log.info(f'Retrieved PR #{pr_number} for {repo_name}')
        return result
    except UnknownObjectException:
        raise GitHubPRError(f'PR #{pr_number} not found in {repo_name}')
    except GithubException as e:
        raise GitHubPRError(f'Failed to get PR #{pr_number} for {repo_name}: {e}')


def get_pr_reviews(repo_name, pr_number):
    '''
    Get reviews for a specific pull request.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: PR number (integer).

    Output:
        List of dicts, each containing review metadata from _normalize_review().

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If the PR or its reviews cannot be accessed.
    '''
    log.debug(f'Entering get_pr_reviews(repo_name={repo_name}, pr_number={pr_number})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        reviews = pr.get_reviews()

        results = []
        for review in reviews:
            results.append(_normalize_review(review))

        log.info(f'Found {len(results)} reviews for PR #{pr_number} in {repo_name}')
        return results
    except UnknownObjectException:
        raise GitHubPRError(f'PR #{pr_number} not found in {repo_name}')
    except GithubException as e:
        raise GitHubPRError(f'Failed to get reviews for PR #{pr_number} in {repo_name}: {e}')


def get_pr_review_requests(repo_name, pr_number):
    '''
    Get pending review requests for a specific pull request.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: PR number (integer).

    Output:
        Dict with 'users' (list of login strings) and 'teams' (list of slug strings).

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If the PR or its review requests cannot be accessed.
    '''
    log.debug(f'Entering get_pr_review_requests(repo_name={repo_name}, pr_number={pr_number})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        users = [u.login for u in pr.requested_reviewers]
        teams = [t.slug for t in pr.requested_teams]

        log.info(f'Found {len(users)} user and {len(teams)} team review requests '
                 f'for PR #{pr_number} in {repo_name}')
        return {'users': users, 'teams': teams}
    except UnknownObjectException:
        raise GitHubPRError(f'PR #{pr_number} not found in {repo_name}')
    except GithubException as e:
        raise GitHubPRError(f'Failed to get review requests for PR #{pr_number} in {repo_name}: {e}')


# ****************************************************************************************
# Documentation search — find and retrieve docs from GitHub repos
# ****************************************************************************************

def get_repo_readme(repo_name):
    '''
    Fetch the README content for a repository.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').

    Output:
        Dict with: repo, filename, content (markdown text), size, sha, url.
        If no README exists, returns dict with repo and error key.

    Raises:
        GitHubRepoError: If the repository cannot be found.
    '''
    log.debug(f'Entering get_repo_readme(repo_name={repo_name})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
        readme = repo.get_readme()
        content = readme.decoded_content.decode('utf-8')
        result = {
            'repo': repo_name,
            'filename': readme.name,
            'content': content,
            'size': readme.size,
            'sha': readme.sha,
            'url': readme.html_url,
        }
        log.info(f'Retrieved README ({readme.name}) for {repo_name}')
        return result
    except UnknownObjectException:
        raise GitHubRepoError(f'Repository not found: {repo_name}')
    except GithubException as e:
        # No README found is a common case — return gracefully
        log.warning(f'No README found for {repo_name}: {e}')
        return {'repo': repo_name, 'error': 'No README found'}


def list_repo_docs(repo_name, path='docs', extensions=None, ref=None):
    '''
    List documentation files in a repository directory.

    Default: lists all .md, .rst, .txt files under the given path.
    Recurses into subdirectories.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        path: Directory path to search (default: 'docs').
        extensions: List of file extensions to include
            (default: ['.md', '.rst', '.txt']).
        ref: Git ref (branch, tag, or commit SHA) to list from.
            Default: repository default branch.

    Output:
        List of dicts, each containing: path, name, size, sha, url, type.
        Sorted alphabetically by path.

    Raises:
        GitHubRepoError: If the repository cannot be found.
    '''
    log.debug(f'Entering list_repo_docs(repo_name={repo_name}, path={path}, ref={ref})')
    gh = get_connection()

    if extensions is None:
        extensions = ['.md', '.rst', '.txt']

    try:
        repo = gh.get_repo(repo_name)
    except UnknownObjectException:
        raise GitHubRepoError(f'Repository not found: {repo_name}')

    docs = []

    def _recurse(dir_path):
        '''Recursively collect documentation files from a directory.'''
        try:
            # Pass ref so we list files on the correct branch / commit
            contents = repo.get_contents(dir_path, ref=ref) if ref else repo.get_contents(dir_path)
        except GithubException:
            # Path doesn't exist — return gracefully
            return
        if not isinstance(contents, list):
            contents = [contents]
        for item in contents:
            if item.type == 'dir':
                _recurse(item.path)
            elif item.type == 'file':
                # Check if file extension matches
                _, ext = os.path.splitext(item.name)
                if ext.lower() in extensions:
                    docs.append({
                        'path': item.path,
                        'name': item.name,
                        'size': item.size,
                        'sha': item.sha,
                        'url': item.html_url,
                        'type': 'file',
                    })

    _recurse(path)
    docs.sort(key=lambda d: d['path'])

    log.info(f'Found {len(docs)} doc files in {repo_name}/{path}')
    return docs


def search_repo_docs(repo_name, query, extensions=None):
    '''
    Search for documentation files in a repo matching a query string.

    Uses the GitHub code search API scoped to the repository.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        query: Search query string to match in file contents.
        extensions: List of file extensions to search
            (default: ['.md', '.rst', '.txt']).

    Output:
        List of dicts (max 20), each containing: path, name, repo, url,
        score, text_matches.

    Raises:
        GitHubRepoError: If the repository cannot be found.
    '''
    log.debug(f'Entering search_repo_docs(repo_name={repo_name}, query={query!r})')
    gh = get_connection()

    if extensions is None:
        extensions = ['.md', '.rst', '.txt']

    # Build search query with repo scope and extension filters
    ext_parts = ' '.join(f'extension:{ext.lstrip(".")}' for ext in extensions)
    query_string = f'{query} repo:{repo_name} {ext_parts}'

    try:
        results = gh.search_code(query_string)
        docs = []
        count = 0
        for item in results:
            if count >= 20:
                break
            text_matches = []
            if hasattr(item, 'text_matches') and item.text_matches:
                text_matches = [m.get('fragment', '') if isinstance(m, dict)
                                else getattr(m, 'fragment', '')
                                for m in item.text_matches]
            docs.append({
                'path': item.path,
                'name': item.name,
                'repo': item.repository.full_name,
                'url': item.html_url,
                'score': getattr(item, 'score', None),
                'text_matches': text_matches,
            })
            count += 1

        log.info(f'Search found {len(docs)} doc matches for "{query}" in {repo_name}')
        return docs
    except RateLimitExceededException:
        log.warning(f'Rate limit exceeded during doc search in {repo_name}')
        return []
    except GithubException as e:
        log.warning(f'Doc search failed for {repo_name}: {e}')
        return []


# ****************************************************************************************
# Hygiene analysis — Drucker will call these directly
# ****************************************************************************************

def analyze_pr_staleness(repo_name, stale_days=5, _prefetched_prs=None):
    '''
    Find pull requests older than N days with no activity.

    A PR is considered stale if its updated_at timestamp is older than
    the configured threshold. Draft PRs use a 2x multiplier on the
    threshold before being flagged.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without update to consider stale (default: 5).
        _prefetched_prs: Optional pre-fetched PR list to avoid redundant API calls.

    Output:
        List of dicts, each containing:
            - pr: The normalized PR dict
            - days_stale: Number of days since last update
            - severity: 'high' if >10 days, 'medium' otherwise

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR listing fails.
    '''
    log.debug(f'Entering analyze_pr_staleness(repo_name={repo_name}, stale_days={stale_days})')
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=stale_days)
    draft_threshold = now - timedelta(days=stale_days * 2)

    prs = _prefetched_prs if _prefetched_prs is not None else list_pull_requests(
        repo_name, state='open', sort='updated', direction='asc')

    stale_prs = []
    for pr in prs:
        updated_str = pr.get('updated_at')
        if not updated_str:
            continue

        try:
            updated_at = datetime.fromisoformat(updated_str)
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        effective_threshold = draft_threshold if pr.get('draft', False) else threshold

        if updated_at < effective_threshold:
            days_stale = (now - updated_at).days
            severity = 'high' if days_stale > 10 else 'medium'
            stale_prs.append({
                'pr': pr,
                'days_stale': days_stale,
                'severity': severity,
            })

    log.info(f'Found {len(stale_prs)} stale PRs in {repo_name} '
             f'(threshold: {stale_days} days)')
    return stale_prs


def analyze_missing_reviews(repo_name, _prefetched_prs=None):
    '''
    Find pull requests with zero reviews or pending review requests.

    A PR is flagged if it has:
    - No completed reviews AND no requested reviewers, OR
    - Requested reviewers but no completed reviews (pending requests)

    Draft PRs are excluded from this analysis.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        _prefetched_prs: Optional pre-fetched PR list to avoid redundant API calls.

    Output:
        List of dicts, each containing:
            - pr: The normalized PR dict
            - reason: 'no_reviewers' or 'pending_reviews'
            - severity: 'medium'

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR listing fails.
    '''
    log.debug(f'Entering analyze_missing_reviews(repo_name={repo_name})')

    prs = _prefetched_prs if _prefetched_prs is not None else list_pull_requests(
        repo_name, state='open', sort='created', direction='desc')

    _gh_repo = None

    def _get_repo():
        nonlocal _gh_repo
        if _gh_repo is None:
            gh = get_connection()
            _gh_repo = gh.get_repo(repo_name)
        return _gh_repo

    findings = []
    for pr in prs:
        if pr.get('draft', False):
            continue

        requested_reviewers = pr.get('requested_reviewers', [])
        requested_teams = pr.get('requested_teams', [])

        if not requested_reviewers and not requested_teams:
            findings.append({
                'pr': pr,
                'reason': 'no_reviewers',
                'severity': 'medium',
            })
        elif pr.get('approved'):
            continue
        else:
            if pr.get('review_count', 0) > 0 and not pr.get('approved'):
                findings.append({
                    'pr': pr,
                    'reason': 'pending_reviews',
                    'severity': 'medium',
                })
            else:
                try:
                    pr_obj = _get_repo().get_pull(pr['number'])
                    review_list = list(pr_obj.get_reviews())
                    reviews = [_normalize_review(r) for r in review_list]
                except Exception:
                    reviews = []
                approved = any(r.get('state') == 'APPROVED' for r in reviews)
                pr['review_count'] = len(reviews)
                pr['approved'] = approved
                if not approved:
                    findings.append({
                        'pr': pr,
                        'reason': 'pending_reviews',
                        'severity': 'medium',
                    })

    log.info(f'Found {len(findings)} PRs with missing/pending reviews in {repo_name}')
    return findings


def analyze_repo_pr_hygiene(repo_name, stale_days=5):
    '''
    Combined PR hygiene report for a single repository.

    Runs all hygiene checks (staleness, missing reviews) and returns
    a consolidated report dict suitable for Drucker consumption.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without update to consider stale (default: 5).

    Output:
        Dict containing:
            - repo: Repository name
            - scan_time: ISO timestamp of scan
            - stale_prs: List from analyze_pr_staleness()
            - missing_reviews: List from analyze_missing_reviews()
            - total_open_prs: Count of open PRs scanned
            - total_findings: Total number of findings across all checks
            - summary: Human-readable summary string

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR operations fail.
    '''
    log.debug(f'Entering analyze_repo_pr_hygiene(repo_name={repo_name}, stale_days={stale_days})')
    scan_time = datetime.now(timezone.utc).isoformat()

    parts = repo_name.split('/', 1)
    if len(parts) == 2:
        try:
            open_prs = _graphql_list_open_prs(parts[0], parts[1])
        except Exception as e:
            log.warning(f'GraphQL fetch failed, falling back to REST: {e}')
            open_prs = list_pull_requests(repo_name, state='open', limit=500)
    else:
        open_prs = list_pull_requests(repo_name, state='open', limit=500)

    total_open = len(open_prs)

    stale_findings = analyze_pr_staleness(repo_name, stale_days=stale_days, _prefetched_prs=open_prs)
    review_findings = analyze_missing_reviews(repo_name, _prefetched_prs=open_prs)

    total_findings = len(stale_findings) + len(review_findings)

    # Build human-readable summary
    parts = []
    if stale_findings:
        parts.append(f'{len(stale_findings)} stale PR(s)')
    if review_findings:
        parts.append(f'{len(review_findings)} PR(s) with missing/pending reviews')
    if not parts:
        summary = f'{repo_name}: {total_open} open PRs, no hygiene issues found'
    else:
        summary = f'{repo_name}: {total_findings} findings across {total_open} open PRs — ' + ', '.join(parts)

    report = {
        'repo': repo_name,
        'scan_time': scan_time,
        'stale_prs': stale_findings,
        'missing_reviews': review_findings,
        'total_open_prs': total_open,
        'total_findings': total_findings,
        'summary': summary,
    }

    log.info(f'Hygiene scan complete for {repo_name}: {summary}')
    return report


# ****************************************************************************************
# Extended Hygiene — Phase 5 scans
# ****************************************************************************************

def analyze_naming_compliance(repo_name, ticket_patterns=None, _prefetched_prs=None):
    '''
    Check branch names and PR titles against Jira ticket naming convention.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        ticket_patterns: List of regex pattern strings to match ticket references.
            Default: [r'(?i)(STL|STLSW)-\\d+']
        _prefetched_prs: Optional pre-fetched PR list to avoid redundant API calls.

    Output:
        Dict with pr_findings, branch_findings, summary, and total_findings.

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR listing fails.
    '''
    log.debug(f'Entering analyze_naming_compliance(repo_name={repo_name})')

    if ticket_patterns is None:
        ticket_patterns = [r'(?i)(STL|STLSW)-\d+']

    compiled_patterns = [re.compile(p) for p in ticket_patterns]
    no_jira_re = re.compile(r'(?i)\[NO-JIRA\]')

    if _prefetched_prs is not None:
        prs = _prefetched_prs
    else:
        prs = list_pull_requests(repo_name, state='open')

    pr_findings = []
    branch_findings = []
    title_compliant_count = 0
    title_noncompliant_count = 0
    no_jira_count = 0
    branch_compliant_count = 0
    branch_noncompliant_count = 0

    for pr in prs:
        title = pr.get('title', '')
        head_ref = pr.get('head_branch', '') or pr.get('head_ref', '')
        base_ref = pr.get('base_branch', '') or pr.get('base_ref', '')
        author = pr.get('author', 'unknown')
        number = pr.get('number', 0)

        title_matches = any(p.search(title) for p in compiled_patterns)
        has_no_jira = bool(no_jira_re.search(title))
        title_ok = title_matches or has_no_jira
        branch_ok = any(p.search(head_ref) for p in compiled_patterns)

        if title_ok:
            title_compliant_count += 1
        else:
            title_noncompliant_count += 1

        if has_no_jira:
            no_jira_count += 1

        if branch_ok:
            branch_compliant_count += 1
        else:
            branch_noncompliant_count += 1

        # Severity: high if targeting main or release-* branches
        targets_protected = base_ref in ('main', 'master') or base_ref.startswith('release-')
        if not title_ok:
            severity = 'high' if targets_protected else 'medium'
        else:
            severity = 'low'

        if not title_ok:
            pr_findings.append({
                'pr': {
                    'number': number,
                    'title': title,
                    'author': author,
                    'url': pr.get('html_url', '') or pr.get('url', ''),
                    'head_ref': head_ref,
                    'base_ref': base_ref,
                    'draft': pr.get('draft', False),
                },
                'title_compliant': title_ok,
                'branch_compliant': branch_ok,
                'has_no_jira': has_no_jira,
                'severity': severity,
            })

        if not branch_ok:
            branch_findings.append({
                'branch_name': head_ref,
                'pr_number': number,
                'pr_title': title,
                'author': author,
            })

    total_findings = title_noncompliant_count + branch_noncompliant_count

    result = {
        'repo': repo_name,
        'scan_time': datetime.now(timezone.utc).isoformat(),
        'ticket_patterns': ticket_patterns,
        'pr_findings': pr_findings,
        'branch_findings': branch_findings,
        'summary': {
            'total_prs_scanned': len(prs),
            'title_compliant': title_compliant_count,
            'title_noncompliant': title_noncompliant_count,
            'no_jira_count': no_jira_count,
            'branch_compliant': branch_compliant_count,
            'branch_noncompliant': branch_noncompliant_count,
        },
        'total_findings': total_findings,
    }

    log.info(f'Naming compliance scan for {repo_name}: '
             f'{title_noncompliant_count} title + {branch_noncompliant_count} branch findings')
    return result


def analyze_merge_conflicts(repo_name, _prefetched_prs=None):
    '''
    Find open PRs that have merge conflicts.

    Uses GraphQL to fetch the mergeable field efficiently. Falls back to
    REST if GraphQL fails (N+1 lazy fetches per PR).

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        _prefetched_prs: Optional pre-fetched PR list (REST fallback only).

    Output:
        Dict with conflicts list, total_open_prs, total_conflicts, summary.

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR operations fail.
    '''
    log.debug(f'Entering analyze_merge_conflicts(repo_name={repo_name})')

    conflicts = []
    total_open = 0

    parts = repo_name.split('/', 1)
    graphql_ok = False

    if len(parts) == 2:
        try:
            gql_prs = _graphql_pr_mergeability(parts[0], parts[1])
            graphql_ok = True
            total_open = len(gql_prs)
            for pr in gql_prs:
                if pr.get('mergeable') == 'CONFLICTING':
                    conflicts.append({
                        'pr': {
                            'number': pr['number'],
                            'title': pr['title'],
                            'author': pr['author'],
                            'url': pr['url'],
                            'head_ref': pr['head_ref'],
                            'base_ref': pr['base_ref'],
                            'draft': pr['draft'],
                        },
                        'mergeable_state': 'CONFLICTING',
                        'severity': 'high',
                    })
        except Exception as e:
            log.warning(f'GraphQL mergeability fetch failed, falling back to REST: {e}')

    if not graphql_ok:
        prs = _prefetched_prs if _prefetched_prs is not None else list_pull_requests(
            repo_name, state='open')
        total_open = len(prs)
        gh = get_connection()
        repo_obj = gh.get_repo(repo_name)
        for pr in prs:
            try:
                pr_obj = repo_obj.get_pull(pr['number'])
                if pr_obj.mergeable is False:
                    conflicts.append({
                        'pr': {
                            'number': pr['number'],
                            'title': pr.get('title', ''),
                            'author': pr.get('author', 'unknown'),
                            'url': pr.get('html_url', ''),
                            'head_ref': pr.get('head_branch', '') or pr.get('head_ref', ''),
                            'base_ref': pr.get('base_branch', '') or pr.get('base_ref', ''),
                            'draft': pr.get('draft', False),
                        },
                        'mergeable_state': 'dirty',
                        'severity': 'high',
                    })
            except Exception as e:
                log.warning(f'Could not check mergeability for PR #{pr["number"]}: {e}')

    total_conflicts = len(conflicts)
    summary = f'{total_conflicts} of {total_open} open PRs have merge conflicts'

    result = {
        'repo': repo_name,
        'scan_time': datetime.now(timezone.utc).isoformat(),
        'conflicts': conflicts,
        'total_open_prs': total_open,
        'total_conflicts': total_conflicts,
        'summary': summary,
    }

    log.info(f'Merge conflict scan for {repo_name}: {summary}')
    return result


def analyze_ci_failures(repo_name, _prefetched_prs=None):
    '''
    Find open PRs with failing CI checks on their HEAD commit.

    Uses GraphQL to fetch statusCheckRollup efficiently. Falls back to
    REST commit status checks if GraphQL fails.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        _prefetched_prs: Optional pre-fetched PR list (REST fallback only).

    Output:
        Dict with failures list, total_open_prs, total_failures, summary.

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If PR operations fail.
    '''
    log.debug(f'Entering analyze_ci_failures(repo_name={repo_name})')

    failures = []
    total_open = 0

    parts = repo_name.split('/', 1)
    graphql_ok = False

    if len(parts) == 2:
        try:
            gql_prs = _graphql_pr_ci_status(parts[0], parts[1])
            graphql_ok = True
            total_open = len(gql_prs)
            for pr in gql_prs:
                rollup = pr.get('rollup_state')
                if rollup in ('FAILURE', 'ERROR'):
                    failures.append({
                        'pr': {
                            'number': pr['number'],
                            'title': pr['title'],
                            'author': pr['author'],
                            'url': pr['url'],
                            'head_ref': pr['head_ref'],
                            'base_ref': pr['base_ref'],
                            'draft': pr['draft'],
                        },
                        'rollup_state': rollup,
                        'failed_checks': pr.get('failed_checks', []),
                        'severity': 'high' if not pr.get('draft') else 'medium',
                    })
        except Exception as e:
            log.warning(f'GraphQL CI status fetch failed, falling back to REST: {e}')

    if not graphql_ok:
        prs = _prefetched_prs if _prefetched_prs is not None else list_pull_requests(
            repo_name, state='open')
        total_open = len(prs)
        gh = get_connection()
        repo_obj = gh.get_repo(repo_name)
        for pr in prs:
            try:
                pr_obj = repo_obj.get_pull(pr['number'])
                head_sha = pr_obj.head.sha
                commit = repo_obj.get_commit(head_sha)
                failed_checks = []

                for check in commit.get_check_runs():
                    if check.conclusion in ('failure', 'timed_out'):
                        failed_checks.append({
                            'name': check.name,
                            'conclusion': check.conclusion.upper(),
                        })

                for status in commit.get_statuses():
                    if status.state in ('failure', 'error'):
                        failed_checks.append({
                            'name': status.context,
                            'conclusion': status.state.upper(),
                        })

                if failed_checks:
                    failures.append({
                        'pr': {
                            'number': pr['number'],
                            'title': pr.get('title', ''),
                            'author': pr.get('author', 'unknown'),
                            'url': pr.get('html_url', ''),
                            'head_ref': pr.get('head_branch', '') or pr.get('head_ref', ''),
                            'base_ref': pr.get('base_branch', '') or pr.get('base_ref', ''),
                            'draft': pr.get('draft', False),
                        },
                        'rollup_state': 'FAILURE',
                        'failed_checks': failed_checks,
                        'severity': 'high' if not pr.get('draft') else 'medium',
                    })
            except Exception as e:
                log.warning(f'Could not check CI status for PR #{pr["number"]}: {e}')

    total_failures = len(failures)
    summary = f'{total_failures} of {total_open} open PRs have failing CI checks'

    result = {
        'repo': repo_name,
        'scan_time': datetime.now(timezone.utc).isoformat(),
        'failures': failures,
        'total_open_prs': total_open,
        'total_failures': total_failures,
        'summary': summary,
    }

    log.info(f'CI failure scan for {repo_name}: {summary}')
    return result


def analyze_stale_branches(repo_name, stale_days=30, exclude_protected=True):
    '''
    Find branches with no recent commits and no associated open PRs.

    Uses GraphQL to fetch branch metadata efficiently.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without commits to consider stale (default: 30).
        exclude_protected: Skip protected branches (default: True).

    Output:
        Dict with stale_branches list, summary, and total_findings.

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If branch operations fail.
    '''
    log.debug(f'Entering analyze_stale_branches(repo_name={repo_name}, '
              f'stale_days={stale_days}, exclude_protected={exclude_protected})')

    now = datetime.now(timezone.utc)
    stale_cutoff = (now - timedelta(days=stale_days)).isoformat()

    parts = repo_name.split('/', 1)
    if len(parts) != 2:
        raise GitHubRepoError(f'Invalid repo name format (expected owner/repo): {repo_name}')

    branches, total_branches, protection_patterns = _graphql_stale_branches(
        parts[0], parts[1], stale_cutoff)

    stale_branches = []
    protected_excluded = 0
    with_open_prs = 0

    for branch in branches:
        if branch.get('open_pr_count', 0) > 0:
            with_open_prs += 1
            continue

        if exclude_protected and branch.get('is_protected', False):
            protected_excluded += 1
            continue

        committed_date_str = branch.get('last_commit_date')
        if not committed_date_str:
            continue

        try:
            committed_date = datetime.fromisoformat(committed_date_str.replace('Z', '+00:00'))
            if committed_date.tzinfo is None:
                committed_date = committed_date.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        days_stale = (now - committed_date).days
        if days_stale < stale_days:
            continue

        if days_stale < 60:
            severity = 'low'
        elif days_stale < 180:
            severity = 'medium'
        else:
            severity = 'high'

        stale_branches.append({
            'name': branch['name'],
            'last_commit_date': committed_date.isoformat(),
            'last_commit_author': branch.get('last_commit_author', 'unknown'),
            'days_stale': days_stale,
            'is_protected': branch.get('is_protected', False),
            'has_open_pr': False,
            'severity': severity,
        })

    stale_branches.sort(key=lambda b: b['days_stale'], reverse=True)

    result = {
        'repo': repo_name,
        'scan_time': datetime.now(timezone.utc).isoformat(),
        'stale_days_threshold': stale_days,
        'stale_branches': stale_branches,
        'summary': {
            'total_branches': total_branches,
            'protected_excluded': protected_excluded,
            'with_open_prs': with_open_prs,
            'stale_count': len(stale_branches),
        },
        'total_findings': len(stale_branches),
    }

    log.info(f'Stale branch scan for {repo_name}: {len(stale_branches)} stale branches found')
    return result


def analyze_extended_hygiene(repo_name, stale_days=5, branch_stale_days=30, ticket_patterns=None):
    '''
    Combined extended hygiene report — runs all 6 scans in one pass.

    Fetches the PR list once and passes it to each PR-based scan.
    Stale branches is independent (fetches branches, not PRs).

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: PR staleness threshold in days (default: 5).
        branch_stale_days: Branch staleness threshold in days (default: 30).
        ticket_patterns: List of regex patterns for naming compliance.

    Output:
        Dict with results from all 6 scans plus combined totals.

    Raises:
        GitHubRepoError: If the repository cannot be found.
        GitHubPRError: If operations fail.
    '''
    log.debug(f'Entering analyze_extended_hygiene(repo_name={repo_name})')
    scan_time = datetime.now(timezone.utc).isoformat()

    parts = repo_name.split('/', 1)
    if len(parts) == 2:
        try:
            open_prs = _graphql_list_open_prs(parts[0], parts[1])
        except Exception as e:
            log.warning(f'GraphQL fetch failed, falling back to REST: {e}')
            open_prs = list_pull_requests(repo_name, state='open', limit=500)
    else:
        open_prs = list_pull_requests(repo_name, state='open', limit=500)

    total_open = len(open_prs)

    stale_findings = analyze_pr_staleness(
        repo_name, stale_days=stale_days, _prefetched_prs=open_prs)
    review_findings = analyze_missing_reviews(
        repo_name, _prefetched_prs=open_prs)
    naming_findings = analyze_naming_compliance(
        repo_name, ticket_patterns=ticket_patterns, _prefetched_prs=open_prs)
    conflict_findings = analyze_merge_conflicts(repo_name)
    ci_findings = analyze_ci_failures(repo_name)

    try:
        branch_findings = analyze_stale_branches(
            repo_name, stale_days=branch_stale_days)
    except Exception as e:
        log.warning(f'Stale branch scan failed: {e}')
        branch_findings = {
            'repo': repo_name,
            'scan_time': scan_time,
            'stale_days_threshold': branch_stale_days,
            'stale_branches': [],
            'summary': {'total_branches': 0, 'protected_excluded': 0,
                        'with_open_prs': 0, 'stale_count': 0},
            'total_findings': 0,
        }

    naming_count = naming_findings['total_findings']
    conflict_count = conflict_findings['total_conflicts']
    ci_count = ci_findings['total_failures']
    branch_count = branch_findings['total_findings']
    total_findings = (
        len(stale_findings)
        + len(review_findings)
        + naming_count
        + conflict_count
        + ci_count
        + branch_count
    )

    summary_parts = []
    if stale_findings:
        summary_parts.append(f'{len(stale_findings)} stale PR(s)')
    if review_findings:
        summary_parts.append(f'{len(review_findings)} PR(s) missing reviews')
    nf = naming_findings.get('total_findings', 0)
    if nf:
        summary_parts.append(f'{nf} naming finding(s)')
    cf = conflict_findings.get('total_conflicts', 0)
    if cf:
        summary_parts.append(f'{cf} merge conflict(s)')
    ci = ci_findings.get('total_failures', 0)
    if ci:
        summary_parts.append(f'{ci} CI failure(s)')
    bf = branch_findings.get('total_findings', 0)
    if bf:
        summary_parts.append(f'{bf} stale branch(es)')

    if not summary_parts:
        summary = f'{repo_name}: {total_open} open PRs, no hygiene issues found'
    else:
        summary = (f'{repo_name}: {total_findings} findings across {total_open} open PRs — '
                   + ', '.join(summary_parts))

    report = {
        'repo': repo_name,
        'scan_time': scan_time,
        'stale_prs': stale_findings,
        'missing_reviews': review_findings,
        'naming_findings': naming_findings,
        'merge_conflicts': conflict_findings,
        'ci_failures': ci_findings,
        'stale_branches': branch_findings,
        'total_open_prs': total_open,
        'total_findings': total_findings,
        'summary': summary,
    }

    log.info(f'Extended hygiene scan complete for {repo_name}: {summary}')
    return report


# ****************************************************************************************
# Write operations
# ****************************************************************************************

# Inline fallback for resolve_dry_run so github_utils.py can run standalone
# without requiring config.env_loader on the import path.
try:
    from config.env_loader import resolve_dry_run as _resolve_dry_run
except ImportError:
    def _resolve_dry_run(explicit=None):
        '''Standalone fallback: explicit param > DRY_RUN env var > True.'''
        if explicit is not None:
            return explicit
        env_val = os.environ.get('DRY_RUN', '').strip().lower()
        if env_val in ('0', 'false', 'no', 'off'):
            return False
        return True


def get_pr_changed_files(repo_name, pr_number):
    '''
    Get the list of files changed in a pull request.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        pr_number: The pull request number.

    Output:
        List of dicts, each containing:
            - filename: Path of the changed file
            - status: One of 'added', 'removed', 'modified', 'renamed'
            - additions: Number of lines added
            - deletions: Number of lines deleted
            - changes: Total number of line changes
            - patch: Unified diff patch (may be None for binary files)
            - sha: Blob SHA of the file

    Raises:
        GitHubRepoError: If the repository is not accessible.
        GitHubPRError: If the PR does not exist or files cannot be fetched.
    '''
    log.debug(f'Entering get_pr_changed_files(repo_name={repo_name}, pr_number={pr_number})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    try:
        pr = repo.get_pull(int(pr_number))
        files = pr.get_files()
        result = []
        for f in files:
            result.append({
                'filename': f.filename,
                'status': f.status,
                'additions': f.additions,
                'deletions': f.deletions,
                'changes': f.changes,
                'patch': f.patch,
                'sha': f.sha,
            })
        log.info(f'PR #{pr_number} in {repo_name}: {len(result)} changed files')
        return result
    except GithubException as e:
        raise GitHubPRError(f'Failed to get changed files for PR #{pr_number} in {repo_name}: {e}')


def get_file_content(repo_name, path, branch='main'):
    '''
    Get the content of a file from a GitHub repository.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        path: File path within the repository.
        branch: Branch name (default: 'main').

    Output:
        Dict containing:
            - path: File path
            - content: Decoded file content as string
            - sha: Blob SHA (needed for updates)
            - size: File size in bytes
            - encoding: Content encoding
        Returns None if the file does not exist.

    Raises:
        GitHubRepoError: If the repository is not accessible.
    '''
    log.debug(f'Entering get_file_content(repo_name={repo_name}, path={path}, branch={branch})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    try:
        contents = repo.get_contents(path, ref=branch)
        # get_contents can return a list for directories; we only handle files
        if isinstance(contents, list):
            log.warning(f'{path} is a directory, not a file')
            return None
        result = {
            'path': contents.path,
            'content': contents.decoded_content.decode('utf-8'),
            'sha': contents.sha,
            'size': contents.size,
            'encoding': contents.encoding,
        }
        log.info(f'Retrieved file {path} from {repo_name}@{branch} ({contents.size} bytes)')
        return result
    except UnknownObjectException:
        log.info(f'File {path} not found in {repo_name}@{branch}')
        return None
    except GithubException as e:
        raise GitHubRepoError(f'Failed to get file {path} from {repo_name}@{branch}: {e}')


def create_or_update_file(repo_name, path, content, message, branch='main', dry_run=None):
    '''
    Create or update a single file in a GitHub repository.

    MUTATION — dry-run by default.  Pass dry_run=False to execute.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        path: File path within the repository.
        content: File content as a string.
        message: Commit message.
        branch: Target branch (default: 'main').
        dry_run: If True (default), preview only — no changes made.

    Output:
        Dict with operation result.  Dry-run returns a preview dict;
        execute returns the commit SHA and operation type.

    Raises:
        GitHubRepoError: If the repository is not accessible or the commit fails.
    '''
    log.debug(f'Entering create_or_update_file(repo_name={repo_name}, path={path}, '
              f'branch={branch}, dry_run={dry_run})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    # Check whether the file already exists to decide create vs update
    existing = get_file_content(repo_name, path, branch=branch)
    operation = 'update' if existing else 'create'

    if _resolve_dry_run(dry_run):
        preview = {
            'dry_run': True,
            'repo': repo_name,
            'path': path,
            'branch': branch,
            'operation': operation,
            'content_length': len(content),
        }
        log.info(f'Dry-run: would {operation} {path} in {repo_name}@{branch}')
        return preview

    try:
        if existing:
            result = repo.update_file(path, message, content, existing['sha'], branch=branch)
        else:
            result = repo.create_file(path, message, content, branch=branch)

        commit_sha = result['commit'].sha
        log.info(f'{operation.capitalize()}d {path} in {repo_name}@{branch} (commit {commit_sha})')
        return {
            'repo': repo_name,
            'path': path,
            'branch': branch,
            'operation': operation,
            'commit_sha': commit_sha,
            'content_length': len(content),
        }
    except GithubException as e:
        raise GitHubRepoError(f'Failed to {operation} {path} in {repo_name}@{branch}: {e}')


def batch_commit_files(repo_name, files, message, branch='main', dry_run=None):
    '''
    Atomically commit multiple files to a GitHub repository via the Git Tree API.

    MUTATION — dry-run by default.  Pass dry_run=False to execute.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        files: Dict[str, str] mapping path→content, or List of dicts with 'path' and 'content' keys.
        message: Commit message.
        branch: Target branch (default: 'main').
        dry_run: If True (default), preview only — no changes made.

    Output:
        Dict with operation result.  Dry-run returns a preview dict;
        execute returns the commit SHA and per-file operations.

    Raises:
        GitHubRepoError: If the repository is not accessible or the commit fails.
    '''
    # Normalize files: accept Dict[str,str] (path→content) or List[Dict] with path+content keys
    if isinstance(files, dict):
        files = [{'path': p, 'content': c} for p, c in files.items()]

    log.debug(f'Entering batch_commit_files(repo_name={repo_name}, file_count={len(files)}, '
              f'branch={branch}, dry_run={dry_run})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    if _resolve_dry_run(dry_run):
        preview = {
            'dry_run': True,
            'repo': repo_name,
            'branch': branch,
            'file_count': len(files),
            'files': [{'path': f['path'], 'content_length': len(f['content'])} for f in files],
        }
        log.info(f'Dry-run: would batch-commit {len(files)} files to {repo_name}@{branch}')
        return preview

    try:
        # Step 1: Create blobs and tree elements for each file
        elements = []
        for f in files:
            blob = repo.create_git_blob(f['content'], 'utf-8')
            elements.append(InputGitTreeElement(
                path=f['path'], mode='100644', type='blob', sha=blob.sha,
            ))

        # Step 2: Get current HEAD and base tree
        head_sha = repo.get_branch(branch).commit.sha
        base_tree = repo.get_git_tree(sha=head_sha)

        # Step 3: Create new tree, commit, and update ref
        new_tree = repo.create_git_tree(elements, base_tree=base_tree)
        parent = repo.get_git_commit(head_sha)
        commit = repo.create_git_commit(message, new_tree, [parent])
        repo.get_git_ref(f'heads/{branch}').edit(sha=commit.sha)

        log.info(f'Batch-committed {len(files)} files to {repo_name}@{branch} '
                 f'(commit {commit.sha})')
        return {
            'repo': repo_name,
            'branch': branch,
            'commit_sha': commit.sha,
            'file_count': len(files),
            'files': [{'path': f['path'], 'operation': 'committed'} for f in files],
        }
    except GithubException as e:
        raise GitHubRepoError(
            f'Failed to batch-commit {len(files)} files to {repo_name}@{branch}: {e}'
        )


def post_pr_comment(repo_name, pr_number, body, dry_run=None):
    '''
    Post a comment on a GitHub pull request.

    MUTATION — dry-run by default.  Pass dry_run=False to execute.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        pr_number: The pull request number.
        body: Comment body text.
        dry_run: If True (default), preview only — no comment posted.

    Output:
        Dict with operation result.  Dry-run returns a preview dict;
        execute returns the comment ID and URL.

    Raises:
        GitHubRepoError: If the repository is not accessible.
        GitHubPRError: If the PR does not exist or the comment fails.
    '''
    log.debug(f'Entering post_pr_comment(repo_name={repo_name}, pr_number={pr_number}, '
              f'body_length={len(body)}, dry_run={dry_run})')
    gh = get_connection()

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    if _resolve_dry_run(dry_run):
        preview = {
            'dry_run': True,
            'repo': repo_name,
            'pr_number': int(pr_number),
            'body_length': len(body),
            'body_preview': body[:200],
        }
        log.info(f'Dry-run: would post comment on PR #{pr_number} in {repo_name}')
        return preview

    try:
        pr = repo.get_pull(int(pr_number))
        comment = pr.create_issue_comment(body)
        log.info(f'Posted comment {comment.id} on PR #{pr_number} in {repo_name}')
        return {
            'repo': repo_name,
            'pr_number': int(pr_number),
            'comment_id': comment.id,
            'html_url': comment.html_url,
        }
    except GithubException as e:
        raise GitHubPRError(
            f'Failed to post comment on PR #{pr_number} in {repo_name}: {e}'
        )


# ****************************************************************************************
# Commit status
# ****************************************************************************************

def post_commit_status(repo_name, sha, state, context='default', description='',
                       target_url=None, dry_run=None):
    '''
    Set a commit status check on a specific SHA.

    MUTATION — dry-run by default.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        sha: Full commit SHA to set status on.
        state: One of 'pending', 'success', 'failure', 'error'.
        context: Status check name (e.g., 'hemingway/documentation').
        description: Short human-readable description.
        target_url: Optional URL linking to details.
        dry_run: If True (default), preview only.

    Output:
        Dict with status result or dry-run preview.
    '''
    log.debug(f'Entering post_commit_status(repo_name={repo_name}, sha={sha[:8]}, '
              f'state={state}, context={context}, dry_run={dry_run})')
    gh = get_connection()

    valid_states = ('pending', 'success', 'failure', 'error')
    if state not in valid_states:
        raise GitHubPRError(f'Invalid state {state!r}. Must be one of: {valid_states}')

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GitHubRepoError(f'Cannot access repository {repo_name}: {e}')

    if _resolve_dry_run(dry_run):
        return {
            'dry_run': True,
            'repo': repo_name,
            'sha': sha,
            'state': state,
            'context': context,
            'description': description,
        }

    try:
        commit = repo.get_commit(sha)
        kwargs = {
            'state': state,
            'context': context,
            'description': description[:140],
        }
        if target_url:
            kwargs['target_url'] = target_url
        status = commit.create_status(**kwargs)
        log.info(f'Set status {state!r} on {sha[:8]} in {repo_name} (context={context})')
        return {
            'repo': repo_name,
            'sha': sha,
            'state': state,
            'context': context,
            'status_id': status.id,
            'url': status.url,
        }
    except GithubException as e:
        raise GitHubPRError(f'Failed to set commit status on {sha[:8]} in {repo_name}: {e}')


# ****************************************************************************************
# Rate limit
# ****************************************************************************************

def get_rate_limit():
    '''
    Get current GitHub API rate limit status.

    Input:
        None.

    Output:
        Dict containing:
            - limit: Maximum requests per hour
            - remaining: Requests remaining in current window
            - reset: ISO timestamp when the limit resets
            - used: Requests used in current window

    Raises:
        GitHubConnectionError: If connection fails.
    '''
    log.debug('Entering get_rate_limit()')
    gh = get_connection()

    try:
        rate = gh.get_rate_limit()
        core = rate.core
        reset_time = core.reset.replace(tzinfo=timezone.utc).isoformat() if core.reset else None
        result = {
            'limit': core.limit,
            'remaining': core.remaining,
            'reset': reset_time,
            'used': core.limit - core.remaining,
        }
        log.info(f'Rate limit: {core.remaining}/{core.limit} remaining, '
                 f'resets at {reset_time}')
        return result
    except GithubException as e:
        raise GitHubConnectionError(f'Failed to get rate limit: {e}')


def check_rate_limit(minimum=100):
    '''
    Check if we have enough API quota remaining.

    Input:
        minimum: Minimum number of requests required (default: 100).

    Output:
        True if remaining requests >= minimum, False otherwise.
    '''
    log.debug(f'Entering check_rate_limit(minimum={minimum})')
    try:
        rate = get_rate_limit()
        remaining = int(rate.get('remaining', 0) or 0)
        has_quota = remaining >= minimum
        if not has_quota:
            log.warning(f'Rate limit low: {remaining} remaining, need {minimum}')
        return has_quota
    except Exception as e:
        log.warning(f'Could not check rate limit: {e}')
        return False


# ****************************************************************************************
# CLI interface
# ****************************************************************************************

def handle_args():
    '''
    Parse CLI arguments and configure console logging handlers.

    Input:
        None directly; reads flags from sys.argv.

    Output:
        argparse.Namespace containing parsed arguments.

    Side Effects:
        Attaches a stream handler to the module logger with formatting and
        level derived from the parsed arguments.
    '''
    log.debug('Entering handle_args()')

    parser = argparse.ArgumentParser(
        description='GitHub utilities for Cornelis Networks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Credentials Setup:
  Set the following environment variable before running:
    export GITHUB_TOKEN="your_personal_access_token_here"

  Generate a PAT at:
    https://github.com/settings/tokens

Examples:
  %(prog)s --list-repos cornelisnetworks
                                            List repos in an org
  %(prog)s --list-prs cornelisnetworks/opa-psm2
                                            List open PRs for a repo
  %(prog)s --list-prs cornelisnetworks/opa-psm2 --state all --limit 50
                                            List all PRs (open+closed), max 50
  %(prog)s --get-pr cornelisnetworks/opa-psm2 123
                                            Get details for PR #123
  %(prog)s --pr-reviews cornelisnetworks/opa-psm2 123
                                            Get reviews for PR #123
  %(prog)s --stale-prs cornelisnetworks/opa-psm2 --days 7
                                            Find PRs with no update in 7 days
  %(prog)s --missing-reviews cornelisnetworks/opa-psm2
                                            Find PRs missing reviews
  %(prog)s --pr-hygiene cornelisnetworks/opa-psm2 --days 5
                                            Full PR hygiene report
  %(prog)s --rate-limit
                                            Show API rate limit status
''')

    # Environment
    parser.add_argument('--env', type=str, default=None,
                        help='Path to alternate .env file to load')

    # Output control
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress stdout output (log file still written)')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON instead of tables')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose console logging')

    # Repository operations
    parser.add_argument('--list-repos', type=str, metavar='ORG',
                        help='List repositories in a GitHub organization')
    parser.add_argument('--repo-info', type=str, metavar='REPO',
                        help='Get metadata for a specific repository')

    # PR operations
    parser.add_argument('--list-prs', type=str, metavar='REPO',
                        help='List pull requests for a repository')
    parser.add_argument('--get-pr', nargs=2, metavar=('REPO', 'NUMBER'),
                        help='Get details for a specific PR')
    parser.add_argument('--pr-reviews', nargs=2, metavar=('REPO', 'NUMBER'),
                        help='Get reviews for a specific PR')

    # PR filters
    parser.add_argument('--state', type=str, default='open',
                        choices=['open', 'closed', 'all'],
                        help='PR state filter (default: open)')
    parser.add_argument('--limit', type=int, default=100,
                        help='Maximum number of results (default: 100)')

    # Hygiene operations
    parser.add_argument('--stale-prs', type=str, metavar='REPO',
                        help='Find stale PRs in a repository')
    parser.add_argument('--missing-reviews', type=str, metavar='REPO',
                        help='Find PRs with missing reviews')
    parser.add_argument('--pr-hygiene', type=str, metavar='REPO',
                        help='Full PR hygiene report for a repository')
    parser.add_argument('--days', type=int, default=5,
                        help='Staleness threshold in days (default: 5)')

    # Extended hygiene operations
    parser.add_argument('--naming-compliance', type=str, metavar='REPO',
                        help='Check PR title and branch naming compliance')
    parser.add_argument('--merge-conflicts', type=str, metavar='REPO',
                        help='Find open PRs with merge conflicts')
    parser.add_argument('--ci-failures', type=str, metavar='REPO',
                        help='Find open PRs with failing CI checks')
    parser.add_argument('--stale-branches', type=str, metavar='REPO',
                        help='Find stale branches with no recent commits')
    parser.add_argument('--extended-hygiene', type=str, metavar='REPO',
                        help='Full extended hygiene report (all scans)')
    parser.add_argument('--branch-stale-days', type=int, default=30,
                        help='Branch staleness threshold in days (default: 30)')

    # Documentation search
    parser.add_argument('--get-readme', type=str, metavar='REPO',
                        help='Get the README content for a repository')
    parser.add_argument('--list-docs', type=str, metavar='REPO',
                        help='List documentation files in a repository')
    parser.add_argument('--search-docs', nargs=2, metavar=('REPO', 'QUERY'),
                        help='Search documentation files in a repository')
    parser.add_argument('--docs-path', type=str, default='docs',
                        help='Directory path for --list-docs (default: docs)')

    # Write operations
    parser.add_argument('--pr-files', nargs=2, metavar=('REPO', 'NUMBER'),
                        help='List files changed in a pull request')
    parser.add_argument('--get-file', nargs='+', metavar=('REPO', 'PATH'),
                        help='Get file content from a repository (REPO PATH [BRANCH])')
    parser.add_argument('--commit-file', nargs='+', metavar=('REPO', 'PATH'),
                        help='Create or update a file (REPO PATH CONTENT MESSAGE [BRANCH])')
    parser.add_argument('--batch-commit', nargs='+', metavar=('REPO', 'ARG'),
                        help='Batch commit files (REPO MESSAGE PATH:CONTENT [PATH:CONTENT ...] [--branch BRANCH])')
    parser.add_argument('--pr-comment', nargs=3, metavar=('REPO', 'NUMBER', 'BODY'),
                        help='Post a comment on a pull request')
    parser.add_argument('--execute', action='store_true',
                        help='Execute mutation operations (default is dry-run)')

    # Rate limit
    parser.add_argument('--rate-limit', action='store_true',
                        help='Show current API rate limit status')

    args = parser.parse_args()

    # Load alternate .env if specified
    if args.env:
        log.info(f'Loading environment from: {args.env}')
        load_dotenv(args.env, override=True)

    # Configure quiet mode
    global _quiet_mode
    if args.quiet:
        _quiet_mode = True

    # Add console handler for verbose mode
    ch = logging.StreamHandler()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARNING)
    ch_formatter = logging.Formatter('%(levelname)-8s %(message)s')
    ch.setFormatter(ch_formatter)
    log.addHandler(ch)

    log.debug(f'Parsed arguments: {args}')
    return args


def main():
    '''
    Entrypoint that wires together dependencies and launches the CLI.

    Sequence:
        1. Parse command line arguments
        2. Connect to GitHub
        3. Execute requested action(s)

    Output:
        Exit code 0 on success, 1 on failure.
    '''
    args = handle_args()
    log.debug('Entering main()')

    try:
        # --- Repository operations ---

        if args.list_repos:
            repos = list_repos(args.list_repos)
            if args.json:
                output(json.dumps(repos, indent=2))
            else:
                output('')
                output(f'Repositories in {args.list_repos}:')
                output('-' * 100)
                output(f'{"Name":<35} {"Visibility":<12} {"Language":<15} {"Open Issues":<13} {"Description":<40}')
                output('-' * 100)
                for r in repos:
                    name = r.get('full_name', 'N/A')
                    vis = r.get('visibility', 'N/A')
                    lang = r.get('language', 'N/A') or 'N/A'
                    issues = str(r.get('open_issues_count', 0))
                    desc = r.get('description', '') or ''
                    if len(name) > 33:
                        name = name[:33] + '..'
                    if len(lang) > 13:
                        lang = lang[:13] + '..'
                    if len(desc) > 38:
                        desc = desc[:38] + '..'
                    output(f'{name:<35} {vis:<12} {lang:<15} {issues:<13} {desc:<40}')
                output('=' * 100)
                output(f'Total: {len(repos)} repositories')
                output('')

        if args.repo_info:
            info = get_repo_info(args.repo_info)
            if args.json:
                output(json.dumps(info, indent=2))
            else:
                output('')
                output(f'Repository: {info.get("full_name", "N/A")}')
                output('-' * 50)
                for key, val in info.items():
                    output(f'  {key}: {val}')
                output('')

        # --- PR operations ---

        if args.list_prs:
            prs = list_pull_requests(args.list_prs, state=args.state, limit=args.limit)
            if args.json:
                output(json.dumps(prs, indent=2))
            else:
                output('')
                output(f'Pull Requests for {args.list_prs} (state={args.state}):')
                print_pr_table_header()
                for pr in prs:
                    print_pr_row(pr)
                print_pr_table_footer(len(prs))

        if args.get_pr:
            repo, number = args.get_pr[0], int(args.get_pr[1])
            pr = get_pull_request(repo, number)
            if args.json:
                output(json.dumps(pr, indent=2))
            else:
                output('')
                output(f'PR #{pr.get("number")} — {pr.get("title")}')
                output('-' * 70)
                output(f'  Author:      {pr.get("author")}')
                output(f'  State:       {pr.get("state")}')
                output(f'  Draft:       {pr.get("draft")}')
                output(f'  Created:     {pr.get("created_at")}')
                output(f'  Updated:     {pr.get("updated_at")}')
                output(f'  Merged:      {pr.get("merged_at", "N/A")}')
                output(f'  Base:        {pr.get("base_branch")}')
                output(f'  Head:        {pr.get("head_branch")}')
                output(f'  Mergeable:   {pr.get("mergeable")}')
                output(f'  Reviews:     {pr.get("review_count")}')
                output(f'  Approved:    {pr.get("approved")}')
                output(f'  Reviewers:   {", ".join(pr.get("requested_reviewers", [])) or "None"}')
                output(f'  Teams:       {", ".join(pr.get("requested_teams", [])) or "None"}')
                output(f'  Labels:      {", ".join(pr.get("labels", [])) or "None"}')
                output(f'  URL:         {pr.get("html_url")}')
                output('')

        if args.pr_reviews:
            repo, number = args.pr_reviews[0], int(args.pr_reviews[1])
            reviews = get_pr_reviews(repo, number)
            if args.json:
                output(json.dumps(reviews, indent=2))
            else:
                output('')
                output(f'Reviews for PR #{number} in {repo}:')
                output('-' * 100)
                output(f'{"User":<20} {"State":<20} {"Submitted":<25} {"Body":<35}')
                output('-' * 100)
                for r in reviews:
                    user = r.get('user', 'N/A')
                    state = r.get('state', 'N/A')
                    submitted = r.get('submitted_at', 'N/A') or 'N/A'
                    body = r.get('body', '') or ''
                    if len(user) > 18:
                        user = user[:18] + '..'
                    if len(body) > 33:
                        body = body[:33] + '..'
                    output(f'{user:<20} {state:<20} {submitted:<25} {body:<35}')
                output('=' * 100)
                output(f'Total: {len(reviews)} reviews')
                output('')

        # --- Hygiene operations ---

        if args.stale_prs:
            findings = analyze_pr_staleness(args.stale_prs, stale_days=args.days)
            if args.json:
                output(json.dumps(findings, indent=2))
            else:
                output('')
                output(f'Stale PRs in {args.stale_prs} (threshold: {args.days} days):')
                output('-' * 130)
                output(f'{"#":<8} {"Author":<18} {"Days Stale":<12} {"Severity":<10} {"Title":<50} {"URL":<40}')
                output('-' * 130)
                for f in findings:
                    pr = f.get('pr', {})
                    number = str(pr.get('number', 'N/A'))
                    author = pr.get('author', 'N/A')
                    days = str(f.get('days_stale', 0))
                    sev = f.get('severity', 'N/A')
                    title = pr.get('title', 'N/A')
                    url = pr.get('html_url', '')
                    if len(author) > 16:
                        author = author[:16] + '..'
                    if len(title) > 48:
                        title = title[:48] + '..'
                    if len(url) > 38:
                        url = url[:38] + '..'
                    output(f'{number:<8} {author:<18} {days:<12} {sev:<10} {title:<50} {url:<40}')
                output('=' * 130)
                output(f'Total: {len(findings)} stale PRs')
                output('')

        if args.missing_reviews:
            findings = analyze_missing_reviews(args.missing_reviews)
            if args.json:
                output(json.dumps(findings, indent=2))
            else:
                output('')
                output(f'PRs with missing reviews in {args.missing_reviews}:')
                output('-' * 120)
                output(f'{"#":<8} {"Author":<18} {"Reason":<20} {"Severity":<10} {"Title":<50} {"URL":<30}')
                output('-' * 120)
                for f in findings:
                    pr = f.get('pr', {})
                    number = str(pr.get('number', 'N/A'))
                    author = pr.get('author', 'N/A')
                    reason = f.get('reason', 'N/A')
                    sev = f.get('severity', 'N/A')
                    title = pr.get('title', 'N/A')
                    url = pr.get('html_url', '')
                    if len(author) > 16:
                        author = author[:16] + '..'
                    if len(title) > 48:
                        title = title[:48] + '..'
                    if len(url) > 28:
                        url = url[:28] + '..'
                    output(f'{number:<8} {author:<18} {reason:<20} {sev:<10} {title:<50} {url:<30}')
                output('=' * 120)
                output(f'Total: {len(findings)} PRs with missing reviews')
                output('')

        if args.pr_hygiene:
            report = analyze_repo_pr_hygiene(args.pr_hygiene, stale_days=args.days)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'PR Hygiene Report — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output('=' * 80)
                output(report.get('summary', ''))
                output('')

                stale = report.get('stale_prs', [])
                if stale:
                    output(f'Stale PRs ({len(stale)}):')
                    output('-' * 80)
                    for f in stale:
                        pr = f.get('pr', {})
                        output(f'  PR #{pr.get("number")} ({pr.get("author")}): '
                               f'"{pr.get("title")}" — '
                               f'no update in {f.get("days_stale")} days '
                               f'[{f.get("severity")}]')
                    output('')

                missing = report.get('missing_reviews', [])
                if missing:
                    output(f'Missing/Pending Reviews ({len(missing)}):')
                    output('-' * 80)
                    for f in missing:
                        pr = f.get('pr', {})
                        output(f'  PR #{pr.get("number")} ({pr.get("author")}): '
                               f'"{pr.get("title")}" — '
                               f'{f.get("reason")} [{f.get("severity")}]')
                    output('')

                output(f'Total open PRs scanned: {report.get("total_open_prs")}')
                output(f'Total findings: {report.get("total_findings")}')
                output('')

        # --- Extended hygiene operations ---

        if args.naming_compliance:
            report = analyze_naming_compliance(args.naming_compliance)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'Naming Compliance — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output(f'Patterns: {report.get("ticket_patterns")}')
                output('=' * 120)
                s = report.get('summary', {})
                output(f'PRs scanned: {s.get("total_prs_scanned", 0)}  |  '
                       f'Title compliant: {s.get("title_compliant", 0)}  |  '
                       f'Title non-compliant: {s.get("title_noncompliant", 0)}  |  '
                       f'[NO-JIRA]: {s.get("no_jira_count", 0)}')
                output(f'Branch compliant: {s.get("branch_compliant", 0)}  |  '
                       f'Branch non-compliant: {s.get("branch_noncompliant", 0)}')
                output('')
                pf = report.get('pr_findings', [])
                if pf:
                    output(f'Non-compliant PR titles ({len(pf)}):')
                    output('-' * 120)
                    for f in pf:
                        pr = f.get('pr', {})
                        output(f'  PR #{pr.get("number")} ({pr.get("author")}): '
                               f'"{pr.get("title")}" -> {pr.get("base_ref")} '
                               f'[{f.get("severity")}]')
                    output('')
                bf = report.get('branch_findings', [])
                if bf:
                    output(f'Non-compliant branches ({len(bf)}):')
                    output('-' * 120)
                    for f in bf:
                        output(f'  {f.get("branch_name")} (PR #{f.get("pr_number")}, '
                               f'{f.get("author")})')
                    output('')
                output(f'Total findings: {report.get("total_findings")}')
                output('')

        if args.merge_conflicts:
            report = analyze_merge_conflicts(args.merge_conflicts)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'Merge Conflicts — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output('=' * 120)
                output(report.get('summary', ''))
                output('')
                for f in report.get('conflicts', []):
                    pr = f.get('pr', {})
                    output(f'  PR #{pr.get("number")} ({pr.get("author")}): '
                           f'"{pr.get("title")}" — {pr.get("head_ref")} -> {pr.get("base_ref")} '
                           f'[{f.get("mergeable_state")}]')
                if report.get('conflicts'):
                    output('')

        if args.ci_failures:
            report = analyze_ci_failures(args.ci_failures)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'CI Failures — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output('=' * 120)
                output(report.get('summary', ''))
                output('')
                for f in report.get('failures', []):
                    pr = f.get('pr', {})
                    checks = ', '.join(c.get('name', '') for c in f.get('failed_checks', []))
                    output(f'  PR #{pr.get("number")} ({pr.get("author")}): '
                           f'"{pr.get("title")}" — {f.get("rollup_state")} '
                           f'[{f.get("severity")}]')
                    if checks:
                        output(f'    Failed: {checks}')
                if report.get('failures'):
                    output('')

        if args.stale_branches:
            report = analyze_stale_branches(
                args.stale_branches, stale_days=args.branch_stale_days)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'Stale Branches — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output(f'Threshold: {report.get("stale_days_threshold")} days')
                output('=' * 120)
                s = report.get('summary', {})
                output(f'Total branches: {s.get("total_branches", 0)}  |  '
                       f'Protected excluded: {s.get("protected_excluded", 0)}  |  '
                       f'With open PRs: {s.get("with_open_prs", 0)}  |  '
                       f'Stale: {s.get("stale_count", 0)}')
                output('')
                output(f'{"Branch":<40} {"Last Commit":<25} {"Author":<20} {"Days":<8} {"Severity":<10}')
                output('-' * 120)
                for b in report.get('stale_branches', []):
                    name = b.get('name', '')
                    if len(name) > 38:
                        name = name[:38] + '..'
                    lcd = (b.get('last_commit_date', '') or '')[:10]
                    author = b.get('last_commit_author', '')
                    if len(author) > 18:
                        author = author[:18] + '..'
                    output(f'{name:<40} {lcd:<25} {author:<20} '
                           f'{str(b.get("days_stale", 0)):<8} {b.get("severity", ""):<10}')
                output('=' * 120)
                output(f'Total: {report.get("total_findings")} stale branches')
                output('')

        if args.extended_hygiene:
            report = analyze_extended_hygiene(
                args.extended_hygiene, stale_days=args.days,
                branch_stale_days=args.branch_stale_days)
            if args.json:
                output(json.dumps(report, indent=2))
            else:
                output('')
                output(f'Extended Hygiene Report — {report.get("repo")}')
                output(f'Scan time: {report.get("scan_time")}')
                output('=' * 80)
                output(report.get('summary', ''))
                output('')
                output(f'Total open PRs scanned: {report.get("total_open_prs")}')
                output(f'Total findings: {report.get("total_findings")}')
                output('')

        # --- Documentation search ---

        if args.get_readme:
            result = get_repo_readme(args.get_readme)
            if args.json:
                output(json.dumps(result, indent=2))
            else:
                if 'error' in result:
                    output('')
                    output(f'README for {result.get("repo")}: {result.get("error")}')
                    output('')
                else:
                    output('')
                    output(f'README for {result.get("repo")} — {result.get("filename")}')
                    output(f'Size: {result.get("size")} bytes  |  URL: {result.get("url")}')
                    output('=' * 80)
                    output(result.get('content', ''))
                    output('')

        if args.list_docs:
            docs = list_repo_docs(args.list_docs, path=args.docs_path)
            if args.json:
                output(json.dumps(docs, indent=2))
            else:
                output('')
                output(f'Documentation files in {args.list_docs}/{args.docs_path}:')
                output('-' * 100)
                output(f'{"Path":<50} {"Size":<10} {"URL":<40}')
                output('-' * 100)
                for d in docs:
                    path = d.get('path', '')
                    size = str(d.get('size', 0))
                    url = d.get('url', '')
                    if len(path) > 48:
                        path = path[:48] + '..'
                    if len(url) > 38:
                        url = url[:38] + '..'
                    output(f'{path:<50} {size:<10} {url:<40}')
                output('=' * 100)
                output(f'Total: {len(docs)} documentation files')
                output('')

        if args.search_docs:
            repo, query = args.search_docs[0], args.search_docs[1]
            docs = search_repo_docs(repo, query)
            if args.json:
                output(json.dumps(docs, indent=2))
            else:
                output('')
                output(f'Documentation search in {repo} for "{query}":')
                output('-' * 120)
                output(f'{"Path":<50} {"Score":<10} {"URL":<40}')
                output('-' * 120)
                for d in docs:
                    path = d.get('path', '')
                    score = str(d.get('score', ''))
                    url = d.get('url', '')
                    if len(path) > 48:
                        path = path[:48] + '..'
                    if len(url) > 38:
                        url = url[:38] + '..'
                    output(f'{path:<50} {score:<10} {url:<40}')
                output('=' * 120)
                output(f'Total: {len(docs)} matches')
                output('')

        # --- Write operations ---

        if args.pr_files:
            repo, number = args.pr_files[0], int(args.pr_files[1])
            files = get_pr_changed_files(repo, number)
            if args.json:
                output(json.dumps(files, indent=2))
            else:
                output('')
                output(f'Changed files in PR #{number} for {repo}:')
                output('-' * 130)
                output(f'{"Filename":<60} {"Status":<12} {"Additions":<10} {"Deletions":<10} {"Changes":<10}')
                output('-' * 130)
                for f in files:
                    fname = f.get('filename', '')
                    if len(fname) > 58:
                        fname = fname[:58] + '..'
                    output(f'{fname:<60} {f.get("status", ""):<12} '
                           f'{str(f.get("additions", 0)):<10} '
                           f'{str(f.get("deletions", 0)):<10} '
                           f'{str(f.get("changes", 0)):<10}')
                output('=' * 130)
                output(f'Total: {len(files)} changed files')
                output('')

        if args.get_file:
            parts = args.get_file
            if len(parts) < 2:
                output('ERROR: --get-file requires REPO PATH [BRANCH]')
                sys.exit(1)
            repo, path = parts[0], parts[1]
            branch = parts[2] if len(parts) > 2 else 'main'
            result = get_file_content(repo, path, branch=branch)
            if result is None:
                output(f'File {path} not found in {repo}@{branch}')
            elif args.json:
                output(json.dumps(result, indent=2))
            else:
                output('')
                output(f'File: {result.get("path")} ({result.get("size")} bytes)')
                output(f'SHA: {result.get("sha")}')
                output('=' * 80)
                output(result.get('content', ''))

        if args.commit_file:
            parts = args.commit_file
            if len(parts) < 4:
                output('ERROR: --commit-file requires REPO PATH CONTENT MESSAGE [BRANCH]')
                sys.exit(1)
            repo, path, content, message = parts[0], parts[1], parts[2], parts[3]
            branch = parts[4] if len(parts) > 4 else 'main'
            dry = not args.execute
            result = create_or_update_file(repo, path, content, message, branch=branch, dry_run=dry)
            if args.json:
                output(json.dumps(result, indent=2))
            else:
                if result.get('dry_run'):
                    output(f'[DRY-RUN] Would {result.get("operation")} {path} '
                           f'in {repo}@{branch} ({result.get("content_length")} bytes)')
                else:
                    output(f'{result.get("operation").capitalize()}d {path} '
                           f'in {repo}@{branch} (commit {result.get("commit_sha")})')

        if args.batch_commit:
            parts = args.batch_commit
            if len(parts) < 3:
                output('ERROR: --batch-commit requires REPO MESSAGE PATH:CONTENT [PATH:CONTENT ...]')
                sys.exit(1)
            repo, message = parts[0], parts[1]
            file_specs = parts[2:]
            files_list = []
            for spec in file_specs:
                if ':' not in spec:
                    output(f'ERROR: Invalid file spec "{spec}" — expected PATH:CONTENT')
                    sys.exit(1)
                fpath, fcontent = spec.split(':', 1)
                files_list.append({'path': fpath, 'content': fcontent})
            dry = not args.execute
            result = batch_commit_files(repo, files_list, message, dry_run=dry)
            if args.json:
                output(json.dumps(result, indent=2))
            else:
                if result.get('dry_run'):
                    output(f'[DRY-RUN] Would batch-commit {result.get("file_count")} files '
                           f'to {repo}@{result.get("branch")}')
                    for f in result.get('files', []):
                        output(f'  {f.get("path")} ({f.get("content_length")} bytes)')
                else:
                    output(f'Batch-committed {result.get("file_count")} files '
                           f'to {repo}@{result.get("branch")} (commit {result.get("commit_sha")})')

        if args.pr_comment:
            repo, number, body = args.pr_comment[0], int(args.pr_comment[1]), args.pr_comment[2]
            dry = not args.execute
            result = post_pr_comment(repo, number, body, dry_run=dry)
            if args.json:
                output(json.dumps(result, indent=2))
            else:
                if result.get('dry_run'):
                    output(f'[DRY-RUN] Would post comment on PR #{number} in {repo} '
                           f'({result.get("body_length")} chars)')
                else:
                    output(f'Posted comment on PR #{number} in {repo}: {result.get("html_url")}')

        # --- Rate limit ---

        if args.rate_limit:
            rate = get_rate_limit()
            if args.json:
                output(json.dumps(rate, indent=2))
            else:
                output('')
                output('GitHub API Rate Limit:')
                output('-' * 40)
                output(f'  Limit:     {rate.get("limit")}')
                output(f'  Used:      {rate.get("used")}')
                output(f'  Remaining: {rate.get("remaining")}')
                output(f'  Resets at: {rate.get("reset")}')
                output('')

    except GitHubCredentialsError as e:
        log.error(e.message)
        output('')
        output('ERROR: ' + e.message)
        output('')
        output('Please set the required environment variable:')
        output('  export GITHUB_TOKEN="your_personal_access_token_here"')
        output('')
        sys.exit(1)
    except GitHubConnectionError as e:
        log.error(e.message)
        output('')
        output('ERROR: ' + e.message)
        output('')
        sys.exit(1)
    except GitHubRepoError as e:
        log.error(e.message)
        output('')
        output('ERROR: ' + e.message)
        output('')
        sys.exit(1)
    except GitHubPRError as e:
        log.error(e.message)
        output('')
        output('ERROR: ' + e.message)
        output('')
        sys.exit(1)
    except Exception as e:
        log.error(f'Unexpected error: {e}')
        output(f'ERROR: {e}')
        sys.exit(1)

    log.info('Operation complete.')


if __name__ == '__main__':
    main()
