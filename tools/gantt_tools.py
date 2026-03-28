##########################################################################################
#
# Module: tools/gantt_tools.py
#
# Description: Gantt planning tools for agent use.
#              Wraps the Gantt planning snapshot workflow as agent-callable tools.
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
    description='Create a Gantt planning snapshot from Jira backlog state'
)
def create_gantt_snapshot(
    project_key: str,
    planning_horizon_days: int = 90,
    limit: int = 200,
    include_done: bool = False,
    backlog_jql: Optional[str] = None,
    policy_profile: str = 'default',
    evidence_paths: Optional[list[str]] = None,
    persist: bool = True,
) -> ToolResult:
    '''
    Create a Gantt planning snapshot from Jira backlog state.

    Input:
        project_key: Jira project key to snapshot.
        planning_horizon_days: Planning horizon in days.
        limit: Maximum number of issues to inspect.
        include_done: Whether to include done/closed issues.
        backlog_jql: Optional JQL override for backlog selection.
        policy_profile: Optional future-facing planning policy profile.
        evidence_paths: Optional build/test/release/meeting evidence files.
        persist: Whether to save the snapshot in the durable snapshot store.

    Output:
        ToolResult with the generated snapshot and optional storage metadata.
    '''
    log.debug(
        f'create_gantt_snapshot(project_key={project_key}, '
        f'planning_horizon_days={planning_horizon_days}, limit={limit}, '
        f'include_done={include_done}, backlog_jql={backlog_jql}, '
        f'policy_profile={policy_profile}, evidence_paths={evidence_paths}, '
        f'persist={persist})'
    )

    try:
        from agents.gantt_agent import GanttProjectPlannerAgent
        from agents.gantt_models import PlanningRequest
        from state.gantt_snapshot_store import GanttSnapshotStore

        agent = GanttProjectPlannerAgent(project_key=project_key)
        request = PlanningRequest(
            project_key=project_key,
            planning_horizon_days=planning_horizon_days,
            limit=limit,
            include_done=include_done,
            backlog_jql=backlog_jql,
            policy_profile=policy_profile,
            evidence_paths=list(evidence_paths or []),
        )
        snapshot = agent.create_snapshot(request)

        result = {
            'snapshot': snapshot.to_dict(),
        }

        if persist:
            stored = GanttSnapshotStore().save_snapshot(
                snapshot,
                summary_markdown=snapshot.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            snapshot_id=snapshot.snapshot_id,
            project_key=project_key,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create Gantt snapshot: {e}')
        return ToolResult.failure(f'Failed to create Gantt snapshot: {e}')


@tool(
    description='Get a persisted Gantt planning snapshot by snapshot ID'
)
def get_gantt_snapshot(
    snapshot_id: str,
    project_key: Optional[str] = None,
) -> ToolResult:
    '''
    Get a persisted Gantt planning snapshot by snapshot ID.

    Input:
        snapshot_id: Stored snapshot ID.
        project_key: Optional project key to disambiguate the lookup.

    Output:
        ToolResult with the stored snapshot payload and storage summary.
    '''
    log.debug(f'get_gantt_snapshot(snapshot_id={snapshot_id}, project_key={project_key})')

    try:
        from state.gantt_snapshot_store import GanttSnapshotStore

        record = GanttSnapshotStore().get_snapshot(snapshot_id, project_key=project_key)
        if not record:
            return ToolResult.failure(f'Gantt snapshot {snapshot_id} not found')

        return ToolResult.success(record, snapshot_id=snapshot_id, project_key=project_key)
    except Exception as e:
        log.error(f'Failed to get Gantt snapshot: {e}')
        return ToolResult.failure(f'Failed to get Gantt snapshot: {e}')


@tool(
    description='List persisted Gantt planning snapshots'
)
def list_gantt_snapshots(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Gantt planning snapshots.

    Input:
        project_key: Optional project key filter.
        limit: Maximum number of snapshots to return.

    Output:
        ToolResult with snapshot summary rows.
    '''
    log.debug(f'list_gantt_snapshots(project_key={project_key}, limit={limit})')

    try:
        from state.gantt_snapshot_store import GanttSnapshotStore

        rows = GanttSnapshotStore().list_snapshots(project_key=project_key, limit=limit)
        return ToolResult.success(rows, count=len(rows), project_key=project_key)
    except Exception as e:
        log.error(f'Failed to list Gantt snapshots: {e}')
        return ToolResult.failure(f'Failed to list Gantt snapshots: {e}')


@tool(
    description='Accept or reject an inferred Gantt dependency edge'
)
def review_gantt_dependency(
    project_key: str,
    source_key: str,
    target_key: str,
    relationship: str = 'blocks',
    accepted: bool = True,
    note: Optional[str] = None,
    reviewer: Optional[str] = None,
) -> ToolResult:
    '''
    Accept or reject an inferred Gantt dependency edge.

    Input:
        project_key: Jira project key for the planning graph.
        source_key: Upstream issue key.
        target_key: Downstream issue key.
        relationship: Dependency relationship, usually ``blocks``.
        accepted: Whether the inferred dependency is accepted.
        note: Optional review note.
        reviewer: Optional reviewer identifier.

    Output:
        ToolResult with the stored review record.
    '''
    log.debug(
        f'review_gantt_dependency(project_key={project_key}, '
        f'source_key={source_key}, target_key={target_key}, '
        f'relationship={relationship}, accepted={accepted}, reviewer={reviewer})'
    )

    try:
        from state.gantt_dependency_review_store import GanttDependencyReviewStore

        record = GanttDependencyReviewStore().record_review(
            project_key=project_key,
            source_key=source_key,
            target_key=target_key,
            relationship=relationship,
            accepted=accepted,
            note=note,
            reviewer=reviewer,
        )
        return ToolResult.success(
            record,
            project_key=project_key,
            source_key=source_key,
            target_key=target_key,
            relationship=relationship,
            status=record['status'],
        )
    except Exception as e:
        log.error(f'Failed to review Gantt dependency: {e}')
        return ToolResult.failure(f'Failed to review Gantt dependency: {e}')


@tool(
    description='List stored Gantt dependency review decisions'
)
def list_gantt_dependency_reviews(
    project_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List stored Gantt dependency review decisions.

    Input:
        project_key: Optional Jira project key filter.
        status: Optional status filter (``accepted`` or ``rejected``).
        limit: Maximum number of records to return.

    Output:
        ToolResult with dependency review rows.
    '''
    log.debug(
        f'list_gantt_dependency_reviews(project_key={project_key}, '
        f'status={status}, limit={limit})'
    )

    try:
        from state.gantt_dependency_review_store import GanttDependencyReviewStore

        rows = GanttDependencyReviewStore().list_reviews(
            project_key=project_key,
            status=status,
            limit=limit,
        )
        return ToolResult.success(
            rows,
            count=len(rows),
            project_key=project_key,
            status=status,
        )
    except Exception as e:
        log.error(f'Failed to list Gantt dependency reviews: {e}')
        return ToolResult.failure(f'Failed to list Gantt dependency reviews: {e}')


# ===========================================================================
# Roadmap Analysis Tools
# ===========================================================================


@tool(
    description='Create a roadmap analysis snapshot from Jira initiative hierarchy'
)
def create_roadmap_snapshot(
    project_key: str = 'STL',
    scope_label: str = '',
    initiative_keys: Optional[str] = None,
    fix_versions: Optional[str] = None,
    hierarchy_depth: int = 3,
    include_closed: bool = False,
    output_file: Optional[str] = None,
    include_gap_analysis: bool = True,
    persist: bool = True,
    show_priority: bool = True,
    blank_unassigned: bool = True,
    bold_stories: bool = True,
) -> ToolResult:
    '''
    Create a roadmap analysis snapshot from Jira initiative hierarchy.

    Fetches initiatives, epics, and stories under the given scope label,
    runs optional LLM gap analysis, and produces an xlsx roadmap artifact.

    Input:
        project_key: Jira project key (default "STL").
        scope_label: Required scope label filter (e.g. "CN6000", "CN5000").
        initiative_keys: Optional comma-separated initiative ticket keys
                         to anchor on (e.g. "STL-1234,STL-5678").
        fix_versions: Optional comma-separated fix version patterns
                      (e.g. "12.2.0.x,14.0.0.x").
        hierarchy_depth: How deep to traverse the hierarchy
                         (0=Initiative, 1=Epic, 2=Story, default 3).
        include_closed: Whether to include closed/done tickets.
        output_file: Path for xlsx output. Defaults to
                     "{scope_label}_combined_roadmap.xlsx".
        include_gap_analysis: Whether to run LLM gap analysis (default True).
        persist: Whether to save the snapshot in the durable snapshot store
                 (default True).

    Output:
        ToolResult with the generated snapshot summary and optional
        storage metadata.
    '''
    log.debug(
        f'create_roadmap_snapshot(project_key={project_key}, '
        f'scope_label={scope_label}, initiative_keys={initiative_keys}, '
        f'fix_versions={fix_versions}, hierarchy_depth={hierarchy_depth}, '
        f'include_closed={include_closed}, output_file={output_file}, '
        f'include_gap_analysis={include_gap_analysis}, persist={persist})'
    )

    try:
        from agents.gantt_agent import GanttProjectPlannerAgent
        from agents.gantt_models import RoadmapRequest
        from state.roadmap_snapshot_store import RoadmapSnapshotStore

        # Parse comma-separated strings into lists
        parsed_initiative_keys = (
            [k.strip() for k in initiative_keys.split(',') if k.strip()]
            if initiative_keys else None
        )
        parsed_fix_versions = (
            [v.strip() for v in fix_versions.split(',') if v.strip()]
            if fix_versions else None
        )

        # Default output file based on scope label
        resolved_output_file = output_file or f'{scope_label}_combined_roadmap.xlsx'

        request = RoadmapRequest(
            project_key=project_key,
            scope_label=scope_label,
            initiative_keys=parsed_initiative_keys,
            fix_versions=parsed_fix_versions,
            hierarchy_depth=hierarchy_depth,
            include_closed=include_closed,
            output_file=resolved_output_file,
            include_gap_analysis=include_gap_analysis,
            show_priority=show_priority,
            blank_unassigned=blank_unassigned,
            bold_stories=bold_stories,
        )

        agent = GanttProjectPlannerAgent(project_key=project_key)
        snapshot = agent.create_roadmap_snapshot(request)

        result = {
            'snapshot': snapshot.to_dict(),
        }

        if persist:
            stored = RoadmapSnapshotStore().save_snapshot(
                snapshot.to_dict(),
                summary_markdown=snapshot.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            snapshot_id=snapshot.snapshot_id,
            project_key=project_key,
            scope_label=scope_label,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create roadmap snapshot: {e}')
        return ToolResult.failure(f'Failed to create roadmap snapshot: {e}')


@tool(
    description='Get a persisted roadmap snapshot by project key and snapshot ID'
)
def get_roadmap_snapshot(
    project_key: str,
    snapshot_id: str,
) -> ToolResult:
    '''
    Get a persisted roadmap snapshot by project key and snapshot ID.

    Input:
        project_key: Jira project key (e.g. "STL").
        snapshot_id: Stored snapshot ID.

    Output:
        ToolResult with the stored snapshot payload and storage summary.
    '''
    log.debug(
        f'get_roadmap_snapshot(project_key={project_key}, '
        f'snapshot_id={snapshot_id})'
    )

    try:
        from state.roadmap_snapshot_store import RoadmapSnapshotStore

        record = RoadmapSnapshotStore().get_snapshot(
            project_key=project_key,
            snapshot_id=snapshot_id,
        )
        if not record:
            return ToolResult.failure(
                f'Roadmap snapshot {snapshot_id} not found '
                f'for project {project_key}'
            )

        return ToolResult.success(
            record,
            snapshot_id=snapshot_id,
            project_key=project_key,
        )
    except Exception as e:
        log.error(f'Failed to get roadmap snapshot: {e}')
        return ToolResult.failure(f'Failed to get roadmap snapshot: {e}')


@tool(
    description='List persisted roadmap analysis snapshots'
)
def list_roadmap_snapshots(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted roadmap analysis snapshots.

    Input:
        project_key: Optional Jira project key filter.
        limit: Maximum number of snapshots to return (default 20).

    Output:
        ToolResult with snapshot summary rows sorted newest-first.
    '''
    log.debug(
        f'list_roadmap_snapshots(project_key={project_key}, limit={limit})'
    )

    try:
        from state.roadmap_snapshot_store import RoadmapSnapshotStore

        rows = RoadmapSnapshotStore().list_snapshots(
            project_key=project_key,
            limit=limit,
        )
        return ToolResult.success(
            rows,
            count=len(rows),
            project_key=project_key,
        )
    except Exception as e:
        log.error(f'Failed to list roadmap snapshots: {e}')
        return ToolResult.failure(f'Failed to list roadmap snapshots: {e}')


# ===========================================================================
# Release Monitor Tools
# ===========================================================================


@tool(
    description='Generate a release health monitoring report'
)
def create_release_monitor(
    project_key: str = 'STL',
    releases: Optional[str] = None,
    scope_label: Optional[str] = None,
    include_gap_analysis: bool = True,
    include_bug_report: bool = True,
    include_velocity: bool = True,
    include_readiness: bool = True,
    compare_to_previous: bool = True,
    output_file: Optional[str] = None,
    persist: bool = True,
) -> ToolResult:
    '''
    Generate a release health monitoring report.

    Analyzes the current state of one or more releases: bug counts by
    status/priority, velocity trends, readiness assessment, delta from
    previous snapshot, and roadmap gap analysis.

    Input:
        project_key: Jira project key (default "STL").
        releases: Comma-separated fix version names to monitor
                  (e.g. "12.2.0.x, 14.0.0.x"). If empty, monitors all
                  unreleased versions.
        scope_label: Optional keyword to filter tickets (e.g. "CN6000").
        include_gap_analysis: Run roadmap gap analysis on the release scope.
        include_bug_report: Include bug status/priority breakdown.
        include_velocity: Compute velocity and throughput metrics.
        include_readiness: Run release readiness assessment.
        compare_to_previous: Compare against previous snapshot for delta.
        output_file: Output xlsx path (defaults to
                     "{project_key}_release_monitor.xlsx").
        persist: Save report for historical tracking.

    Output:
        ToolResult with the generated release monitor report and optional
        storage metadata.
    '''
    log.debug(
        f'create_release_monitor(project_key={project_key}, '
        f'releases={releases}, scope_label={scope_label}, '
        f'include_gap_analysis={include_gap_analysis}, '
        f'include_bug_report={include_bug_report}, '
        f'include_velocity={include_velocity}, '
        f'include_readiness={include_readiness}, '
        f'compare_to_previous={compare_to_previous}, '
        f'output_file={output_file}, persist={persist})'
    )

    try:
        from agents.gantt_agent import GanttProjectPlannerAgent
        from agents.gantt_models import ReleaseMonitorRequest
        from state.gantt_release_monitor_store import GanttReleaseMonitorStore

        # Parse comma-separated releases string into list
        parsed_releases = (
            [r.strip() for r in releases.split(',') if r.strip()]
            if releases else None
        )

        # Default output file based on project key
        resolved_output_file = (
            output_file or f'{project_key}_release_monitor.xlsx'
        )

        request = ReleaseMonitorRequest(
            project_key=project_key,
            releases=parsed_releases,
            scope_label=scope_label or '',
            include_gap_analysis=include_gap_analysis,
            include_bug_report=include_bug_report,
            include_velocity=include_velocity,
            include_readiness=include_readiness,
            compare_to_previous=compare_to_previous,
            output_file=resolved_output_file,
        )

        agent = GanttProjectPlannerAgent(project_key=project_key)
        report = agent.create_release_monitor(request)

        result = {
            'report': report.to_dict(),
        }

        if persist:
            stored = GanttReleaseMonitorStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            report_id=report.report_id,
            project_key=project_key,
            releases=parsed_releases,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create release monitor report: {e}')
        return ToolResult.failure(
            f'Failed to create release monitor report: {e}'
        )


@tool(
    description='Get a persisted Gantt release-monitor report by report ID'
)
def get_gantt_release_monitor_report(
    report_id: str,
    project_key: Optional[str] = None,
) -> ToolResult:
    '''
    Get a persisted Gantt release-monitor report by report ID.
    '''
    log.debug(
        f'get_gantt_release_monitor_report(report_id={report_id}, '
        f'project_key={project_key})'
    )

    try:
        from state.gantt_release_monitor_store import GanttReleaseMonitorStore

        record = GanttReleaseMonitorStore().get_report(
            report_id,
            project_key=project_key,
        )
        if not record:
            return ToolResult.failure(
                f'Gantt release monitor report {report_id} not found'
            )

        return ToolResult.success(
            record,
            report_id=report_id,
            project_key=project_key,
        )
    except Exception as e:
        log.error(f'Failed to get Gantt release monitor report: {e}')
        return ToolResult.failure(
            f'Failed to get Gantt release monitor report: {e}'
        )


@tool(
    description='List persisted Gantt release-monitor reports'
)
def list_gantt_release_monitor_reports(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Gantt release-monitor reports.
    '''
    log.debug(
        f'list_gantt_release_monitor_reports(project_key={project_key}, '
        f'limit={limit})'
    )

    try:
        from state.gantt_release_monitor_store import GanttReleaseMonitorStore

        rows = GanttReleaseMonitorStore().list_reports(
            project_key=project_key,
            limit=limit,
        )
        return ToolResult.success(rows, count=len(rows), project_key=project_key)
    except Exception as e:
        log.error(f'Failed to list Gantt release monitor reports: {e}')
        return ToolResult.failure(
            f'Failed to list Gantt release monitor reports: {e}'
        )


@tool(
    description='Generate a release execution survey focused on done, active, and remaining work'
)
def create_release_survey(
    project_key: str = 'STL',
    releases: Optional[str] = None,
    scope_label: Optional[str] = None,
    survey_mode: str = 'feature_dev',
    output_file: Optional[str] = None,
    persist: bool = True,
) -> ToolResult:
    '''
    Generate a Gantt release execution survey.

    Input:
        project_key: Jira project key (default "STL").
        releases: Comma-separated fix version names to survey.
        scope_label: Optional scope label filter, accepts CSV values
                     (for example "CN5000,CN6000").
        survey_mode: 'feature_dev' excludes bugs; 'bug' includes only bugs.
        output_file: Output xlsx path (defaults to
                     "{project_key}_release_survey.xlsx").
        persist: Save the survey for later retrieval.

    Output:
        ToolResult with the generated release survey and optional storage metadata.
    '''
    log.debug(
        f'create_release_survey(project_key={project_key}, '
        f'releases={releases}, scope_label={scope_label}, '
        f'survey_mode={survey_mode}, '
        f'output_file={output_file}, persist={persist})'
    )

    try:
        from agents.gantt_agent import GanttProjectPlannerAgent
        from agents.gantt_models import ReleaseSurveyRequest
        from state.gantt_release_survey_store import GanttReleaseSurveyStore

        parsed_releases = (
            [r.strip() for r in releases.split(',') if r.strip()]
            if releases else None
        )
        resolved_output_file = output_file or f'{project_key}_release_survey.xlsx'

        request = ReleaseSurveyRequest(
            project_key=project_key,
            releases=parsed_releases,
            scope_label=scope_label or '',
            survey_mode=survey_mode,
            output_file=resolved_output_file,
        )

        agent = GanttProjectPlannerAgent(project_key=project_key)
        survey = agent.create_release_survey(request)

        result = {
            'survey': survey.to_dict(),
        }

        if persist:
            stored = GanttReleaseSurveyStore().save_survey(
                survey,
                summary_markdown=survey.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            survey_id=survey.survey_id,
            project_key=project_key,
            releases=parsed_releases,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to create release survey: {e}')
        return ToolResult.failure(f'Failed to create release survey: {e}')


@tool(
    description='Get a persisted Gantt release-survey report by survey ID'
)
def get_gantt_release_survey(
    survey_id: str,
    project_key: Optional[str] = None,
) -> ToolResult:
    '''
    Get a persisted Gantt release-survey report by survey ID.
    '''
    log.debug(
        f'get_gantt_release_survey(survey_id={survey_id}, '
        f'project_key={project_key})'
    )

    try:
        from state.gantt_release_survey_store import GanttReleaseSurveyStore

        record = GanttReleaseSurveyStore().get_survey(
            survey_id,
            project_key=project_key,
        )
        if not record:
            return ToolResult.failure(
                f'Gantt release survey {survey_id} not found'
            )

        return ToolResult.success(
            record,
            survey_id=survey_id,
            project_key=project_key,
        )
    except Exception as e:
        log.error(f'Failed to get Gantt release survey: {e}')
        return ToolResult.failure(f'Failed to get Gantt release survey: {e}')


@tool(
    description='List persisted Gantt release-survey reports'
)
def list_gantt_release_surveys(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Gantt release-survey reports.
    '''
    log.debug(
        f'list_gantt_release_surveys(project_key={project_key}, '
        f'limit={limit})'
    )

    try:
        from state.gantt_release_survey_store import GanttReleaseSurveyStore

        rows = GanttReleaseSurveyStore().list_surveys(
            project_key=project_key,
            limit=limit,
        )
        return ToolResult.success(rows, count=len(rows), project_key=project_key)
    except Exception as e:
        log.error(f'Failed to list Gantt release surveys: {e}')
        return ToolResult.failure(f'Failed to list Gantt release surveys: {e}')


class GanttTools(BaseTool):
    '''
    Collection of Gantt planning tools for agent use.
    '''

    @tool(description='Create a Gantt planning snapshot from Jira backlog state')
    def create_gantt_snapshot(
        self,
        project_key: str,
        planning_horizon_days: int = 90,
        limit: int = 200,
        include_done: bool = False,
        backlog_jql: Optional[str] = None,
        policy_profile: str = 'default',
        evidence_paths: Optional[list[str]] = None,
        persist: bool = True,
    ) -> ToolResult:
        return create_gantt_snapshot(
            project_key,
            planning_horizon_days,
            limit,
            include_done,
            backlog_jql,
            policy_profile,
            evidence_paths,
            persist,
        )

    @tool(description='Get a persisted Gantt planning snapshot by snapshot ID')
    def get_gantt_snapshot(
        self,
        snapshot_id: str,
        project_key: Optional[str] = None,
    ) -> ToolResult:
        return get_gantt_snapshot(snapshot_id, project_key)

    @tool(description='List persisted Gantt planning snapshots')
    def list_gantt_snapshots(
        self,
        project_key: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_gantt_snapshots(project_key, limit)

    @tool(description='Accept or reject an inferred Gantt dependency edge')
    def review_gantt_dependency(
        self,
        project_key: str,
        source_key: str,
        target_key: str,
        relationship: str = 'blocks',
        accepted: bool = True,
        note: Optional[str] = None,
        reviewer: Optional[str] = None,
    ) -> ToolResult:
        return review_gantt_dependency(
            project_key,
            source_key,
            target_key,
            relationship,
            accepted,
            note,
            reviewer,
        )

    @tool(description='List stored Gantt dependency review decisions')
    def list_gantt_dependency_reviews(
        self,
        project_key: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_gantt_dependency_reviews(project_key, status, limit)

    @tool(description='Create a roadmap analysis snapshot from Jira initiative hierarchy')
    def create_roadmap_snapshot(
        self,
        project_key: str = 'STL',
        scope_label: str = '',
        initiative_keys: Optional[str] = None,
        fix_versions: Optional[str] = None,
        hierarchy_depth: int = 3,
        include_closed: bool = False,
        output_file: Optional[str] = None,
        include_gap_analysis: bool = True,
        persist: bool = True,
        show_priority: bool = True,
        blank_unassigned: bool = True,
        bold_stories: bool = True,
    ) -> ToolResult:
        return create_roadmap_snapshot(
            project_key,
            scope_label,
            initiative_keys,
            fix_versions,
            hierarchy_depth,
            include_closed,
            output_file,
            include_gap_analysis,
            persist,
            show_priority,
            blank_unassigned,
            bold_stories,
        )

    @tool(description='Get a persisted roadmap snapshot by project key and snapshot ID')
    def get_roadmap_snapshot(
        self,
        project_key: str,
        snapshot_id: str,
    ) -> ToolResult:
        return get_roadmap_snapshot(project_key, snapshot_id)

    @tool(description='List persisted roadmap analysis snapshots')
    def list_roadmap_snapshots(
        self,
        project_key: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_roadmap_snapshots(project_key, limit)

    @tool(description='Generate a release health monitoring report')
    def create_release_monitor(
        self,
        project_key: str = 'STL',
        releases: Optional[str] = None,
        scope_label: Optional[str] = None,
        include_gap_analysis: bool = True,
        include_bug_report: bool = True,
        include_velocity: bool = True,
        include_readiness: bool = True,
        compare_to_previous: bool = True,
        output_file: Optional[str] = None,
        persist: bool = True,
    ) -> ToolResult:
        return create_release_monitor(
            project_key,
            releases,
            scope_label,
            include_gap_analysis,
            include_bug_report,
            include_velocity,
            include_readiness,
            compare_to_previous,
            output_file,
            persist,
        )

    @tool(description='Get a persisted Gantt release-monitor report by report ID')
    def get_gantt_release_monitor_report(
        self,
        report_id: str,
        project_key: Optional[str] = None,
    ) -> ToolResult:
        return get_gantt_release_monitor_report(report_id, project_key)

    @tool(description='List persisted Gantt release-monitor reports')
    def list_gantt_release_monitor_reports(
        self,
        project_key: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_gantt_release_monitor_reports(project_key, limit)

    @tool(description='Generate a release execution survey focused on done, active, and remaining work')
    def create_release_survey(
        self,
        project_key: str = 'STL',
        releases: Optional[str] = None,
        scope_label: Optional[str] = None,
        survey_mode: str = 'feature_dev',
        output_file: Optional[str] = None,
        persist: bool = True,
    ) -> ToolResult:
        return create_release_survey(
            project_key,
            releases,
            scope_label,
            survey_mode,
            output_file,
            persist,
        )

    @tool(description='Get a persisted Gantt release-survey report by survey ID')
    def get_gantt_release_survey(
        self,
        survey_id: str,
        project_key: Optional[str] = None,
    ) -> ToolResult:
        return get_gantt_release_survey(survey_id, project_key)

    @tool(description='List persisted Gantt release-survey reports')
    def list_gantt_release_surveys(
        self,
        project_key: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_gantt_release_surveys(project_key, limit)
