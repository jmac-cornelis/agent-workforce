##########################################################################################
#
# Module: agents/gantt_models.py
#
# Description: Data models for the Gantt Project Planner and Roadmap Analyzer agents.
#              Defines structured planning snapshot, milestone, dependency,
#              and risk records used by the Gantt planning workflow, plus
#              roadmap request, item, gap, section, and snapshot models
#              used by the roadmap analysis workflow.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


@dataclass
class PlanningRequest:
    '''
    Input request for generating a planning snapshot.
    '''
    project_key: str = ''
    planning_horizon_days: int = 90
    limit: int = 200
    include_done: bool = False
    backlog_jql: Optional[str] = None
    policy_profile: str = 'default'
    evidence_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_key': self.project_key,
            'planning_horizon_days': self.planning_horizon_days,
            'limit': self.limit,
            'include_done': self.include_done,
            'backlog_jql': self.backlog_jql,
            'policy_profile': self.policy_profile,
            'evidence_paths': self.evidence_paths,
        }


@dataclass
class DependencyEdge:
    '''
    A single dependency relationship between two work items.
    '''
    source_key: str
    target_key: str
    relationship: str
    inferred: bool = False
    evidence: str = ''
    confidence: str = 'high'
    rule_id: str = ''
    review_state: str = 'accepted'
    rationale: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_key': self.source_key,
            'target_key': self.target_key,
            'relationship': self.relationship,
            'inferred': self.inferred,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'rule_id': self.rule_id,
            'review_state': self.review_state,
            'rationale': self.rationale,
        }


@dataclass
class DependencyGraph:
    '''
    Directed dependency graph for a project backlog.
    '''
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[DependencyEdge] = field(default_factory=list)
    blocked_keys: List[str] = field(default_factory=list)
    unscheduled_keys: List[str] = field(default_factory=list)
    cycle_paths: List[List[str]] = field(default_factory=list)
    depth_by_key: Dict[str, int] = field(default_factory=dict)
    blocker_chains: List[List[str]] = field(default_factory=list)
    root_blockers: List[str] = field(default_factory=list)
    review_summary: Dict[str, int] = field(default_factory=dict)
    suppressed_edges: List[DependencyEdge] = field(default_factory=list)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def explicit_edge_count(self) -> int:
        return sum(1 for edge in self.edges if not edge.inferred)

    @property
    def inferred_edge_count(self) -> int:
        return sum(1 for edge in self.edges if edge.inferred)

    @property
    def suppressed_edge_count(self) -> int:
        return len(self.suppressed_edges)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_count': self.node_count,
            'edge_count': self.edge_count,
            'explicit_edge_count': self.explicit_edge_count,
            'inferred_edge_count': self.inferred_edge_count,
            'suppressed_edge_count': self.suppressed_edge_count,
            'blocked_keys': self.blocked_keys,
            'unscheduled_keys': self.unscheduled_keys,
            'cycle_paths': self.cycle_paths,
            'depth_by_key': self.depth_by_key,
            'blocker_chains': self.blocker_chains,
            'root_blockers': self.root_blockers,
            'review_summary': self.review_summary,
            'nodes': self.nodes,
            'edges': [edge.to_dict() for edge in self.edges],
            'suppressed_edges': [edge.to_dict() for edge in self.suppressed_edges],
        }


@dataclass
class MilestoneProposal:
    '''
    Proposed milestone grouping derived from Jira release targets or backlog state.
    '''
    name: str
    source: str = 'fix_version'
    target_date: str = ''
    issue_keys: List[str] = field(default_factory=list)
    total_issues: int = 0
    open_issues: int = 0
    done_issues: int = 0
    blocked_issues: int = 0
    unassigned_issues: int = 0
    confidence: str = 'medium'
    risk_level: str = 'low'
    summary: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'source': self.source,
            'target_date': self.target_date,
            'issue_keys': self.issue_keys,
            'total_issues': self.total_issues,
            'open_issues': self.open_issues,
            'done_issues': self.done_issues,
            'blocked_issues': self.blocked_issues,
            'unassigned_issues': self.unassigned_issues,
            'confidence': self.confidence,
            'risk_level': self.risk_level,
            'summary': self.summary,
        }


@dataclass
class PlanningRiskRecord:
    '''
    Risk identified during planning snapshot generation.
    '''
    risk_type: str
    severity: str
    title: str
    description: str
    issue_keys: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_type': self.risk_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'issue_keys': self.issue_keys,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
        }


