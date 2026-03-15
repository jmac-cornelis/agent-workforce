##########################################################################################
#
# Module: agents/gantt_components.py
#
# Description: Deterministic planning components used by the Gantt Project Planner.
#              Splits backlog interpretation, dependency mapping, milestone planning,
#              risk projection, and summary formatting into reusable units.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from agents.gantt_models import (
    DependencyEdge,
    DependencyGraph,
    MilestoneProposal,
    PlanningRequest,
    PlanningRiskRecord,
    PlanningSnapshot,
)
from core.tickets import issue_to_dict

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class BacklogInterpreter:
    '''
    Normalizes Jira backlog issues into a consistent planning shape.
    '''

    DEFAULT_FIELDS = ','.join([
        'summary',
        'description',
        'issuetype',
        'status',
        'priority',
        'assignee',
        'reporter',
        'created',
        'updated',
        'resolutiondate',
        'project',
        'fixVersions',
        'versions',
        'components',
        'labels',
        'issuelinks',
        'parent',
        'duedate',
    ])

    def __init__(
        self,
        jira_provider: Callable[[], Any],
        now_provider: Callable[[], datetime],
        stale_days: int = 30,
    ):
        self._jira_provider = jira_provider
        self._now_provider = now_provider
        self._stale_days = stale_days

    def load_backlog_issues(self, request: PlanningRequest) -> List[Dict[str, Any]]:
        '''
        Query Jira and normalize issues for planning.
        '''
        jira = self._jira_provider()
        jql = request.backlog_jql or self.build_backlog_jql(request)
        issues = jira.search_issues(
            jql,
            maxResults=request.limit,
            fields=self.DEFAULT_FIELDS,
        )
        return [self.normalize_issue(issue) for issue in issues]

    @staticmethod
    def build_backlog_jql(request: PlanningRequest) -> str:
        clauses = [
            f'project = "{request.project_key}"',
            'issuetype != "Sub-task"',
        ]
        if not request.include_done:
            clauses.append('statusCategory != Done')
        return ' AND '.join(clauses) + ' ORDER BY updated DESC'

    def normalize_issue(self, issue: Any) -> Dict[str, Any]:
        '''
        Convert a Jira issue resource into a normalized planning record.
        '''
        base = issue_to_dict(issue)
        raw = getattr(issue, 'raw', None) if hasattr(issue, 'raw') else issue
        fields = raw.get('fields', {}) if isinstance(raw, dict) else {}

        parent = fields.get('parent') or {}
        parent_key = parent.get('key', '') if isinstance(parent, dict) else ''
        due_date = str(fields.get('duedate') or '')
        status_obj = fields.get('status') or {}
        status_category = ''
        if isinstance(status_obj, dict):
            status_category = str(
                (status_obj.get('statusCategory') or {}).get('name', '') or ''
            )

        updated_ts = base.get('updated') or ''
        updated_dt = self.parse_jira_datetime(updated_ts)
        now = self._now_provider()
        age_days = (now - updated_dt).days if updated_dt else 0
        is_done = status_category.casefold() == 'done' or self.is_done_status(
            base.get('status', '')
        )

        normalized = dict(base)
        normalized.update({
            'parent_key': parent_key,
            'due_date': due_date,
            'status_category': status_category,
            'is_done': is_done,
            'age_days': age_days,
            'is_stale': age_days >= self._stale_days and not is_done,
            # Internal planner-only field. DependencyMapper consumes and removes it.
            '_issue_links': fields.get('issuelinks') or [],
        })
        return normalized

    @staticmethod
    def parse_jira_datetime(value: str) -> Optional[datetime]:
        if not value:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
        ]
        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        return None

    @staticmethod
    def is_done_status(status: str) -> bool:
        return str(status).casefold() in {'done', 'closed', 'resolved'}

    @staticmethod
    def is_high_priority(priority: str) -> bool:
        normalized = str(priority).casefold()
        return any(
            token in normalized
            for token in ('blocker', 'critical', 'highest', 'high', 'p0', 'p1')
        )


