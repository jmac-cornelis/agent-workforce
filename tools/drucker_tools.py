##########################################################################################
#
# Module: tools/drucker_tools.py
#
# Description: Drucker hygiene tools for agent use.
#              Wraps the Drucker hygiene workflow as agent-callable tools.
#
# Author: Cornelis Networks
#
##########################################################################################

import logging
import os
import sys
from typing import Optional

from tools.base import BaseTool, ToolResult, tool

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


@tool(
    description='Create a Drucker Jira hygiene report and optional durable record'
)
def create_drucker_hygiene_report(
    project_key: str,
    limit: int = 200,
    include_done: bool = False,
    stale_days: int = 30,
    jql: Optional[str] = None,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> ToolResult:
    '''
    Create a Drucker Jira hygiene report and optional durable record.
    '''
    log.debug(
        f'create_drucker_hygiene_report(project_key={project_key}, limit={limit}, '
        f'include_done={include_done}, stale_days={stale_days}, jql={jql}, '
        f'label_prefix={label_prefix}, persist={persist})'
    )

    try:
        from agents.drucker_agent import DruckerCoordinatorAgent
        from agents.drucker_models import DruckerRequest
        from state.drucker_report_store import DruckerReportStore

        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            limit=limit,
            include_done=include_done,
            stale_days=stale_days,
            jql=jql,
            label_prefix=label_prefix,
        )
        report = agent.analyze_project_hygiene(request)
        review_session = agent.create_review_session(report)

        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }

        if persist:
            stored = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            report_id=report.report_id,
            project_key=project_key,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create Drucker hygiene report: {e}')
        return ToolResult.failure(f'Failed to create Drucker hygiene report: {e}')


@tool(
    description='Run a Drucker issue-check for a specific Jira ticket'
)
def create_drucker_issue_check(
    project_key: str,
    ticket_key: str,
    stale_days: int = 30,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> ToolResult:
    '''
    Run a Drucker issue-check for a specific Jira ticket.
    '''
    log.debug(
        f'create_drucker_issue_check(project_key={project_key}, ticket_key={ticket_key}, '
        f'stale_days={stale_days}, label_prefix={label_prefix}, persist={persist})'
    )

    try:
        from agents.drucker_agent import DruckerCoordinatorAgent
        from agents.drucker_models import DruckerRequest
        from state.drucker_report_store import DruckerReportStore

        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            ticket_key=ticket_key,
            stale_days=stale_days,
            label_prefix=label_prefix,
        )
        report = agent.analyze_ticket_hygiene(request)
        review_session = agent.create_review_session(report)

        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }

        if persist:
            stored = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            report_id=report.report_id,
            project_key=project_key,
            ticket_key=ticket_key,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create Drucker issue check: {e}')
        return ToolResult.failure(f'Failed to create Drucker issue check: {e}')


@tool(
    description='Create a Drucker recent-ticket intake report and optional durable record'
)
def create_drucker_intake_report(
    project_key: str,
    limit: int = 200,
    stale_days: int = 30,
    since: Optional[str] = None,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> ToolResult:
    '''
    Run a Drucker recent-ticket intake report and optional durable record.
    '''
    log.debug(
        f'create_drucker_intake_report(project_key={project_key}, limit={limit}, '
        f'stale_days={stale_days}, since={since}, label_prefix={label_prefix}, '
        f'persist={persist})'
    )

    try:
        from agents.drucker_agent import DruckerCoordinatorAgent
        from agents.drucker_models import DruckerRequest
        from state.drucker_report_store import DruckerReportStore

        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            limit=limit,
            stale_days=stale_days,
            since=since,
            recent_only=True,
            label_prefix=label_prefix,
        )
        report = agent.analyze_recent_ticket_intake(request)
        review_session = agent.create_review_session(report)

        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }

        if persist:
            stored = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            report_id=report.report_id,
            project_key=project_key,
            persisted=persist,
            monitor_scope='recent_ticket_intake',
        )
    except Exception as e:
        log.error(f'Failed to create Drucker intake report: {e}')
        return ToolResult.failure(f'Failed to create Drucker intake report: {e}')