@dataclass
class PlanningSnapshot:
    '''
    Durable planning snapshot produced by the Gantt Project Planner.
    '''
    project_key: str = ''
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    planning_horizon_days: int = 90
    project_info: Dict[str, Any] = field(default_factory=dict)
    backlog_overview: Dict[str, Any] = field(default_factory=dict)
    milestones: List[MilestoneProposal] = field(default_factory=list)
    dependency_graph: DependencyGraph = field(default_factory=DependencyGraph)
    risks: List[PlanningRiskRecord] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    evidence_gaps: List[str] = field(default_factory=list)
    summary_markdown: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'project_key': self.project_key,
            'created_at': self.created_at,
            'planning_horizon_days': self.planning_horizon_days,
            'project_info': self.project_info,
            'backlog_overview': self.backlog_overview,
            'milestones': [milestone.to_dict() for milestone in self.milestones],
            'dependency_graph': self.dependency_graph.to_dict(),
            'risks': [risk.to_dict() for risk in self.risks],
            'issues': self.issues,
            'evidence_summary': self.evidence_summary,
            'evidence_gaps': self.evidence_gaps,
            'summary_markdown': self.summary_markdown,
        }


# ===========================================================================
# Roadmap Analysis Models
# ===========================================================================


@dataclass
class RoadmapRequest:
    '''
    Input request for generating a roadmap analysis snapshot.

    Attributes:
        project_key:          Jira project key (e.g. "STL").
        scope_label:          Label filter for scope (e.g. "CN6000", "CN5000").
        initiative_keys:      Explicit initiative ticket keys to anchor on.
                              If empty, discover via scope_label.
        fix_versions:         Filter by fix version patterns
                              (e.g. ["12.2.0.x", "14.0.0.x"]).
        hierarchy_depth:      How deep to traverse
                              (0=Initiative, 1=Epic, 2=Story).
        include_closed:       Whether to include closed/done tickets.
        output_file:          Path for xlsx output.
        include_gap_analysis: Whether to run LLM gap analysis.
    '''
    project_key: str = ''
    scope_label: str = ''
    initiative_keys: Optional[List[str]] = None
    fix_versions: Optional[List[str]] = None
    hierarchy_depth: int = 3
    include_closed: bool = False
    output_file: Optional[str] = None
    include_gap_analysis: bool = True

    show_priority: bool = True
    blank_unassigned: bool = True
    bold_stories: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_key': self.project_key,
            'scope_label': self.scope_label,
            'initiative_keys': self.initiative_keys,
            'fix_versions': self.fix_versions,
            'hierarchy_depth': self.hierarchy_depth,
            'include_closed': self.include_closed,
            'output_file': self.output_file,
            'include_gap_analysis': self.include_gap_analysis,
        }


@dataclass
class RoadmapItem:
    '''
    A single Jira ticket or proposed work item in the roadmap.

    Attributes:
        key:         Jira ticket key (empty string for proposed items).
        summary:     Ticket summary / title.
        issue_type:  Initiative, Epic, or Story.
        status:      Open, In Progress, etc.
        priority:    P0, P1, P2, P3.
        assignee:    Display name of the assignee.
        fix_version: Target fix version string.
        component:   Jira component name.
        labels:      Comma-separated label string.
        parent_key:  Parent ticket key.
        depth:       Hierarchy depth (0=Initiative, 1=Epic, 2=Story).
        source:      "Jira" or "Proposed".
        section:     Section grouping label.
    '''
    key: str = ''
    summary: str = ''
    issue_type: str = ''
    status: str = ''
    priority: str = ''
    assignee: str = ''
    fix_version: str = ''
    component: str = ''
    labels: str = ''
    parent_key: str = ''
    depth: int = 0
    source: str = 'Jira'
    section: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'summary': self.summary,
            'issue_type': self.issue_type,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'fix_version': self.fix_version,
            'component': self.component,
            'labels': self.labels,
            'parent_key': self.parent_key,
            'depth': self.depth,
            'source': self.source,
            'section': self.section,
        }


