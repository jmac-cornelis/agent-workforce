##########################################################################################
#
# Module: tools/github_tools.py
#
# Description: GitHub tools for agent use.
#              Wraps github_utils.py functionality as agent-callable tools.
#
# Author: Cornelis Networks
#
##########################################################################################

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from tools.base import BaseTool, ToolResult, tool

# Load environment variables
load_dotenv()

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Import from github_utils.py - reuse existing functionality
try:
    import github_utils
    from github_utils import (
        connect_to_github,
        get_connection,
        reset_connection,
        validate_repo,
        list_repos as _list_repos,
        get_repo_info as _get_repo_info,
        list_pull_requests as _list_pull_requests,
        get_pull_request as _get_pull_request,
        get_pr_reviews as _get_pr_reviews,
        get_pr_review_requests as _get_pr_review_requests,
        analyze_pr_staleness as _analyze_pr_staleness,
        analyze_missing_reviews as _analyze_missing_reviews,
        analyze_repo_pr_hygiene as _analyze_repo_pr_hygiene,
        get_rate_limit as _get_rate_limit,
        analyze_naming_compliance as _analyze_naming_compliance,
        analyze_merge_conflicts as _analyze_merge_conflicts,
        analyze_ci_failures as _analyze_ci_failures,
        analyze_stale_branches as _analyze_stale_branches,
        analyze_extended_hygiene as _analyze_extended_hygiene,
        get_repo_readme as _get_repo_readme,
        list_repo_docs as _list_repo_docs,
        search_repo_docs as _search_repo_docs,
    )
    GITHUB_UTILS_AVAILABLE = True
except ImportError as e:
    GITHUB_UTILS_AVAILABLE = False
    log.warning(f'github_utils.py not available: {e}')


def get_github():
    '''Get or create GitHub connection using github_utils.'''
    if not GITHUB_UTILS_AVAILABLE:
        raise RuntimeError('github_utils.py is required but not available')
    return github_utils.get_connection()


# ****************************************************************************************
# Tool Functions
# ****************************************************************************************

@tool(description='List repositories in a GitHub organization')
def list_repos(org: str) -> ToolResult:
    '''
    List repositories in a GitHub organization.

    Input:
        org: The GitHub organization name.

    Output:
        ToolResult with list of repository dicts.
    '''
    log.debug(f'list_repos(org={org})')

    try:
        get_github()
        repos = _list_repos(org)

        return ToolResult.success(repos, count=len(repos), org=org)

    except Exception as e:
        log.error(f'Failed to list repos: {e}')
        return ToolResult.failure(f'Failed to list repos for {org}: {e}')


@tool(description='Get detailed information about a GitHub repository')
def get_repo_info(repo_name: str) -> ToolResult:
    '''
    Get detailed information about a GitHub repository.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with repository information.
    '''
    log.debug(f'get_repo_info(repo_name={repo_name})')

    try:
        get_github()
        info = _get_repo_info(repo_name)

        return ToolResult.success(info)

    except Exception as e:
        log.error(f'Failed to get repo info: {e}')
        return ToolResult.failure(f'Failed to get repo info for {repo_name}: {e}')


@tool(description='Validate that a GitHub repository exists and is accessible')
def validate_repository(repo_name: str) -> ToolResult:
    '''
    Validate that a GitHub repository exists and is accessible.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with validation status.
    '''
    log.debug(f'validate_repository(repo_name={repo_name})')

    try:
        get_github()
        valid = validate_repo(repo_name)

        result = {
            'repo_name': repo_name,
            'valid': valid,
        }

        return ToolResult.success(result)

    except Exception as e:
        log.error(f'Failed to validate repository: {e}')
        return ToolResult.failure(f'Repository {repo_name} is not accessible: {e}')


@tool(description='List pull requests for a GitHub repository')
def list_pull_requests(
    repo_name: str,
    state: str = 'open',
    sort: str = 'created',
    direction: str = 'desc',
    limit: int = 100,
) -> ToolResult:
    '''
    List pull requests for a GitHub repository.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        state: PR state filter: 'open', 'closed', or 'all'.
        sort: Sort field: 'created', 'updated', or 'popularity'.
        direction: Sort direction: 'asc' or 'desc'.
        limit: Maximum number of PRs to return.

    Output:
        ToolResult with list of pull request dicts.
    '''
    log.debug(f'list_pull_requests(repo_name={repo_name}, state={state}, limit={limit})')

    try:
        get_github()
        prs = _list_pull_requests(
            repo_name, state=state, sort=sort,
            direction=direction, limit=limit,
        )

        return ToolResult.success(prs, count=len(prs), repo_name=repo_name, state=state)

    except Exception as e:
        log.error(f'Failed to list pull requests: {e}')
        return ToolResult.failure(f'Failed to list PRs for {repo_name}: {e}')


