##########################################################################################
#
# Module: state
#
# Description: State management for Cornelis Agent Pipeline.
#              Provides session state and persistence capabilities.
#
# Author: Cornelis Networks
#
##########################################################################################

from typing import Any

from state.session import SessionState, SessionManager
from state.persistence import StatePersistence, JSONPersistence, SQLitePersistence

__all__ = [
    'SessionState',
    'SessionManager',
    'StatePersistence',
    'JSONPersistence',
    'SQLitePersistence',
    'DruckerReportStore',
    'GanttDependencyReviewStore',
    'GanttReleaseMonitorStore',
    'GanttReleaseSurveyStore',
    'GanttSnapshotStore',
    'HemingwayRecordStore',
    'HypatiaRecordStore',
    'ShannonStateStore',
]


def __getattr__(name: str) -> Any:
    if name == 'DruckerReportStore':
        from agents.drucker.state.report_store import DruckerReportStore

        return DruckerReportStore
    if name == 'GanttDependencyReviewStore':
        from agents.gantt.state.dependency_review_store import GanttDependencyReviewStore

        return GanttDependencyReviewStore
    if name == 'GanttReleaseMonitorStore':
        from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore

        return GanttReleaseMonitorStore
    if name == 'GanttReleaseSurveyStore':
        from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore

        return GanttReleaseSurveyStore
    if name == 'GanttSnapshotStore':
        from agents.gantt.state.snapshot_store import GanttSnapshotStore

        return GanttSnapshotStore
    if name in ('HemingwayRecordStore', 'HypatiaRecordStore'):
        from agents.hemingway.state.record_store import HemingwayRecordStore

        return HemingwayRecordStore
    if name == 'ShannonStateStore':
        from agents.shannon.state_store import ShannonStateStore

        return ShannonStateStore
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