class DependencyMapper:
    '''
    Identifies explicit dependency relationships and produces a graph view.
    '''

    def attach_dependency_edges(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        Enrich normalized issues with extracted dependency edges.
        '''
        enriched: List[Dict[str, Any]] = []
        for issue in issues:
            issue_copy = dict(issue)
            edges = self.extract_edges(
                issue_copy.get('key', ''),
                issue_copy.get('parent_key', ''),
                issue_copy.pop('_issue_links', []),
            )
            issue_copy['dependency_edges'] = [edge.to_dict() for edge in edges]
            enriched.append(issue_copy)
        return enriched

    def build_graph(self, issues: List[Dict[str, Any]]) -> DependencyGraph:
        nodes = []
        edges: List[DependencyEdge] = []
        seen_edges = set()
        blocked_keys = set()
        unscheduled_keys = set()

        for issue in issues:
            nodes.append({
                'key': issue.get('key', ''),
                'summary': issue.get('summary', ''),
                'issue_type': issue.get('issue_type', ''),
                'status': issue.get('status', ''),
                'assignee': issue.get('assignee_display') or issue.get('assignee', ''),
                'fix_versions': issue.get('fix_versions', []),
            })

            if self.is_blocked_status(issue.get('status', '')):
                blocked_keys.add(issue.get('key', ''))
            if not issue.get('fix_versions') and not issue.get('is_done', False):
                unscheduled_keys.add(issue.get('key', ''))

            for edge_dict in issue.get('dependency_edges', []):
                edge = DependencyEdge(**edge_dict)
                dedupe_key = (edge.source_key, edge.target_key, edge.relationship)
                if dedupe_key in seen_edges:
                    continue
                seen_edges.add(dedupe_key)
                edges.append(edge)
                if edge.relationship == 'blocks':
                    blocked_keys.add(edge.target_key)

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            blocked_keys=sorted(key for key in blocked_keys if key),
            unscheduled_keys=sorted(key for key in unscheduled_keys if key),
        )

    def extract_edges(
        self,
        issue_key: str,
        parent_key: str,
        issue_links: Iterable[Any],
    ) -> List[DependencyEdge]:
        edges: List[DependencyEdge] = []

        if parent_key:
            edges.append(
                DependencyEdge(
                    source_key=parent_key,
                    target_key=issue_key,
                    relationship='parent_of',
                    evidence='jira_parent',
                )
            )

        for link in issue_links:
            if not isinstance(link, dict):
                continue
            link_type = link.get('type') or {}
            outward = self.slugify_relationship(
                link_type.get('outward') or link_type.get('name') or 'linked_to'
            )
            if link.get('outwardIssue'):
                target = link['outwardIssue'].get('key', '')
                if target:
                    edges.append(
                        DependencyEdge(
                            source_key=issue_key,
                            target_key=target,
                            relationship=outward,
                            evidence='jira_issue_link',
                        )
                    )
            elif link.get('inwardIssue'):
                source = link['inwardIssue'].get('key', '')
                if source:
                    edges.append(
                        DependencyEdge(
                            source_key=source,
                            target_key=issue_key,
                            relationship=outward,
                            evidence='jira_issue_link',
                        )
                    )

        return edges

    @staticmethod
    def slugify_relationship(value: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '_', str(value).casefold()).strip('_')
        return slug or 'linked_to'

    @staticmethod
    def is_blocked_status(status: str) -> bool:
        normalized = str(status).casefold()
        return any(token in normalized for token in ('blocked', 'on hold', 'impeded'))


class MilestonePlanner:
    '''
    Groups backlog work into milestone proposals.
    '''

    def build_milestones(
        self,
        issues: List[Dict[str, Any]],
        releases: List[Dict[str, Any]],
        dependency_graph: DependencyGraph,
    ) -> List[MilestoneProposal]:
        release_map = {release.get('name', ''): release for release in releases}
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for issue in issues:
            targets = issue.get('fix_versions') or []
            milestone_name = targets[0] if targets else 'Unscheduled Backlog'
            grouped.setdefault(milestone_name, []).append(issue)

        proposals: List[MilestoneProposal] = []
        for name, bucket in grouped.items():
            release = release_map.get(name, {})
            total_issues = len(bucket)
            done_issues = sum(1 for issue in bucket if issue.get('is_done'))
            open_issues = total_issues - done_issues
            blocked_issues = sum(
                1 for issue in bucket if issue.get('key') in dependency_graph.blocked_keys
            )
            unassigned_issues = sum(
                1
                for issue in bucket
                if not issue.get('is_done')
                and (issue.get('assignee_display') or issue.get('assignee'))
                in ('', None, 'Unassigned')
            )

            risk_level = self.milestone_risk_level(
                open_issues,
                blocked_issues,
                unassigned_issues,
                release.get('releaseDate'),
            )
            confidence = 'high'
            if name == 'Unscheduled Backlog' or blocked_issues:
                confidence = 'medium'
            if not release.get('releaseDate') and name != 'Unscheduled Backlog':
                confidence = 'low'

            summary = (
                f'{open_issues} open, {blocked_issues} blocked, '
                f'{unassigned_issues} unassigned'
            )

            proposals.append(
                MilestoneProposal(
                    name=name,
                    source='fix_version' if name != 'Unscheduled Backlog' else 'backlog',
                    target_date=str(release.get('releaseDate') or ''),
                    issue_keys=[issue.get('key', '') for issue in bucket],
                    total_issues=total_issues,
                    open_issues=open_issues,
                    done_issues=done_issues,
                    blocked_issues=blocked_issues,
                    unassigned_issues=unassigned_issues,
                    confidence=confidence,
                    risk_level=risk_level,
                    summary=summary,
                )
            )

        proposals.sort(key=self.milestone_sort_key)
        return proposals

    def milestone_risk_level(
        self,
        open_issues: int,
        blocked_issues: int,
        unassigned_issues: int,
        release_date: Optional[str],
    ) -> str:
        if blocked_issues >= 2 or unassigned_issues >= 3:
            return 'high'
        if blocked_issues >= 1 or unassigned_issues >= 1:
            return 'medium'
        if release_date and open_issues >= 8:
            return 'medium'
        return 'low'

    @staticmethod
    def milestone_sort_key(milestone: MilestoneProposal) -> tuple[int, str, str]:
        if milestone.name == 'Unscheduled Backlog':
            return (1, '9999-99-99', milestone.name)
        target = milestone.target_date or '9999-99-99'
        return (0, target, milestone.name)


class RiskProjector:
    '''
    Projects evidence gaps and planning risks from the current backlog view.
    '''

    def build_evidence_gaps(self, issues: List[Dict[str, Any]]) -> List[str]:
        gaps = [
            'Build, test, release, and traceability evidence are not yet integrated into Gantt snapshots.',
            'Meeting-derived decisions and action items are not yet connected to planning snapshots.',
        ]

        unscheduled = sum(
            1
            for issue in issues
            if not issue.get('fix_versions') and not issue.get('is_done')
        )
        if unscheduled:
            gaps.append(
                f'{unscheduled} active work items have no release target/fix version.'
            )

        return gaps

    def build_risks(
        self,
        issues: List[Dict[str, Any]],
        milestones: List[MilestoneProposal],
        dependency_graph: DependencyGraph,
    ) -> List[PlanningRiskRecord]:
        risks: List[PlanningRiskRecord] = []

        stale = [issue for issue in issues if issue.get('is_stale')]
        if stale:
            risks.append(
                PlanningRiskRecord(
                    risk_type='stale_work',
                    severity='high' if len(stale) >= 3 else 'medium',
                    title='Stale active work detected',
                    description='Open work items have not been updated recently and may indicate roadmap drift.',
                    issue_keys=[issue['key'] for issue in stale],
                    evidence=[
                        f"{issue['key']} last updated {issue.get('updated_date', '')} ({issue.get('age_days', 0)} days ago)"
                        for issue in stale[:10]
                    ],
                    recommendation='Review stale items and confirm whether they should move, close, or regain ownership.',
                )
            )

        blocked = [
            issue
            for issue in issues
            if issue.get('key') in dependency_graph.blocked_keys and not issue.get('is_done')
        ]
        if blocked:
            risks.append(
                PlanningRiskRecord(
                    risk_type='blocked_work',
                    severity='high' if len(blocked) >= 2 else 'medium',
                    title='Blocked work items detected',
                    description='Dependencies or blocked statuses may threaten milestone confidence.',
                    issue_keys=[issue['key'] for issue in blocked],
                    evidence=[
                        f"{issue['key']} status={issue.get('status', '')}"
                        for issue in blocked[:10]
                    ],
                    recommendation='Resolve blockers before committing to milestone dates or delivery promises.',
                )
            )

        unassigned_high = [
            issue
            for issue in issues
            if not issue.get('is_done')
            and BacklogInterpreter.is_high_priority(issue.get('priority', ''))
            and (issue.get('assignee_display') or issue.get('assignee'))
            in ('', None, 'Unassigned')
        ]
        if unassigned_high:
            risks.append(
                PlanningRiskRecord(
                    risk_type='unassigned_priority_work',
                    severity='high',
                    title='High-priority work lacks ownership',
                    description='Priority backlog items without assignees are likely to slip silently.',
                    issue_keys=[issue['key'] for issue in unassigned_high],
                    evidence=[
                        f"{issue['key']} priority={issue.get('priority', '')}"
                        for issue in unassigned_high[:10]
                    ],
                    recommendation='Assign owners or explicitly de-scope these items from current milestones.',
                )
            )

        unscheduled = [
            issue for issue in issues if not issue.get('is_done') and not issue.get('fix_versions')
        ]
        if unscheduled:
            risks.append(
                PlanningRiskRecord(
                    risk_type='unscheduled_work',
                    severity='medium',
                    title='Backlog items without milestone targets',
                    description='Active work without a release target weakens milestone and roadmap clarity.',
                    issue_keys=[issue['key'] for issue in unscheduled],
                    evidence=[f"{issue['key']} has no fix version" for issue in unscheduled[:10]],
                    recommendation='Either assign these items to a milestone or classify them explicitly as unscheduled backlog.',
                )
            )

        overloaded = [milestone for milestone in milestones if milestone.open_issues >= 10]
        if overloaded:
            risks.append(
                PlanningRiskRecord(
                    risk_type='milestone_overload',
                    severity='medium',
                    title='Milestones with heavy open scope detected',
                    description='Large open milestone scope increases coordination risk and reduces confidence.',
                    issue_keys=[key for milestone in overloaded for key in milestone.issue_keys[:5]],
                    evidence=[
                        f'{milestone.name}: {milestone.open_issues} open items'
                        for milestone in overloaded
                    ],
                    recommendation='Consider splitting large milestones or rebalancing scope across release targets.',
                )
            )

        return risks


class PlanningSummarizer:
    '''
    Builds machine-readable overview data and human-readable planning summaries.
    '''

    def build_backlog_overview(
        self,
        issues: List[Dict[str, Any]],
        milestones: List[MilestoneProposal],
        dependency_graph: DependencyGraph,
        risks: List[PlanningRiskRecord],
    ) -> Dict[str, Any]:
        total_issues = len(issues)
        done_issues = sum(1 for issue in issues if issue.get('is_done'))
        open_issues = total_issues - done_issues
        stale_issues = sum(1 for issue in issues if issue.get('is_stale'))
        unassigned_issues = sum(
            1
            for issue in issues
            if not issue.get('is_done')
            and (issue.get('assignee_display') or issue.get('assignee'))
            in ('', None, 'Unassigned')
        )

        return {
            'total_issues': total_issues,
            'open_issues': open_issues,
            'done_issues': done_issues,
            'blocked_issues': len(dependency_graph.blocked_keys),
            'stale_issues': stale_issues,
            'unassigned_issues': unassigned_issues,
            'milestone_count': len(milestones),
            'risk_count': len(risks),
            'dependency_edges': dependency_graph.edge_count,
        }

    def format_snapshot(self, snapshot: PlanningSnapshot) -> str:
        overview = snapshot.backlog_overview
        lines = [
            f'# GANTT PLANNING SNAPSHOT: {snapshot.project_key}',
            '',
            f'**Snapshot ID**: {snapshot.snapshot_id}',
            f'**Created At**: {snapshot.created_at}',
            f'**Planning Horizon**: {snapshot.planning_horizon_days} days',
            '',
            '## Backlog Overview',
            '',
            f"- Total issues: {overview.get('total_issues', 0)}",
            f"- Open issues: {overview.get('open_issues', 0)}",
            f"- Done issues: {overview.get('done_issues', 0)}",
            f"- Blocked issues: {overview.get('blocked_issues', 0)}",
            f"- Stale issues: {overview.get('stale_issues', 0)}",
            f"- Unassigned issues: {overview.get('unassigned_issues', 0)}",
            f"- Dependency edges: {overview.get('dependency_edges', 0)}",
            '',
            '## Milestone Proposals',
            '',
        ]

        if snapshot.milestones:
            for milestone in snapshot.milestones:
                target = milestone.target_date or 'unscheduled'
                lines.extend([
                    f"- **{milestone.name}** ({target})",
                    f"  Open: {milestone.open_issues}, Blocked: {milestone.blocked_issues}, "
                    f"Unassigned: {milestone.unassigned_issues}, Risk: {milestone.risk_level.upper()}, "
                    f"Confidence: {milestone.confidence.upper()}",
                    f"  Summary: {milestone.summary}",
                ])
        else:
            lines.append('- No milestone proposals generated.')

        lines.extend([
            '',
            '## Planning Risks',
            '',
        ])

        if snapshot.risks:
            for risk in snapshot.risks:
                lines.extend([
                    f"- **{risk.title}** [{risk.severity.upper()}]",
                    f"  {risk.description}",
                    f"  Recommendation: {risk.recommendation}",
                ])
        else:
            lines.append('- No major planning risks detected from the current Jira view.')

        lines.extend([
            '',
            '## Dependency Summary',
            '',
            f"- Nodes: {snapshot.dependency_graph.node_count}",
            f"- Edges: {snapshot.dependency_graph.edge_count}",
            f"- Blocked keys: {len(snapshot.dependency_graph.blocked_keys)}",
            f"- Unscheduled keys: {len(snapshot.dependency_graph.unscheduled_keys)}",
            '',
            '## Evidence Gaps',
            '',
        ])

        for gap in snapshot.evidence_gaps:
            lines.append(f'- {gap}')

        return '\n'.join(lines)