@tool(description='Get detailed information about a specific pull request')
def get_pull_request(repo_name: str, pr_number: int) -> ToolResult:
    '''
    Get detailed information about a specific pull request.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        pr_number: The pull request number.

    Output:
        ToolResult with pull request details.
    '''
    log.debug(f'get_pull_request(repo_name={repo_name}, pr_number={pr_number})')

    try:
        get_github()
        pr = _get_pull_request(repo_name, pr_number)

        return ToolResult.success(pr)

    except Exception as e:
        log.error(f'Failed to get pull request: {e}')
        return ToolResult.failure(f'Failed to get PR #{pr_number} for {repo_name}: {e}')


@tool(description='Get reviews for a specific pull request')
def get_pr_reviews(repo_name: str, pr_number: int) -> ToolResult:
    '''
    Get reviews for a specific pull request.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        pr_number: The pull request number.

    Output:
        ToolResult with list of review dicts.
    '''
    log.debug(f'get_pr_reviews(repo_name={repo_name}, pr_number={pr_number})')

    try:
        get_github()
        reviews = _get_pr_reviews(repo_name, pr_number)

        return ToolResult.success(reviews, count=len(reviews), pr_number=pr_number)

    except Exception as e:
        log.error(f'Failed to get PR reviews: {e}')
        return ToolResult.failure(f'Failed to get reviews for PR #{pr_number} in {repo_name}: {e}')


@tool(description='Get pending review requests for a specific pull request')
def get_pr_review_requests(repo_name: str, pr_number: int) -> ToolResult:
    '''
    Get pending review requests for a specific pull request.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        pr_number: The pull request number.

    Output:
        ToolResult with list of pending review request dicts.
    '''
    log.debug(f'get_pr_review_requests(repo_name={repo_name}, pr_number={pr_number})')

    try:
        get_github()
        requests = _get_pr_review_requests(repo_name, pr_number)

        return ToolResult.success(requests, count=len(requests), pr_number=pr_number)

    except Exception as e:
        log.error(f'Failed to get PR review requests: {e}')
        return ToolResult.failure(
            f'Failed to get review requests for PR #{pr_number} in {repo_name}: {e}'
        )


@tool(description='Find stale pull requests that have been open longer than the specified number of days')
def find_stale_prs(repo_name: str, stale_days: int = 5) -> ToolResult:
    '''
    Find stale pull requests that have been open longer than the specified number of days.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        stale_days: Number of days after which a PR is considered stale.

    Output:
        ToolResult with list of stale PR dicts.
    '''
    log.debug(f'find_stale_prs(repo_name={repo_name}, stale_days={stale_days})')

    try:
        get_github()
        stale = _analyze_pr_staleness(repo_name, stale_days=stale_days)

        return ToolResult.success(
            stale, count=len(stale), repo_name=repo_name, stale_days=stale_days,
        )

    except Exception as e:
        log.error(f'Failed to find stale PRs: {e}')
        return ToolResult.failure(f'Failed to find stale PRs for {repo_name}: {e}')


@tool(description='Find pull requests that are missing reviews or have pending review requests')
def find_missing_reviews(repo_name: str) -> ToolResult:
    '''
    Find pull requests that are missing reviews or have pending review requests.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with list of PRs missing reviews.
    '''
    log.debug(f'find_missing_reviews(repo_name={repo_name})')

    try:
        get_github()
        missing = _analyze_missing_reviews(repo_name)

        return ToolResult.success(missing, count=len(missing), repo_name=repo_name)

    except Exception as e:
        log.error(f'Failed to find missing reviews: {e}')
        return ToolResult.failure(f'Failed to find missing reviews for {repo_name}: {e}')


