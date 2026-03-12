from __future__ import annotations

from typing import Any, Iterable, Sequence


def _quote_values(values: Iterable[str]) -> str:
    return ', '.join([f'"{value}"' for value in values])


def _build_status_jql(statuses: Sequence[str] | dict[str, Sequence[str]] | None) -> str:
    if not statuses:
        return ''

    clauses = []

    if isinstance(statuses, dict):
        includes = statuses.get('include', [])
        excludes = statuses.get('exclude', [])

        if includes:
            clauses.append(f'status IN ({_quote_values(includes)})')

        if excludes:
            clauses.append(f'status NOT IN ({_quote_values(excludes)})')
    else:
        clauses.append(f'status IN ({_quote_values(statuses)})')

    return ' AND '.join(clauses)


def build_tickets_jql(project: str, issue_types: Sequence[str] | None = None, statuses: Sequence[str] | dict[str, Sequence[str]] | None = None, date_filter: str | None = None, jql_extra: str | None = None) -> str:
    jql_parts = [f'project = "{project}"']

    if jql_extra:
        jql_parts.append(jql_extra)

    if issue_types:
        jql_parts.append(f'issuetype IN ({_quote_values(issue_types)})')

    status_clause = _build_status_jql(statuses)
    if status_clause:
        jql_parts.append(status_clause)

    jql = ' AND '.join(jql_parts)
    if date_filter:
        jql = f'{jql} {date_filter}'

    return f'{jql} ORDER BY created DESC'


def build_release_tickets_jql(project: str, release: str, issue_types: Sequence[str] | None = None, statuses: Sequence[str] | dict[str, Sequence[str]] | None = None) -> str:
    return build_tickets_jql(
        project,
        issue_types=issue_types,
        statuses=statuses,
        jql_extra=f'fixVersion = "{release}"',
    )


def build_releases_tickets_jql(project: str, releases: Sequence[str], issue_types: Sequence[str] | None = None, statuses: Sequence[str] | dict[str, Sequence[str]] | None = None, date_filter: str | None = None) -> str:
    jql = build_tickets_jql(
        project,
        issue_types=issue_types,
        statuses=statuses,
        date_filter=date_filter,
        jql_extra=f'fixVersion IN ({_quote_values(releases)})',
    )
    return jql.replace('ORDER BY created DESC', 'ORDER BY fixVersion DESC, created DESC', 1)


def build_no_release_jql(project: str, issue_types: Sequence[str] | None = None, statuses: Sequence[str] | dict[str, Sequence[str]] | None = None) -> str:
    return build_tickets_jql(
        project,
        issue_types=issue_types,
        statuses=statuses,
        jql_extra='fixVersion is EMPTY',
    )


def paginated_jql_search(
    jira_connection: Any,
    jql: str,
    max_results: int | None = None,
    fields: Sequence[str] | None = None,
    page_size: int = 100,
) -> list[Any]:
    all_issues: list[Any] = []
    start_at = 0
    effective_page_size = max(1, page_size)

    while True:
        if max_results is not None:
            remaining = max_results - len(all_issues)
            if remaining <= 0:
                break
            current_page_size = min(effective_page_size, remaining)
        else:
            current_page_size = effective_page_size

        search_kwargs: dict[str, Any] = {
            'startAt': start_at,
            'maxResults': current_page_size,
        }
        if fields is not None:
            search_kwargs['fields'] = list(fields)

        issues_page = jira_connection.search_issues(jql, **search_kwargs)

        page_items = list(issues_page or [])
        if not page_items:
            break

        all_issues.extend(page_items)

        if len(page_items) < current_page_size:
            break

        start_at += len(page_items)

    if max_results is not None and len(all_issues) > max_results:
        return all_issues[:max_results]

    return all_issues
