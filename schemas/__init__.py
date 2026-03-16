"""
schemas — Canonical data record models shared across all AI Agent Workforce agents.

These Pydantic models define the six canonical objects from the agent specification
(Section 10.2) plus supporting types for requests, failures, decisions, and patches.
"""

from .build_record import BuildRecord
from .test_execution_record import TestRunRequest, TestExecutionRecord, TestFailureRecord
from .release_record import ReleaseCandidate, ReleaseDecision, ReleaseReadinessSummary
from .traceability_record import TraceabilityRecord, RelationshipEdge, CoverageGapRecord
from .documentation_record import DocumentationRecord, DocumentationPatch, PublicationRecord
from .meeting_summary_record import (
    MeetingRecord,
    MeetingSummaryRecord,
    ActionItemDraft,
    DecisionRecord,
)

__all__ = [
    # Build
    "BuildRecord",
    # Test
    "TestRunRequest",
    "TestExecutionRecord",
    "TestFailureRecord",
    # Release
    "ReleaseCandidate",
    "ReleaseDecision",
    "ReleaseReadinessSummary",
    # Traceability
    "TraceabilityRecord",
    "RelationshipEdge",
    "CoverageGapRecord",
    # Documentation
    "DocumentationRecord",
    "DocumentationPatch",
    "PublicationRecord",
    # Meeting
    "MeetingRecord",
    "MeetingSummaryRecord",
    "ActionItemDraft",
    "DecisionRecord",
]