@tool(description='Run a comprehensive PR hygiene analysis for a repository')
def analyze_pr_hygiene(repo_name: str, stale_days: int = 5) -> ToolResult:
    '''
    Run a comprehensive PR hygiene analysis for a repository.

    Combines staleness analysis, missing review detection, and overall
    PR health metrics into a single report.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        stale_days: Number of days after which a PR is considered stale.

    Output:
        ToolResult with comprehensive PR hygiene report.
    '''
    log.debug(f'analyze_pr_hygiene(repo_name={repo_name}, stale_days={stale_days})')

    try:
        get_github()
        report = _analyze_repo_pr_hygiene(repo_name, stale_days=stale_days)

        return ToolResult.success(report, repo_name=repo_name, stale_days=stale_days)

    except Exception as e:
        log.error(f'Failed to analyze PR hygiene: {e}')
        return ToolResult.failure(f'Failed to analyze PR hygiene for {repo_name}: {e}')


@tool(description='Get current GitHub API rate limit status')
def get_rate_limit_status() -> ToolResult:
    '''
    Get current GitHub API rate limit status.

    Output:
        ToolResult with rate limit information including remaining calls
        and reset time.
    '''
    log.debug('get_rate_limit_status()')

    try:
        get_github()
        rate_limit = _get_rate_limit()

        return ToolResult.success(rate_limit)

    except Exception as e:
        log.error(f'Failed to get rate limit: {e}')
        return ToolResult.failure(f'Failed to get GitHub rate limit: {e}')


# ****************************************************************************************
# Phase 5 — Extended Hygiene Scan Tools
# ****************************************************************************************

@tool(description='Check branch and PR title naming compliance against Jira ticket conventions')
def check_naming_compliance(repo_name: str, ticket_patterns: str = '') -> ToolResult:
    '''
    Check branch and PR title naming compliance against Jira ticket conventions.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        ticket_patterns: Comma-separated regex patterns for ticket IDs.
                         Default: None (uses built-in STL/STLSW patterns).

    Output:
        ToolResult with naming compliance analysis.
    '''
    log.debug(f'check_naming_compliance(repo_name={repo_name}, ticket_patterns={ticket_patterns!r})')

    try:
        get_github()
        # Parse comma-separated string to list; empty string means use defaults
        patterns = [p.strip() for p in ticket_patterns.split(',') if p.strip()] if ticket_patterns else None
        result = _analyze_naming_compliance(repo_name, ticket_patterns=patterns)

        return ToolResult.success(
            result,
            repo=repo_name,
            total_prs=result.get('total_prs', 0),
            title_compliant=result.get('title_compliant', 0),
            title_noncompliant=result.get('title_noncompliant', 0),
            no_jira_count=result.get('no_jira_count', 0),
            branch_compliant=result.get('branch_compliant', 0),
            branch_noncompliant=result.get('branch_noncompliant', 0),
            total_findings=result.get('total_findings', 0),
        )

    except Exception as e:
        log.error(f'Failed to check naming compliance: {e}')
        return ToolResult.failure(f'Failed to check naming compliance for {repo_name}: {e}')


@tool(description='Find open PRs with merge conflicts')
def check_merge_conflicts(repo_name: str) -> ToolResult:
    '''
    Find open pull requests with merge conflicts.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with merge conflict analysis.
    '''
    log.debug(f'check_merge_conflicts(repo_name={repo_name})')

    try:
        get_github()
        result = _analyze_merge_conflicts(repo_name)

        return ToolResult.success(
            result,
            repo=repo_name,
            total_open_prs=result.get('total_open_prs', 0),
            total_conflicts=result.get('total_conflicts', 0),
        )

    except Exception as e:
        log.error(f'Failed to check merge conflicts: {e}')
        return ToolResult.failure(f'Failed to check merge conflicts for {repo_name}: {e}')


@tool(description='Find open PRs with failing CI checks')
def check_ci_failures(repo_name: str) -> ToolResult:
    '''
    Find open pull requests with failing CI checks.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with CI failure analysis.
    '''
    log.debug(f'check_ci_failures(repo_name={repo_name})')

    try:
        get_github()
        result = _analyze_ci_failures(repo_name)

        return ToolResult.success(
            result,
            repo=repo_name,
            total_open_prs=result.get('total_open_prs', 0),
            total_failures=result.get('total_failures', 0),
        )

    except Exception as e:
        log.error(f'Failed to check CI failures: {e}')
        return ToolResult.failure(f'Failed to check CI failures for {repo_name}: {e}')