@tool(
    description='Create a Drucker bug activity report for a specific date'
)
def create_drucker_bug_activity_report(
    project_key: str,
    target_date: Optional[str] = None,
) -> ToolResult:
    '''
    Run a Drucker bug activity report for a specific date.
    '''
    log.debug(
        f'create_drucker_bug_activity_report(project_key={project_key}, '
        f'target_date={target_date})'
    )

    try:
        from agents.drucker_agent import DruckerCoordinatorAgent

        agent = DruckerCoordinatorAgent(project_key=project_key)
        activity = agent.analyze_bug_activity(
            project_key=project_key,
            target_date=target_date,
        )

        return ToolResult.success(
            activity,
            project_key=project_key,
            target_date=activity.get('date'),
        )
    except Exception as e:
        log.error(f'Failed to create Drucker bug activity report: {e}')
        return ToolResult.failure(
            f'Failed to create Drucker bug activity report: {e}'
        )


@tool(
    description='Get a persisted Drucker hygiene report by report ID'
)
def get_drucker_report(
    report_id: str,
    project_key: Optional[str] = None,
) -> ToolResult:
    '''
    Get a persisted Drucker hygiene report by report ID.
    '''
    log.debug(f'get_drucker_report(report_id={report_id}, project_key={project_key})')

    try:
        from state.drucker_report_store import DruckerReportStore

        record = DruckerReportStore().get_report(report_id, project_key=project_key)
        if not record:
            return ToolResult.failure(f'Drucker report {report_id} not found')

        return ToolResult.success(record, report_id=report_id, project_key=project_key)
    except Exception as e:
        log.error(f'Failed to get Drucker report: {e}')
        return ToolResult.failure(f'Failed to get Drucker report: {e}')


@tool(
    description='List persisted Drucker hygiene reports'
)
def list_drucker_reports(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Drucker hygiene reports.
    '''
    log.debug(f'list_drucker_reports(project_key={project_key}, limit={limit})')

    try:
        from state.drucker_report_store import DruckerReportStore

        rows = DruckerReportStore().list_reports(project_key=project_key, limit=limit)
        return ToolResult.success(rows, count=len(rows), project_key=project_key)
    except Exception as e:
        log.error(f'Failed to list Drucker reports: {e}')
        return ToolResult.failure(f'Failed to list Drucker reports: {e}')


class DruckerTools(BaseTool):
    '''
    Collection of Drucker hygiene tools for agent use.
    '''

    @tool(description='Run a Drucker issue-check for a specific Jira ticket')
    def create_drucker_issue_check(
        self,
        project_key: str,
        ticket_key: str,
        stale_days: int = 30,
        label_prefix: str = 'drucker',
        persist: bool = True,
    ) -> ToolResult:
        return create_drucker_issue_check(
            project_key=project_key,
            ticket_key=ticket_key,
            stale_days=stale_days,
            label_prefix=label_prefix,
            persist=persist,
        )

    @tool(description='Create a Drucker Jira hygiene report')
    def create_drucker_hygiene_report(
        self,
        project_key: str,
        limit: int = 200,
        include_done: bool = False,
        stale_days: int = 30,
        jql: Optional[str] = None,
        label_prefix: str = 'drucker',
        persist: bool = True,
    ) -> ToolResult:
        return create_drucker_hygiene_report(
            project_key=project_key,
            limit=limit,
            include_done=include_done,
            stale_days=stale_days,
            jql=jql,
            label_prefix=label_prefix,
            persist=persist,
        )

    @tool(description='Create a Drucker recent-ticket intake report')
    def create_drucker_intake_report(
        self,
        project_key: str,
        limit: int = 200,
        stale_days: int = 30,
        since: Optional[str] = None,
        label_prefix: str = 'drucker',
        persist: bool = True,
    ) -> ToolResult:
        return create_drucker_intake_report(
            project_key=project_key,
            limit=limit,
            stale_days=stale_days,
            since=since,
            label_prefix=label_prefix,
            persist=persist,
        )

    @tool(description='Create a Drucker bug activity report')
    def create_drucker_bug_activity_report(
        self,
        project_key: str,
        target_date: Optional[str] = None,
    ) -> ToolResult:
        return create_drucker_bug_activity_report(
            project_key=project_key,
            target_date=target_date,
        )

    @tool(description='Get a persisted Drucker hygiene report by report ID')
    def get_drucker_report(
        self,
        report_id: str,
        project_key: Optional[str] = None,
    ) -> ToolResult:
        return get_drucker_report(report_id, project_key)

    @tool(description='List persisted Drucker hygiene reports')
    def list_drucker_reports(
        self,
        project_key: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_drucker_reports(project_key, limit)
