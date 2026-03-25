from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from core.release_tracking import (
    ReleaseSnapshot,
    TrackerConfig,
    assess_readiness,
    build_snapshot,
    compute_cycle_time_stats,
    compute_delta,
    compute_velocity,
    format_summary,
)


def _ticket(
    key: str,
    *,
    release: str = '12.1.1.x',
    status: str = 'Open',
    priority: str = 'P2-High',
    components=None,
    assignee: str = 'Jane Dev',
    created: str = '2026-03-01T10:00:00+00:00',
    updated: str = '2026-03-02T10:00:00+00:00',
):
    if components is None:
        components = ['JKR Host Driver']
    return {
        'key': key,
        'fix_versions': [release],
        'status': status,
        'priority': priority,
        'components': components,
        'assignee': assignee,
        'created': created,
        'updated': updated,
    }


def test_build_snapshot_aggregates_counts_for_release():
    tickets: list[Mapping[str, Any]] = [
        _ticket('STL-1', status='Open', priority='P0-Stopper', components=['JKR Host Driver']),
        _ticket('STL-2', status='In Progress', priority='P1-Critical', components=['BTS/verbs']),
        _ticket('STL-3', status='Closed', priority='P2-High', components=[]),
        _ticket('STL-4', release='12.2.0.x', status='Open', priority='P0-Stopper'),
    ]

    snapshot = build_snapshot(tickets, '12.1.1.x')

    assert snapshot.release == '12.1.1.x'
    assert snapshot.total_tickets == 3
    assert snapshot.by_status['Open'] == 1
    assert snapshot.by_status['In Progress'] == 1
    assert snapshot.by_status['Closed'] == 1
    assert snapshot.by_priority['P0-Stopper'] == 1
    assert snapshot.by_component['JKR Host Driver'] == 1
    assert snapshot.by_component['BTS/verbs'] == 1
    assert snapshot.by_component['Unspecified'] == 1


def test_compute_delta_detects_new_closed_and_changes():
    previous = ReleaseSnapshot(
        release='12.1.1.x',
        timestamp='2026-03-10T09:00:00+00:00',
        total_tickets=3,
        tickets=[
            _ticket('STL-10', status='Open', priority='P2-High'),
            _ticket('STL-11', status='In Progress', priority='P1-Critical'),
            _ticket('STL-12', status='Verify', priority='P3-Medium'),
        ],
    )

    current = ReleaseSnapshot(
        release='12.1.1.x',
        timestamp='2026-03-11T09:00:00+00:00',
        total_tickets=3,
        tickets=[
            _ticket('STL-10', status='Closed', priority='P2-High'),
            _ticket('STL-11', status='Closed', priority='P0-Stopper'),
            _ticket('STL-13', status='Open', priority='P1-Critical'),
        ],
    )

    delta = compute_delta(current, previous)

    assert delta.release == '12.1.1.x'
    assert delta.new_tickets == ['STL-13']
    assert delta.closed_tickets == ['STL-10', 'STL-11', 'STL-12']
    assert {'key': 'STL-10', 'from': 'Open', 'to': 'Closed'} in delta.status_changes
    assert {'key': 'STL-11', 'from': 'P1-Critical', 'to': 'P0-Stopper'} in delta.priority_changes
    assert delta.new_p0_p1 == ['STL-13']
    assert delta.velocity == 3.0


def test_compute_velocity_uses_snapshot_window_and_rates():
    base = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    snapshots = [
        ReleaseSnapshot(
            release='12.1.1.x',
            timestamp=(base + timedelta(days=0)).isoformat(),
            total_tickets=2,
            tickets=[
                _ticket('STL-20', status='Open'),
                _ticket('STL-21', status='Open'),
            ],
        ),
        ReleaseSnapshot(
            release='12.1.1.x',
            timestamp=(base + timedelta(days=1)).isoformat(),
            total_tickets=3,
            tickets=[
                _ticket('STL-20', status='Closed'),
                _ticket('STL-21', status='Open'),
                _ticket('STL-22', status='Open'),
            ],
        ),
        ReleaseSnapshot(
            release='12.1.1.x',
            timestamp=(base + timedelta(days=2)).isoformat(),
            total_tickets=4,
            tickets=[
                _ticket('STL-20', status='Closed'),
                _ticket('STL-21', status='Closed'),
                _ticket('STL-22', status='Open'),
                _ticket('STL-23', status='Open'),
            ],
        ),
    ]

    velocity = compute_velocity(snapshots, window_days=14)

    assert velocity['snapshots_used'] == 3
    assert velocity['opened'] == 2
    assert velocity['closed'] == 2
    assert velocity['daily_open_rate'] == 1.0
    assert velocity['daily_close_rate'] == 1.0
    assert velocity['daily_net_rate'] == 0.0


