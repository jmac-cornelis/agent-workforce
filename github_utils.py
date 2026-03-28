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
except ImportError:
    print('Error: PyGithub package not installed. Run: pip install PyGithub')
    sys.exit(1)

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


def reset_connection():
    '''
    Clear the cached GitHub connection.

    The next call to get_connection() will create a fresh connection.
    Useful for testing or after credential changes.
    '''
    global _cached_connection
    _cached_connection = None


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


def _normalize_pr(pr):
    '''
    Convert a PyGithub PullRequest object to a clean dict.

    Includes all metadata fields needed for hygiene analysis:
    number, title, author, state, timestamps, branches, draft status,
    mergeable state, reviewers, labels, and review summary.

    Input:
        pr: PyGithub PullRequest object.

    Output:
        Dict with PR metadata fields.
    '''
    # Collect requested reviewers (users)
    try:
        requested_reviewers = [u.login for u in pr.requested_reviewers]
    except Exception:
        requested_reviewers = []

    # Collect requested teams
    try:
        requested_teams = [t.slug for t in pr.requested_teams]
    except Exception:
        requested_teams = []

    # Collect labels
    try:
        labels = [l.name for l in pr.labels]
    except Exception:
        labels = []

    # Count reviews and check for approvals
    review_count = 0
    approved = False
    try:
        reviews = pr.get_reviews()
        review_count = reviews.totalCount
        for review in reviews:
            if review.state == 'APPROVED':
                approved = True
                break
    except Exception:
        pass

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
        'mergeable': pr.mergeable,
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
        result = _normalize_pr(pr)
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
# Hygiene analysis — Drucker will call these directly
# ****************************************************************************************

def analyze_pr_staleness(repo_name, stale_days=5):
    '''
    Find pull requests older than N days with no activity.

    A PR is considered stale if its updated_at timestamp is older than
    the configured threshold. Draft PRs use a 2x multiplier on the
    threshold before being flagged.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without update to consider stale (default: 5).

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

    # Fetch open PRs sorted by oldest update first
    prs = list_pull_requests(repo_name, state='open', sort='updated', direction='asc')

    stale_prs = []
    for pr in prs:
        updated_str = pr.get('updated_at')
        if not updated_str:
            continue

        try:
            updated_at = datetime.fromisoformat(updated_str)
            # Ensure timezone-aware comparison
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        # Draft PRs get a 2x grace period
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


def analyze_missing_reviews(repo_name):
    '''
    Find pull requests with zero reviews or pending review requests.

    A PR is flagged if it has:
    - No completed reviews AND no requested reviewers, OR
    - Requested reviewers but no completed reviews (pending requests)

    Draft PRs are excluded from this analysis.

    Input:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').

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

    prs = list_pull_requests(repo_name, state='open', sort='created', direction='desc')

    findings = []
    for pr in prs:
        # Skip draft PRs — they are not expected to have reviews yet
        if pr.get('draft', False):
            continue

        review_count = pr.get('review_count', 0)
        requested_reviewers = pr.get('requested_reviewers', [])
        requested_teams = pr.get('requested_teams', [])
        approved = pr.get('approved', False)

        if review_count == 0 and not requested_reviewers and not requested_teams:
            # No reviews and no one asked to review
            findings.append({
                'pr': pr,
                'reason': 'no_reviewers',
                'severity': 'medium',
            })
        elif (requested_reviewers or requested_teams) and not approved:
            # Reviews requested but not yet approved
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

    # Run individual analyses
    stale_findings = analyze_pr_staleness(repo_name, stale_days=stale_days)
    review_findings = analyze_missing_reviews(repo_name)

    # Count total open PRs for context
    open_prs = list_pull_requests(repo_name, state='open', limit=500)
    total_open = len(open_prs)

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