@dataclass
class RoadmapGap:
    '''
    A proposed gap identified by LLM analysis — an Epic or Story
    that should exist but does not yet have a Jira ticket.

    Attributes:
        summary:               Proposed ticket summary.
        issue_type:            Epic or Story.
        priority:              Suggested priority (P0–P3).
        suggested_component:   Suggested Jira component.
        acceptance_criteria:   Acceptance criteria text.
        dependencies:          Semicolon-separated STL- ticket keys.
        suggested_fix_version: Suggested target fix version.
        labels:                Comma-separated label string.
        depth:                 Hierarchy depth (1=Epic, 2=Story).
        section:               Which section this belongs in.
        parent_summary:        For stories, the parent epic summary
                               (proposed or existing).
    '''
    summary: str = ''
    issue_type: str = ''
    priority: str = ''
    suggested_component: str = ''
    acceptance_criteria: str = ''
    dependencies: str = ''
    suggested_fix_version: str = ''
    labels: str = ''
    depth: int = 1
    section: str = ''
    parent_summary: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'summary': self.summary,
            'issue_type': self.issue_type,
            'priority': self.priority,
            'suggested_component': self.suggested_component,
            'acceptance_criteria': self.acceptance_criteria,
            'dependencies': self.dependencies,
            'suggested_fix_version': self.suggested_fix_version,
            'labels': self.labels,
            'depth': self.depth,
            'section': self.section,
            'parent_summary': self.parent_summary,
        }


@dataclass
class RoadmapSection:
    '''
    A logical grouping of roadmap items and gaps under a common heading.

    Attributes:
        title: Section heading (e.g. initiative summary or thematic group).
        items: Jira-sourced or proposed roadmap items in this section.
        gaps:  LLM-identified gaps belonging to this section.
    '''
    title: str = ''
    items: List[RoadmapItem] = field(default_factory=list)
    gaps: List[RoadmapGap] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'items': [item.to_dict() for item in self.items],
            'gaps': [gap.to_dict() for gap in self.gaps],
        }


@dataclass
class RoadmapSnapshot:
    '''
    Durable snapshot produced by the Roadmap Analyzer.

    Attributes:
        project_key:      Jira project key.
        scope_label:      Scope label used for this analysis.
        created_at:       ISO 8601 timestamp of snapshot creation.
        snapshot_id:      Short UUID identifying this snapshot.
        sections:         Ordered list of roadmap sections.
        summary_markdown: Human-readable Markdown summary of the roadmap.
    '''
    project_key: str = ''
    scope_label: str = ''
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sections: List[RoadmapSection] = field(default_factory=list)
    summary_markdown: str = ''

    # -- computed properties ----------------------------------------------------

    @property
    def total_jira_items(self) -> int:
        '''Count of items sourced from Jira across all sections.'''
        return sum(
            1 for section in self.sections
            for item in section.items
            if item.source == 'Jira'
        )

    @property
    def total_proposed_gaps(self) -> int:
        '''Count of LLM-proposed gaps across all sections.'''
        return sum(len(section.gaps) for section in self.sections)

    @property
    def total_items(self) -> int:
        '''Total count of all items and gaps across all sections.'''
        return sum(
            len(section.items) + len(section.gaps)
            for section in self.sections
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_key': self.project_key,
            'scope_label': self.scope_label,
            'created_at': self.created_at,
            'snapshot_id': self.snapshot_id,
            'total_jira_items': self.total_jira_items,
            'total_proposed_gaps': self.total_proposed_gaps,
            'total_items': self.total_items,
            'sections': [section.to_dict() for section in self.sections],
            'summary_markdown': self.summary_markdown,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'RoadmapSnapshot':
        '''Reconstruct a RoadmapSnapshot from a serialized dictionary.'''
        sections = []
        for section_data in data.get('sections', []):
            items = [
                RoadmapItem(**item_data)
                for item_data in section_data.get('items', [])
            ]
            gaps = [
                RoadmapGap(**gap_data)
                for gap_data in section_data.get('gaps', [])
            ]
            sections.append(RoadmapSection(
                title=section_data.get('title', ''),
                items=items,
                gaps=gaps,
            ))

        return RoadmapSnapshot(
            project_key=data.get('project_key', ''),
            scope_label=data.get('scope_label', ''),
            created_at=data.get('created_at', ''),
            snapshot_id=data.get('snapshot_id', ''),
            sections=sections,
            summary_markdown=data.get('summary_markdown', ''),
        )


# ===========================================================================
# Release Monitor Models
# ===========================================================================


@dataclass
class ReleaseMonitorRequest:
    """Request parameters for release health monitoring."""
    project_key: str = "STL"
    releases: Optional[List[str]] = None          # fix version names to monitor (e.g. ["12.2.0.x", "14.0.0.x"])
    scope_label: Optional[str] = None             # additional keyword filter (e.g. "CN6000")
    include_gap_analysis: bool = True              # run roadmap gap analysis on the release scope
    include_bug_report: bool = True                # include bug status breakdown
    include_velocity: bool = True                  # compute velocity/throughput metrics
    include_readiness: bool = True                 # run readiness assessment
    compare_to_previous: bool = True               # delta comparison with last snapshot
    output_file: Optional[str] = None              # xlsx output path


@dataclass
class BugSummary:
    """Bug counts broken down by status and priority for a release."""
    release: str = ""
    total_bugs: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)    # e.g. {"Open": 5, "In Progress": 3}
    by_priority: Dict[str, int] = field(default_factory=dict)  # e.g. {"P0": 1, "P1": 2}
    by_component: Dict[str, int] = field(default_factory=dict)
    new_since_last: List[str] = field(default_factory=list)    # ticket keys opened since last snapshot
    closed_since_last: List[str] = field(default_factory=list) # ticket keys closed since last snapshot
    priority_changes: List[Dict[str, str]] = field(default_factory=list)  # [{key, from, to}]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "release": self.release,
            "total_bugs": self.total_bugs,
            "by_status": self.by_status,
            "by_priority": self.by_priority,
            "by_component": self.by_component,
            "new_since_last": self.new_since_last,
            "closed_since_last": self.closed_since_last,
            "priority_changes": self.priority_changes,
        }