def test_compute_cycle_time_stats_filters_by_component_and_priority():
    cycle_times: list[Mapping[str, Any]] = [
        {'component': 'JKR Host Driver', 'priority': 'P0-Stopper', 'duration_hours': 24},
        {'component': 'JKR Host Driver', 'priority': 'P0-Stopper', 'duration_hours': 48},
        {'component': 'BTS/verbs', 'priority': 'P0-Stopper', 'duration_hours': 12},
        {'component': 'JKR Host Driver', 'priority': 'P1-Critical', 'duration_hours': 72},
    ]

    stats = compute_cycle_time_stats(cycle_times, component='JKR Host Driver', priority='P0-Stopper')

    assert stats.component == 'JKR Host Driver'
    assert stats.priority == 'P0-Stopper'
    assert stats.sample_size == 2
    assert stats.avg_hours == 36.0
    assert stats.median_hours == 36.0


def test_assess_readiness_calculates_eta_component_risks_and_stale_tickets():
    now = datetime.now(timezone.utc)
    stale_updated = (now - timedelta(hours=70)).isoformat()
    fresh_updated = (now - timedelta(hours=4)).isoformat()

    snapshot = ReleaseSnapshot(
        release='12.1.1.x',
        timestamp=now.isoformat(),
        total_tickets=4,
        tickets=[
            _ticket('STL-30', status='Open', priority='P0-Stopper', components=['JKR Host Driver'], updated=stale_updated),
            _ticket('STL-31', status='In Progress', priority='P1-Critical', components=['BTS/verbs'], updated=fresh_updated),
            _ticket('STL-32', status='Closed', priority='P2-High', components=['BTS/verbs'], updated=fresh_updated),
            _ticket('STL-33', status='Open', priority='P2-High', components=['JKR Host Driver'], updated=fresh_updated),
        ],
    )

    velocity = {
        'daily_close_rate': 2.0,
    }

    cycle_stats = [
        {'component': 'JKR Host Driver', 'priority': 'P0-Stopper', 'avg_hours': 24.0, 'median_hours': 24.0, 'sample_size': 10},
        {'component': 'BTS/verbs', 'priority': 'P1-Critical', 'avg_hours': 12.0, 'median_hours': 12.0, 'sample_size': 8},
    ]

    config = TrackerConfig(
        stale_threshold_multiplier=2.0,
        closed_statuses=['Closed', 'Done', 'Resolved'],
    )

    readiness = assess_readiness(snapshot, velocity, cycle_stats, config)

    assert readiness.release == '12.1.1.x'
    assert readiness.total_open == 3
    assert readiness.p0_open == 1
    assert readiness.p1_open == 1
    assert readiness.daily_close_rate == 2.0
    assert readiness.estimated_days_remaining == 1.5
    assert 'STL-30' in readiness.stale_tickets
    assert readiness.component_risks[0]['component'] == 'JKR Host Driver'


def test_tracker_config_from_yaml_and_summary_formatting():
    yaml_text = '\n'.join(
        [
            'project: STL',
            'releases: ["12.1.1.x", "12.2.0.x"]',
            'track_priorities: ["P0-Stopper", "P1-Critical"]',
            'learning:',
            '  cycle_time_window_days: 60',
            '  stale_threshold_multiplier: 1.5',
            '  velocity_window_days: 10',
            'output:',
            '  format: json',
        ]
    )

    cfg = TrackerConfig.from_yaml(yaml_text)

    assert cfg.project == 'STL'
    assert cfg.releases == ['12.1.1.x', '12.2.0.x']
    assert cfg.track_priorities == ['P0-Stopper', 'P1-Critical']
    assert cfg.cycle_time_window_days == 60
    assert cfg.stale_threshold_multiplier == 1.5
    assert cfg.velocity_window_days == 10
    assert cfg.output['format'] == 'json'

    delta = ReleaseSnapshot(
        release='12.1.1.x',
        timestamp='2026-03-10T09:00:00+00:00',
        total_tickets=0,
        tickets=[],
    )
    next_snapshot = ReleaseSnapshot(
        release='12.1.1.x',
        timestamp='2026-03-11T09:00:00+00:00',
        total_tickets=0,
        tickets=[],
    )
    release_delta = compute_delta(next_snapshot, delta)

    readiness = assess_readiness(
        next_snapshot,
        {'daily_close_rate': 1.0},
        [],
        TrackerConfig(),
    )

    summary = format_summary(release_delta, readiness)

    assert 'Release 12.1.1.x' in summary
    assert 'Daily close rate: 1.00' in summary
