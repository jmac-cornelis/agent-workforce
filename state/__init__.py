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
    'HypatiaRecordStore',
    'ShannonStateStore',
]


def __getattr__(name: str) -> Any:
    if name == 'DruckerReportStore':
        from state.drucker_report_store import DruckerReportStore

        return DruckerReportStore
    if name == 'GanttDependencyReviewStore':
        from state.gantt_dependency_review_store import GanttDependencyReviewStore

        return GanttDependencyReviewStore
    if name == 'GanttReleaseMonitorStore':
        from state.gantt_release_monitor_store import GanttReleaseMonitorStore

        return GanttReleaseMonitorStore
    if name == 'GanttReleaseSurveyStore':
        from state.gantt_release_survey_store import GanttReleaseSurveyStore

        return GanttReleaseSurveyStore
    if name == 'GanttSnapshotStore':
        from state.gantt_snapshot_store import GanttSnapshotStore

        return GanttSnapshotStore
    if name == 'HypatiaRecordStore':
        from state.hypatia_record_store import HypatiaRecordStore

        return HypatiaRecordStore
    if name == 'ShannonStateStore':
        from state.shannon_state_store import ShannonStateStore

        return ShannonStateStore
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