@dataclass
class ReleaseMonitorReport:
    """Complete release health monitoring report."""
    project_key: str = ""
    created_at: str = ""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scope_label: str = ""
    releases_monitored: List[str] = field(default_factory=list)

    # Bug summaries per release
    bug_summaries: List[BugSummary] = field(default_factory=list)

    # Velocity metrics (from core.release_tracking)
    velocity: Optional[Dict[str, Any]] = None

    # Readiness assessment (from core.release_tracking)
    readiness: Optional[Dict[str, Any]] = None

    # Gap analysis (reuses RoadmapSnapshot if run)
    roadmap_snapshot: Optional[Dict[str, Any]] = None

    # Delta from previous report
    delta: Optional[Dict[str, Any]] = None

    # Historical release snapshots and cycle-time evidence
    release_snapshots: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cycle_time_samples: List[Dict[str, Any]] = field(default_factory=list)
    cycle_time_stats: List[Dict[str, Any]] = field(default_factory=list)

    # Human-readable summary
    summary_markdown: str = ""

    # Output file path
    output_file: str = ""

    @property
    def total_bugs(self) -> int:
        return sum(b.total_bugs for b in self.bug_summaries)

    @property
    def total_p0(self) -> int:
        return sum(b.by_priority.get("P0", 0) for b in self.bug_summaries)

    @property
    def total_p1(self) -> int:
        return sum(b.by_priority.get("P1", 0) for b in self.bug_summaries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_key": self.project_key,
            "created_at": self.created_at,
            "report_id": self.report_id,
            "scope_label": self.scope_label,
            "releases_monitored": self.releases_monitored,
            "bug_summaries": [b.to_dict() for b in self.bug_summaries],
            "velocity": self.velocity,
            "readiness": self.readiness,
            "roadmap_snapshot": self.roadmap_snapshot,
            "delta": self.delta,
            "release_snapshots": self.release_snapshots,
            "cycle_time_samples": self.cycle_time_samples,
            "cycle_time_stats": self.cycle_time_stats,
            "summary_markdown": self.summary_markdown,
            "output_file": self.output_file,
            "total_bugs": self.total_bugs,
            "total_p0": self.total_p0,
            "total_p1": self.total_p1,
        }


@dataclass
class ReleaseSurveyRequest:
    '''Request parameters for a release execution survey.'''
    project_key: str = 'STL'
    releases: Optional[List[str]] = None
    scope_label: Optional[str] = None
    survey_mode: str = 'feature_dev'
    output_file: Optional[str] = None


