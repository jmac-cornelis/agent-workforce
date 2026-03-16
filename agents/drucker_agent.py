##########################################################################################
#
# Module: agents/drucker_agent.py
#
# Description: Drucker Jira Coordinator agent.
#              Produces deterministic Jira hygiene reports, ticket-level
#              remediation suggestions, and review-gated Jira write-back plans.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.drucker_models import (
    DruckerAction,
    DruckerFinding,
    DruckerHygieneReport,
    DruckerRequest,
)
from agents.review_agent import ReviewAgent, ReviewItem, ReviewSession
from tools.jira_tools import JiraTools, get_project_info, search_tickets

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class DruckerCoordinatorAgent(BaseAgent):
    '''
    Deterministic-first Jira hygiene coordinator.

    Drucker analyzes project hygiene, identifies risky ticket states, proposes
    low-risk Jira actions, and hands execution off through review-gated paths.
    '''

    DEFAULT_FIELDS = [
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
    ]

    CATEGORY_LABELS = {
        'stale_ticket': 'stale',
        'blocked_stale_ticket': 'blocked',
        'unassigned_ticket': 'needs-owner',
        'missing_fix_version': 'needs-release-target',
        'missing_component': 'needs-component',
        'missing_labels': 'needs-triage',
    }

    def __init__(self, project_key: Optional[str] = None, **kwargs):
        instruction = self._load_prompt_file()
        if not instruction:
            raise FileNotFoundError(
                'config/prompts/drucker_agent.md is required but not found. '
                'The Drucker Coordinator Agent has no hardcoded fallback prompt.'
            )

        config = AgentConfig(
            name='drucker_coordinator',
            description='Coordinates Jira hygiene analysis and review-gated Jira actions',
            instruction=instruction,
            max_iterations=12,
        )

        super().__init__(config=config, tools=[JiraTools()], **kwargs)
        self.project_key = project_key
        self._review_agent: Optional[ReviewAgent] = None

    @staticmethod
    def _load_prompt_file() -> Optional[str]:
        prompt_path = os.path.join('config', 'prompts', 'drucker_agent.md')
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                log.warning(f'Failed to load Drucker agent prompt: {e}')
        return None

    @property
    def review_agent(self) -> ReviewAgent:
        if self._review_agent is None:
            self._review_agent = ReviewAgent()
        return self._review_agent

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Build a Jira hygiene report and corresponding review session.
        '''
        log.debug(f'DruckerCoordinatorAgent.run(input_data={input_data})')

        if isinstance(input_data, str):
            request = DruckerRequest(project_key=input_data)
        elif isinstance(input_data, dict):
            request = DruckerRequest(
                project_key=input_data.get('project_key', self.project_key or ''),
                limit=int(input_data.get('limit', 200)),
                include_done=bool(input_data.get('include_done', False)),
                stale_days=int(input_data.get('stale_days', 30)),
                jql=input_data.get('jql'),
                label_prefix=str(input_data.get('label_prefix', 'drucker') or 'drucker'),
            )
        else:
            return AgentResponse.error_response(
                'Invalid input: expected project key string or request dict'
            )

        if not request.project_key:
            return AgentResponse.error_response('No project_key provided')

        try:
            report = self.analyze_project_hygiene(request)
            review_session = self.create_review_session(report)
        except Exception as e:
            log.error(f'Drucker hygiene analysis failed: {e}')
            return AgentResponse.error_response(str(e))

        return AgentResponse.success_response(
            content=report.summary_markdown,
            metadata={
                'hygiene_report': report.to_dict(),
                'review_session': review_session.to_dict(),
            },
        )

    def analyze_project_hygiene(
        self,
        request: DruckerRequest,
    ) -> DruckerHygieneReport:
        '''
        Produce a deterministic Jira hygiene report for a project.
        '''
        log.info(f'Creating Drucker hygiene report for {request.project_key}')

        project_info = self._load_project_info(request.project_key)
        tickets = self._load_tickets(request)
        findings = self._build_findings(tickets, stale_days=request.stale_days)
        actions = self._build_actions(
            tickets,
            findings,
            label_prefix=request.label_prefix,
        )
        summary = self._build_summary(tickets, findings, actions)

        report = DruckerHygieneReport(
            project_key=request.project_key,
            request=request.to_dict(),
            project_info=project_info,
            summary=summary,
            findings=findings,
            proposed_actions=actions,
            tickets=tickets,
        )
        report.summary_markdown = self._format_report(report)
        return report

    def create_review_session(self, report: DruckerHygieneReport) -> ReviewSession:
        '''
        Convert proposed Drucker actions into a review-gated execution session.
        '''
        session = ReviewSession(
            session_id=report.report_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        ticket_summaries = {
            str(ticket.get('key') or ''): str(ticket.get('summary') or '')
            for ticket in report.tickets
        }

        for action in report.proposed_actions:
            data: Dict[str, Any] = {
                'ticket_key': action.ticket_key,
                'ticket_summary': ticket_summaries.get(action.ticket_key, ''),
                'title': action.title,
                'reason': action.description,
                'finding_ids': action.finding_ids,
                'confidence': action.confidence,
            }

            if action.action_type == 'comment':
                data['body'] = action.comment
            elif action.action_type == 'update':
                data.update(action.update_fields)
            elif action.action_type == 'transition':
                data['to_status'] = action.transition_to
                if action.comment:
                    data['comment'] = action.comment

            session.add_item(ReviewItem(
                id=action.action_id,
                item_type='ticket',
                action=action.action_type,
                data=data,
            ))

        return session

    def execute_approved_actions(self, session: ReviewSession) -> List[Dict[str, Any]]:
        '''
        Execute already-approved Drucker actions through the shared ReviewAgent.
        '''
        return self.review_agent.execute_approved(session)

    def _load_project_info(self, project_key: str) -> Dict[str, Any]:
        result = get_project_info(project_key)
        if result.is_success:
            return result.data
        raise RuntimeError(result.error or f'Failed to load project info for {project_key}')

    def _load_tickets(self, request: DruckerRequest) -> List[Dict[str, Any]]:
        result = search_tickets(
            self._build_jql(request),
            limit=request.limit,
            fields=self.DEFAULT_FIELDS,
        )
        if result.is_error:
            raise RuntimeError(
                result.error or f'Failed to search tickets for {request.project_key}'
            )

        return [
            self._normalize_ticket(ticket, stale_days=request.stale_days)
            for ticket in result.data
        ]

    @staticmethod
    def _build_jql(request: DruckerRequest) -> str:
        if request.jql:
            return request.jql

        clauses = [f'project = "{request.project_key}"']
        if not request.include_done:
            clauses.append('statusCategory != Done')
        return ' AND '.join(clauses) + ' ORDER BY updated ASC'

    def _normalize_ticket(
        self,
        ticket: Dict[str, Any],
        stale_days: int,
    ) -> Dict[str, Any]:
        normalized = dict(ticket)
        updated_dt = self._parse_jira_datetime(str(ticket.get('updated') or ''))
        now = datetime.now(timezone.utc)
        age_days = (now - updated_dt).days if updated_dt else 0
        is_done = self._is_done_status(ticket.get('status', ''))
        is_blocked = self._is_blocked_status(ticket.get('status', ''))
        labels = [
            str(label)
            for label in (ticket.get('labels') or [])
            if str(label).strip()
        ]

        normalized.update({
            'age_days': age_days,
            'is_done': is_done,
            'is_blocked': is_blocked,
            'is_high_priority': self._is_high_priority(ticket.get('priority', '')),
            'is_stale': age_days >= stale_days and not is_done,
            'labels': labels,
            'components': list(ticket.get('components') or []),
            'fix_versions': list(ticket.get('fix_versions') or []),
        })
        return normalized

    def _build_findings(
        self,
        tickets: List[Dict[str, Any]],
        stale_days: int,
    ) -> List[DruckerFinding]:
        findings: List[DruckerFinding] = []
        finding_index = 1

        for ticket in tickets:
            if ticket.get('is_done'):
                continue

            key = str(ticket.get('key') or '')
            priority = str(ticket.get('priority') or '')
            age_days = int(ticket.get('age_days') or 0)
            status = str(ticket.get('status') or '')

            def add_finding(
                category: str,
                severity: str,
                title: str,
                description: str,
                evidence: List[str],
                recommendation: str,
            ) -> None:
                nonlocal finding_index
                findings.append(
                    DruckerFinding(
                        finding_id=f'F{finding_index:03d}',
                        ticket_key=key,
                        category=category,
                        severity=severity,
                        title=title,
                        description=description,
                        evidence=evidence,
                        recommendation=recommendation,
                    )
                )
                finding_index += 1

            if ticket.get('is_stale'):
                severity = 'high' if ticket.get('is_high_priority') else 'medium'
                add_finding(
                    category='stale_ticket',
                    severity=severity,
                    title='Active ticket is stale',
                    description=(
                        f'{key} has not been updated in {age_days} days and may need triage or owner confirmation.'
                    ),
                    evidence=[
                        f'status={status}',
                        f'priority={priority}',
                        f'updated={ticket.get("updated_date", "")}',
                    ],
                    recommendation='Confirm the current owner, status, and next action for this ticket.',
                )

            if ticket.get('is_blocked') and age_days >= min(stale_days, 14):
                add_finding(
                    category='blocked_stale_ticket',
                    severity='high',
                    title='Blocked ticket has gone stale',
                    description=(
                        f'{key} is blocked and has not moved in {age_days} days.'
                    ),
                    evidence=[
                        f'status={status}',
                        f'updated={ticket.get("updated_date", "")}',
                    ],
                    recommendation='Escalate or clarify the blocker before the ticket remains blocked indefinitely.',
                )

            if str(ticket.get('assignee_display') or ticket.get('assignee') or '').strip() in ('', 'Unassigned'):
                add_finding(
                    category='unassigned_ticket',
                    severity='high' if ticket.get('is_high_priority') else 'medium',
                    title='Active ticket has no assignee',
                    description=f'{key} is active work without a clear owner.',
                    evidence=[
                        f'priority={priority}',
                        f'status={status}',
                    ],
                    recommendation='Assign an owner or explicitly de-scope the ticket from active work.',
                )

            if not ticket.get('fix_versions'):
                add_finding(
                    category='missing_fix_version',
                    severity='high' if ticket.get('is_high_priority') else 'medium',
                    title='Active ticket has no release target',
                    description=f'{key} has no fix version or release target assigned.',
                    evidence=[
                        f'priority={priority}',
                        f'labels={", ".join(ticket.get("labels", [])) or "none"}',
                    ],
                    recommendation='Either assign a target release or explicitly classify the ticket as unscheduled backlog.',
                )

            if not ticket.get('components'):
                add_finding(
                    category='missing_component',
                    severity='medium',
                    title='Ticket is missing component metadata',
                    description=f'{key} has no Jira component set.',
                    evidence=[
                        f'issue_type={ticket.get("issue_type", "")}',
                    ],
                    recommendation='Add a component so routing, ownership, and reporting are more reliable.',
                )

            if not ticket.get('labels'):
                add_finding(
                    category='missing_labels',
                    severity='low',
                    title='Ticket has no labels',
                    description=f'{key} has no Jira labels for triage or reporting.',
                    evidence=[
                        f'issue_type={ticket.get("issue_type", "")}',
                        f'components={", ".join(ticket.get("components", [])) or "none"}',
                    ],
                    recommendation='Add at least one durable label to help filtering and triage.',
                )

        return findings

    def _build_actions(
        self,
        tickets: List[Dict[str, Any]],
        findings: List[DruckerFinding],
        label_prefix: str,
    ) -> List[DruckerAction]:
        actions: List[DruckerAction] = []
        findings_by_ticket: Dict[str, List[DruckerFinding]] = defaultdict(list)
        tickets_by_key = {
            str(ticket.get('key') or ''): ticket
            for ticket in tickets
        }

        for finding in findings:
            findings_by_ticket[finding.ticket_key].append(finding)

        action_index = 1
        for ticket_key in sorted(findings_by_ticket):
            ticket_findings = findings_by_ticket[ticket_key]
            ticket = tickets_by_key.get(ticket_key, {})
            existing_labels = {
                str(label).strip()
                for label in (ticket.get('labels') or [])
                if str(label).strip()
            }

            derived_labels = {
                f'{label_prefix}-{self.CATEGORY_LABELS[finding.category]}'
                for finding in ticket_findings
                if finding.category in self.CATEGORY_LABELS
            }
            merged_labels = sorted(existing_labels | derived_labels)

            if merged_labels != sorted(existing_labels):
                update_action = DruckerAction(
                    action_id=f'D{action_index:03d}',
                    ticket_key=ticket_key,
                    action_type='update',
                    title='Apply Drucker hygiene labels',
                    description='Add Jira labels that reflect the hygiene issues detected for this ticket.',
                    finding_ids=[finding.finding_id for finding in ticket_findings],
                    confidence='high',
                    update_fields={'labels': merged_labels},
                )
                actions.append(update_action)
                for finding in ticket_findings:
                    finding.action_ids.append(update_action.action_id)
                action_index += 1

            comment_action = DruckerAction(
                action_id=f'D{action_index:03d}',
                ticket_key=ticket_key,
                action_type='comment',
                title='Post Drucker hygiene summary',
                description='Add a Jira comment summarizing the hygiene issues and recommended follow-up.',
                finding_ids=[finding.finding_id for finding in ticket_findings],
                confidence='medium',
                comment=self._build_comment(ticket, ticket_findings),
            )
            actions.append(comment_action)
            for finding in ticket_findings:
                finding.action_ids.append(comment_action.action_id)
            action_index += 1

        return actions

    def _build_summary(
        self,
        tickets: List[Dict[str, Any]],
        findings: List[DruckerFinding],
        actions: List[DruckerAction],
    ) -> Dict[str, Any]:
        category_counts = Counter(finding.category for finding in findings)
        severity_counts = Counter(finding.severity for finding in findings)
        open_tickets = sum(1 for ticket in tickets if not ticket.get('is_done'))
        tickets_with_findings = sorted({finding.ticket_key for finding in findings})

        return {
            'total_tickets': len(tickets),
            'open_tickets': open_tickets,
            'finding_count': len(findings),
            'action_count': len(actions),
            'tickets_with_findings': len(tickets_with_findings),
            'by_category': dict(category_counts),
            'by_severity': dict(severity_counts),
            'ticket_keys_with_findings': tickets_with_findings,
        }

    def _build_comment(
        self,
        ticket: Dict[str, Any],
        findings: List[DruckerFinding],
    ) -> str:
        titles = [finding.title for finding in findings]
        recommendations = [finding.recommendation for finding in findings]
        unique_recommendations = list(dict.fromkeys(recommendations))
        summary = str(ticket.get('summary') or '').strip()

        lines = [
            'Drucker hygiene review',
            '',
            f"Ticket: {ticket.get('key', '')} - {summary}",
            'Findings:',
        ]
        for finding in findings:
            lines.append(f"- {finding.title}: {finding.description}")

        if unique_recommendations:
            lines.append('')
            lines.append('Recommended follow-up:')
            for recommendation in unique_recommendations:
                lines.append(f'- {recommendation}')

        lines.append('')
        lines.append(
            f'Summary: {len(titles)} hygiene issue(s) identified for review.'
        )
        return '\n'.join(lines)

    def _format_report(self, report: DruckerHygieneReport) -> str:
        summary = report.summary
        findings_by_ticket: Dict[str, List[DruckerFinding]] = defaultdict(list)
        for finding in report.findings:
            findings_by_ticket[finding.ticket_key].append(finding)

        lines = [
            f'# DRUCKER HYGIENE REPORT: {report.project_key}',
            '',
            f'**Report ID**: {report.report_id}',
            f'**Created At**: {report.created_at}',
            '',
            '## Project Summary',
            '',
            f"- Project: {report.project_info.get('name', report.project_key)}",
            f"- Total tickets analyzed: {summary.get('total_tickets', 0)}",
            f"- Open tickets analyzed: {summary.get('open_tickets', 0)}",
            f"- Tickets with findings: {summary.get('tickets_with_findings', 0)}",
            f"- Findings: {summary.get('finding_count', 0)}",
            f"- Proposed actions: {summary.get('action_count', 0)}",
            '',
            '## Severity Breakdown',
            '',
        ]

        severity_counts = summary.get('by_severity', {})
        for severity in ('high', 'medium', 'low'):
            lines.append(f"- {severity.title()}: {int(severity_counts.get(severity, 0) or 0)}")

        lines.extend([
            '',
            '## Finding Categories',
            '',
        ])
        for category, count in sorted((summary.get('by_category') or {}).items()):
            lines.append(f'- {category}: {count}')

        lines.extend([
            '',
            '## Ticket Remediation Suggestions',
            '',
        ])

        if findings_by_ticket:
            tickets_by_key = {
                str(ticket.get('key') or ''): ticket
                for ticket in report.tickets
            }
            for ticket_key in sorted(findings_by_ticket):
                ticket = tickets_by_key.get(ticket_key, {})
                lines.append(
                    f"- **{ticket_key}** {ticket.get('summary', '')}".rstrip()
                )
                for finding in findings_by_ticket[ticket_key]:
                    lines.append(
                        f"  [{finding.severity.upper()}] {finding.title}: {finding.recommendation}"
                    )
        else:
            lines.append('- No hygiene issues were detected for the current Jira scope.')

        lines.extend([
            '',
            '## Proposed Jira Actions',
            '',
        ])

        if report.proposed_actions:
            for action in report.proposed_actions:
                lines.append(
                    f"- [{action.action_type.upper()}] {action.ticket_key}: {action.title}"
                )
                if action.action_type == 'update' and action.update_fields.get('labels'):
                    lines.append(
                        f"  Labels: {', '.join(action.update_fields['labels'])}"
                    )
        else:
            lines.append('- No Jira write-back actions proposed.')

        if report.errors:
            lines.extend([
                '',
                '## Errors',
                '',
            ])
            for error in report.errors:
                lines.append(f'- {error}')

        return '\n'.join(lines)

    @staticmethod
    def _parse_jira_datetime(value: str) -> Optional[datetime]:
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
    def _is_done_status(status: str) -> bool:
        return str(status).casefold() in {'done', 'closed', 'resolved'}

    @staticmethod
    def _is_blocked_status(status: str) -> bool:
        normalized = str(status).casefold()
        return any(token in normalized for token in ('blocked', 'on hold', 'impeded'))

    @staticmethod
    def _is_high_priority(priority: str) -> bool:
        normalized = str(priority).casefold()
        return any(
            token in normalized
            for token in ('blocker', 'critical', 'highest', 'high', 'p0', 'p1')
        )