@tool(description='Find stale branches with no recent activity and no open PRs')
def check_stale_branches(repo_name: str, stale_days: int = 30) -> ToolResult:
    '''
    Find stale branches with no recent activity and no open PRs.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        stale_days: Number of days without activity to consider a branch stale.

    Output:
        ToolResult with stale branch analysis.
    '''
    log.debug(f'check_stale_branches(repo_name={repo_name}, stale_days={stale_days})')

    try:
        get_github()
        result = _analyze_stale_branches(repo_name, stale_days=stale_days)

        return ToolResult.success(
            result,
            repo=repo_name,
            stale_days=stale_days,
            total_branches=result.get('total_branches', 0),
            stale_count=result.get('stale_count', 0),
        )

    except Exception as e:
        log.error(f'Failed to check stale branches: {e}')
        return ToolResult.failure(f'Failed to check stale branches for {repo_name}: {e}')


@tool(description='Run comprehensive extended hygiene analysis including all scan types')
def analyze_extended_hygiene(repo_name: str, stale_days: int = 5, branch_stale_days: int = 30) -> ToolResult:
    '''
    Run comprehensive extended hygiene analysis including all scan types.

    Combines naming compliance, merge conflicts, CI failures, stale branches,
    and PR staleness into a single comprehensive report.

    Input:
        repo_name: Full repository name (e.g., 'org/repo').
        stale_days: Number of days after which a PR is considered stale.
        branch_stale_days: Number of days after which a branch is considered stale.

    Output:
        ToolResult with comprehensive extended hygiene report.
    '''
    log.debug(f'analyze_extended_hygiene(repo_name={repo_name}, stale_days={stale_days}, branch_stale_days={branch_stale_days})')

    try:
        get_github()
        result = _analyze_extended_hygiene(
            repo_name, stale_days=stale_days, branch_stale_days=branch_stale_days,
        )

        return ToolResult.success(
            result,
            repo=repo_name,
            total_open_prs=result.get('total_open_prs', 0),
            total_findings=result.get('total_findings', 0),
        )

    except Exception as e:
        log.error(f'Failed to analyze extended hygiene: {e}')
        return ToolResult.failure(f'Failed to analyze extended hygiene for {repo_name}: {e}')


# ****************************************************************************************
# Documentation Search Tools
# ****************************************************************************************

@tool(description='Get the README content for a GitHub repository')
def get_repo_readme(repo: str) -> ToolResult:
    '''
    Get the README content for a GitHub repository.

    Input:
        repo: Full repository name (e.g., 'org/repo').

    Output:
        ToolResult with README content and metadata.
    '''
    log.debug(f'get_repo_readme(repo={repo})')

    try:
        get_github()
        result = _get_repo_readme(repo)

        return ToolResult.success(result, repo=repo)

    except Exception as e:
        log.error(f'Failed to get repo README: {e}')
        return ToolResult.failure(f'Failed to get README for {repo}: {e}')


@tool(description='List documentation files in a GitHub repository directory')
def list_repo_docs(repo: str, path: str = 'docs', extensions: Optional[list[str]] = None) -> ToolResult:
    '''
    List documentation files in a GitHub repository directory.

    Input:
        repo: Full repository name (e.g., 'org/repo').
        path: Directory path to search (default: 'docs').
        extensions: List of file extensions to include.

    Output:
        ToolResult with list of documentation file dicts.
    '''
    log.debug(f'list_repo_docs(repo={repo}, path={path})')

    try:
        get_github()
        docs = _list_repo_docs(repo, path=path, extensions=extensions)

        return ToolResult.success(docs, count=len(docs), repo=repo, path=path)

    except Exception as e:
        log.error(f'Failed to list repo docs: {e}')
        return ToolResult.failure(f'Failed to list docs for {repo}: {e}')


@tool(description='Search documentation files in a GitHub repository by content query')
def search_repo_docs(repo: str, query: str, extensions: Optional[list[str]] = None) -> ToolResult:
    '''
    Search documentation files in a GitHub repository by content query.

    Input:
        repo: Full repository name (e.g., 'org/repo').
        query: Search query string.
        extensions: List of file extensions to search.

    Output:
        ToolResult with list of matching documentation file dicts.
    '''
    log.debug(f'search_repo_docs(repo={repo}, query={query!r})')

    try:
        get_github()
        docs = _search_repo_docs(repo, query, extensions=extensions)

        return ToolResult.success(docs, count=len(docs), repo=repo, query=query)

    except Exception as e:
        log.error(f'Failed to search repo docs: {e}')
        return ToolResult.failure(f'Failed to search docs for {repo}: {e}')