@dataclass
class ReleaseSurveyReleaseSummary:
    '''Per-release execution survey summary.'''
    release: str = ''
    total_tickets: int = 0
    status_breakdown: Dict[str, int] = field(default_factory=dict)
    priority_breakdown: Dict[str, int] = field(default_factory=dict)
    issue_type_breakdown: Dict[str, int] = field(default_factory=dict)
    component_breakdown: Dict[str, int] = field(default_factory=dict)
    family_breakdowns: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    family_epic_analysis: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    done_tickets: List[Dict[str, Any]] = field(default_factory=list)
    in_progress_tickets: List[Dict[str, Any]] = field(default_factory=list)
    remaining_tickets: List[Dict[str, Any]] = field(default_factory=list)
    blocked_tickets: List[Dict[str, Any]] = field(default_factory=list)
    stale_tickets: List[str] = field(default_factory=list)
    unassigned_tickets: List[str] = field(default_factory=list)

    @property
    def done_count(self) -> int:
        return len(self.done_tickets)

    @property
    def in_progress_count(self) -> int:
        return len(self.in_progress_tickets)

    @property
    def remaining_count(self) -> int:
        return len(self.remaining_tickets)

    @property
    def blocked_count(self) -> int:
        return len(self.blocked_tickets)

    @property
    def stale_count(self) -> int:
        return len(self.stale_tickets)

    @property
    def unassigned_count(self) -> int:
        return len(self.unassigned_tickets)

    @property
    def completion_pct(self) -> float:
        if self.total_tickets <= 0:
            return 0.0
        return (self.done_count / float(self.total_tickets)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'release': self.release,
            'total_tickets': self.total_tickets,
            'status_breakdown': self.status_breakdown,
            'priority_breakdown': self.priority_breakdown,
            'issue_type_breakdown': self.issue_type_breakdown,
            'component_breakdown': self.component_breakdown,
            'family_breakdowns': self.family_breakdowns,
            'family_epic_analysis': self.family_epic_analysis,
            'done_count': self.done_count,
            'in_progress_count': self.in_progress_count,
            'remaining_count': self.remaining_count,
            'blocked_count': self.blocked_count,
            'stale_count': self.stale_count,
            'unassigned_count': self.unassigned_count,
            'completion_pct': self.completion_pct,
            'done_tickets': self.done_tickets,
            'in_progress_tickets': self.in_progress_tickets,
            'remaining_tickets': self.remaining_tickets,
            'blocked_tickets': self.blocked_tickets,
            'stale_tickets': self.stale_tickets,
            'unassigned_tickets': self.unassigned_tickets,
        }


@dataclass
class ReleaseSurveyReport:
    '''Complete release execution survey report.'''
    project_key: str = ''
    created_at: str = ''
    survey_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scope_label: str = ''
    survey_mode: str = 'feature_dev'
    releases_surveyed: List[str] = field(default_factory=list)
    release_summaries: List[ReleaseSurveyReleaseSummary] = field(default_factory=list)
    summary_markdown: str = ''
    output_file: str = ''

    @property
    def total_tickets(self) -> int:
        return sum(item.total_tickets for item in self.release_summaries)

    @property
    def done_count(self) -> int:
        return sum(item.done_count for item in self.release_summaries)

    @property
    def in_progress_count(self) -> int:
        return sum(item.in_progress_count for item in self.release_summaries)

    @property
    def remaining_count(self) -> int:
        return sum(item.remaining_count for item in self.release_summaries)

    @property
    def blocked_count(self) -> int:
        return sum(item.blocked_count for item in self.release_summaries)

    @property
    def stale_count(self) -> int:
        return sum(item.stale_count for item in self.release_summaries)

    @property
    def unassigned_count(self) -> int:
        return sum(item.unassigned_count for item in self.release_summaries)

    @property
    def completion_pct(self) -> float:
        if self.total_tickets <= 0:
            return 0.0
        return (self.done_count / float(self.total_tickets)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_key': self.project_key,
            'created_at': self.created_at,
            'survey_id': self.survey_id,
            'scope_label': self.scope_label,
            'survey_mode': self.survey_mode,
            'releases_surveyed': self.releases_surveyed,
            'release_summaries': [item.to_dict() for item in self.release_summaries],
            'summary_markdown': self.summary_markdown,
            'output_file': self.output_file,
            'total_tickets': self.total_tickets,
            'done_count': self.done_count,
            'in_progress_count': self.in_progress_count,
            'remaining_count': self.remaining_count,
            'blocked_count': self.blocked_count,
            'stale_count': self.stale_count,
            'unassigned_count': self.unassigned_count,
            'completion_pct': self.completion_pct,
        }