# ****************************************************************************************
# Tool Collection Class
# ****************************************************************************************

class GitHubTools(BaseTool):
    '''
    Collection of GitHub tools for agent use.

    Provides all GitHub operations as a unified tool collection,
    wrapping github_utils.py functionality.
    '''

    @tool(description='List repositories in a GitHub organization')
    def list_repos(self, org: str) -> ToolResult:
        return list_repos(org)

    @tool(description='Get detailed information about a GitHub repository')
    def get_repo_info(self, repo_name: str) -> ToolResult:
        return get_repo_info(repo_name)

    @tool(description='Validate that a GitHub repository exists and is accessible')
    def validate_repository(self, repo_name: str) -> ToolResult:
        return validate_repository(repo_name)

    @tool(description='List pull requests for a GitHub repository')
    def list_pull_requests(
        self,
        repo_name: str,
        state: str = 'open',
        sort: str = 'created',
        direction: str = 'desc',
        limit: int = 100,
    ) -> ToolResult:
        return list_pull_requests(repo_name, state, sort, direction, limit)

    @tool(description='Get detailed information about a specific pull request')
    def get_pull_request(self, repo_name: str, pr_number: int) -> ToolResult:
        return get_pull_request(repo_name, pr_number)

    @tool(description='Get reviews for a specific pull request')
    def get_pr_reviews(self, repo_name: str, pr_number: int) -> ToolResult:
        return get_pr_reviews(repo_name, pr_number)

    @tool(description='Get pending review requests for a specific pull request')
    def get_pr_review_requests(self, repo_name: str, pr_number: int) -> ToolResult:
        return get_pr_review_requests(repo_name, pr_number)

    @tool(description='Find stale pull requests')
    def find_stale_prs(self, repo_name: str, stale_days: int = 5) -> ToolResult:
        return find_stale_prs(repo_name, stale_days)

    @tool(description='Find pull requests missing reviews')
    def find_missing_reviews(self, repo_name: str) -> ToolResult:
        return find_missing_reviews(repo_name)

    @tool(description='Run comprehensive PR hygiene analysis')
    def analyze_pr_hygiene(self, repo_name: str, stale_days: int = 5) -> ToolResult:
        return analyze_pr_hygiene(repo_name, stale_days)

    @tool(description='Get current GitHub API rate limit status')
    def get_rate_limit_status(self) -> ToolResult:
        return get_rate_limit_status()

    @tool(description='Check branch and PR title naming compliance against Jira ticket conventions')
    def check_naming_compliance(self, repo_name: str, ticket_patterns: str = '') -> ToolResult:
        return check_naming_compliance(repo_name, ticket_patterns)

    @tool(description='Find open PRs with merge conflicts')
    def check_merge_conflicts(self, repo_name: str) -> ToolResult:
        return check_merge_conflicts(repo_name)

    @tool(description='Find open PRs with failing CI checks')
    def check_ci_failures(self, repo_name: str) -> ToolResult:
        return check_ci_failures(repo_name)

    @tool(description='Find stale branches with no recent activity and no open PRs')
    def check_stale_branches(self, repo_name: str, stale_days: int = 30) -> ToolResult:
        return check_stale_branches(repo_name, stale_days)

    @tool(description='Run comprehensive extended hygiene analysis including all scan types')
    def analyze_extended_hygiene(self, repo_name: str, stale_days: int = 5, branch_stale_days: int = 30) -> ToolResult:
        return analyze_extended_hygiene(repo_name, stale_days, branch_stale_days)

    @tool(description='Get the README content for a GitHub repository')
    def get_repo_readme(self, repo: str) -> ToolResult:
        return get_repo_readme(repo)

    @tool(description='List documentation files in a GitHub repository directory')
    def list_repo_docs(self, repo: str, path: str = 'docs', extensions: Optional[list[str]] = None) -> ToolResult:
        return list_repo_docs(repo, path, extensions)

    @tool(description='Search documentation files in a GitHub repository by content query')
    def search_repo_docs(self, repo: str, query: str, extensions: Optional[list[str]] = None) -> ToolResult:
        return search_repo_docs(repo, query, extensions)
