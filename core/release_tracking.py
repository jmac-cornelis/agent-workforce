##########################################################################################
#
# Module: core/release_tracking.py
#
# Description: Pure-logic release health tracking helpers.
#              The module exposes dataclasses and analytics functions used by tests,
#              CLI wrappers, and future automation.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Mapping, Sequence

import yaml

DEFAULT_CLOSED_STATUSES: list[str] = ['Closed', 'Done', 'Resolved']


@dataclass
class ReleaseSnapshot:
    release: str
    timestamp: str
    total_tickets: int
    tickets: list[dict[str, Any]]

    @property
    def by_status(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for ticket in self.tickets:
            counts[str(ticket.get('status', 'Unknown'))] += 1
        return dict(counts)

    @property
    def by_priority(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for ticket in self.tickets:
            counts[str(ticket.get('priority', 'Unknown'))] += 1
        return dict(counts)

    @property
    def by_component(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for ticket in self.tickets:
            for component in _ticket_components(ticket):
                counts[component] += 1
        return dict(counts)


@dataclass
class TrackerConfig:
    project: str = ''
    releases: list[str] = field(default_factory=list)
    track_priorities: list[str] = field(default_factory=list)
    cycle_time_window_days: int = 30
    stale_threshold_multiplier: float = 2.0
    velocity_window_days: int = 14
    closed_statuses: list[str] = field(default_factory=lambda: list(DEFAULT_CLOSED_STATUSES))
    output: Any | None = None

    @classmethod
    def from_yaml(cls, yaml_text: str) -> TrackerConfig:
        parsed: dict[str, Any] = yaml.safe_load(yaml_text) or {}
        learning = parsed.get('learning') or {}

        # Reasoning: tests accept learning values nested under `learning`, so we
        # prioritize that section but still allow direct keys as fallbacks.
        return cls(
            project=str(parsed.get('project', '')),
            releases=[str(value) for value in (parsed.get('releases') or [])],
            track_priorities=[str(value) for value in (parsed.get('track_priorities') or [])],
            cycle_time_window_days=int(
                learning.get('cycle_time_window_days', parsed.get('cycle_time_window_days', 30))
            ),
            stale_threshold_multiplier=float(
                learning.get('stale_threshold_multiplier', parsed.get('stale_threshold_multiplier', 2.0))
            ),
            velocity_window_days=int(
                learning.get('velocity_window_days', parsed.get('velocity_window_days', 14))
            ),
            closed_statuses=[str(value) for value in (parsed.get('closed_statuses') or DEFAULT_CLOSED_STATUSES)],
            output=parsed.get('output'),
        )


@dataclass
class ReleaseDelta:
    release: str
    new_tickets: list[str]
    closed_tickets: list[str]
    status_changes: list[dict[str, str]]
    priority_changes: list[dict[str, str]]
    new_p0_p1: list[str]
    velocity: float


@dataclass
class CycleTimeStats:
    component: str
    priority: str
    sample_size: int
    avg_hours: float
    median_hours: float


@dataclass
class ReadinessReport:
    release: str
    total_open: int
    p0_open: int
    p1_open: int
    daily_close_rate: float
    estimated_days_remaining: float | None
    stale_tickets: list[str]
    component_risks: list[dict[str, Any]]


def build_snapshot(tickets: list[Mapping[str, Any]], release: str) -> ReleaseSnapshot:
    selected: list[dict[str, Any]] = []

    for raw_ticket in tickets:
        ticket = dict(raw_ticket)
        versions = ticket.get('fix_versions')
        if versions is None:
            versions = ticket.get('fixVersions')

        if isinstance(versions, str):
            version_list = [versions]
        elif isinstance(versions, list):
            version_list = [str(version) for version in versions]
        else:
            version_list = []

        if release in version_list:
            selected.append(ticket)

    return ReleaseSnapshot(
        release=release,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_tickets=len(selected),
        tickets=selected,
    )


def compute_delta(current: ReleaseSnapshot, previous: ReleaseSnapshot) -> ReleaseDelta:
    current_by_key = _tickets_by_key(current.tickets)
    previous_by_key = _tickets_by_key(previous.tickets)

    new_tickets = [
        str(ticket['key'])
        for ticket in current.tickets
        if str(ticket.get('key')) not in previous_by_key
    ]

    closed_tickets: list[str] = []
    closed_statuses = set(DEFAULT_CLOSED_STATUSES)

    # Reasoning: closed tickets include items removed from the current snapshot
    # or items that transitioned from non-closed to closed statuses.
    for previous_ticket in previous.tickets:
        key = str(previous_ticket.get('key'))
        current_ticket = current_by_key.get(key)

        if current_ticket is None:
            closed_tickets.append(key)
            continue

        previous_status = str(previous_ticket.get('status', ''))
        current_status = str(current_ticket.get('status', ''))
        if previous_status != current_status and current_status in closed_statuses:
            closed_tickets.append(key)

    status_changes: list[dict[str, str]] = []
    priority_changes: list[dict[str, str]] = []

    for current_ticket in current.tickets:
        key = str(current_ticket.get('key'))
        previous_ticket = previous_by_key.get(key)
        if previous_ticket is None:
            continue

        previous_status = str(previous_ticket.get('status', ''))
        current_status = str(current_ticket.get('status', ''))
        if previous_status != current_status:
            status_changes.append({'key': key, 'from': previous_status, 'to': current_status})

        previous_priority = str(previous_ticket.get('priority', ''))
        current_priority = str(current_ticket.get('priority', ''))
        if previous_priority != current_priority:
            priority_changes.append({'key': key, 'from': previous_priority, 'to': current_priority})

    new_p0_p1 = [
        key
        for key in new_tickets
        if _is_p0_p1(str(current_by_key.get(key, {}).get('priority', '')))
    ]

    days_between = _days_between(previous.timestamp, current.timestamp)
    velocity = float(len(closed_tickets)) / days_between if days_between > 0 else 0.0

    return ReleaseDelta(
        release=current.release,
        new_tickets=new_tickets,
        closed_tickets=closed_tickets,
        status_changes=status_changes,
        priority_changes=priority_changes,
        new_p0_p1=new_p0_p1,
        velocity=velocity,
    )


def compute_velocity(snapshots: list[ReleaseSnapshot], window_days: int) -> dict[str, float | int]:
    if not snapshots:
        return {
            'snapshots_used': 0,
            'opened': 0,
            'closed': 0,
            'daily_open_rate': 0.0,
            'daily_close_rate': 0.0,
            'daily_net_rate': 0.0,
        }

    ordered = sorted(snapshots, key=lambda snapshot: _parse_iso(snapshot.timestamp))
    latest_time = _parse_iso(ordered[-1].timestamp)

    if window_days > 0:
        cutoff = latest_time - timedelta(days=window_days)
        used = [snapshot for snapshot in ordered if _parse_iso(snapshot.timestamp) >= cutoff]
    else:
        used = ordered

    if not used:
        used = [ordered[-1]]

    first = used[0]
    last = used[-1]

    first_by_key = _tickets_by_key(first.tickets)
    last_by_key = _tickets_by_key(last.tickets)

    first_keys = set(first_by_key)
    last_keys = set(last_by_key)

    opened = len(last_keys - first_keys)

    closed_statuses = set(DEFAULT_CLOSED_STATUSES)
    closed_keys: list[str] = []

    for key, first_ticket in first_by_key.items():
        last_ticket = last_by_key.get(key)
        if last_ticket is None:
            closed_keys.append(key)
            continue

        first_status = str(first_ticket.get('status', ''))
        last_status = str(last_ticket.get('status', ''))
        if first_status != last_status and last_status in closed_statuses:
            closed_keys.append(key)

    closed = len(closed_keys)

    span_days = _days_between(first.timestamp, last.timestamp)
    if span_days <= 0:
        span_days = 1.0

    daily_open_rate = opened / span_days
    daily_close_rate = closed / span_days

    return {
        'snapshots_used': len(used),
        'opened': opened,
        'closed': closed,
        'daily_open_rate': daily_open_rate,
        'daily_close_rate': daily_close_rate,
        'daily_net_rate': daily_open_rate - daily_close_rate,
    }


def compute_cycle_time_stats(
    cycle_times: list[Mapping[str, Any]],
    component: str,
    priority: str,
) -> CycleTimeStats:
    relevant_hours: list[float] = []

    for item in cycle_times:
        if str(item.get('component')) != component:
            continue
        if str(item.get('priority')) != priority:
            continue

        raw_hours = item.get('duration_hours', item.get('hours', 0.0))
        relevant_hours.append(float(raw_hours))

    if relevant_hours:
        avg_hours = sum(relevant_hours) / len(relevant_hours)
        median_hours = float(median(relevant_hours))
    else:
        avg_hours = 0.0
        median_hours = 0.0

    return CycleTimeStats(
        component=component,
        priority=priority,
        sample_size=len(relevant_hours),
        avg_hours=avg_hours,
        median_hours=median_hours,
    )


def assess_readiness(
    snapshot: ReleaseSnapshot,
    velocity: Mapping[str, Any],
    cycle_stats: list[CycleTimeStats | Mapping[str, Any]],
    config: TrackerConfig,
) -> ReadinessReport:
    closed_statuses = set(config.closed_statuses or DEFAULT_CLOSED_STATUSES)

    open_tickets = [
        ticket
        for ticket in snapshot.tickets
        if str(ticket.get('status', '')) not in closed_statuses
    ]

    total_open = len(open_tickets)
    p0_open = sum(1 for ticket in open_tickets if _priority_prefix(str(ticket.get('priority', ''))) == 'P0')
    p1_open = sum(1 for ticket in open_tickets if _priority_prefix(str(ticket.get('priority', ''))) == 'P1')

    daily_close_rate = float(velocity.get('daily_close_rate', 0.0) or 0.0)
    estimated_days_remaining = (total_open / daily_close_rate) if daily_close_rate > 0 else None

    avg_cycle_lookup = _build_avg_cycle_lookup(cycle_stats)
    now = datetime.now(timezone.utc)
    stale_tickets: list[str] = []

    for ticket in open_tickets:
        updated_raw = ticket.get('updated')
        if not updated_raw:
            continue

        updated_time = _parse_iso(str(updated_raw))
        priority = str(ticket.get('priority', ''))

        # Reasoning: tickets can belong to multiple components; we treat the
        # ticket as stale if any component+priority baseline marks it stale.
        for component in _ticket_components(ticket):
            avg_cycle_hours = avg_cycle_lookup.get((component, priority))
            if not avg_cycle_hours or avg_cycle_hours <= 0:
                continue

            threshold = timedelta(hours=avg_cycle_hours * config.stale_threshold_multiplier)
            if now - updated_time > threshold:
                stale_tickets.append(str(ticket.get('key')))
                break

    component_counts: Counter[str] = Counter()
    for ticket in open_tickets:
        for component in _ticket_components(ticket):
            component_counts[component] += 1

    component_risks = [
        {'component': component, 'open_tickets': count}
        for component, count in sorted(component_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    return ReadinessReport(
        release=snapshot.release,
        total_open=total_open,
        p0_open=p0_open,
        p1_open=p1_open,
        daily_close_rate=daily_close_rate,
        estimated_days_remaining=estimated_days_remaining,
        stale_tickets=stale_tickets,
        component_risks=component_risks,
    )


def format_summary(delta: ReleaseDelta, readiness: ReadinessReport) -> str:
    return '\n'.join(
        [
            f'Release {readiness.release}',
            f'New tickets: {len(delta.new_tickets)}',
            f'Closed tickets: {len(delta.closed_tickets)}',
            f'P0 open: {readiness.p0_open}',
            f'P1 open: {readiness.p1_open}',
            f'Daily close rate: {readiness.daily_close_rate:.2f}',
            f'Estimated days remaining: {readiness.estimated_days_remaining}',
        ]
    )


def _ticket_components(ticket: Mapping[str, Any]) -> list[str]:
    raw_components = ticket.get('components')
    if raw_components is None:
        raw_components = ticket.get('component')

    if isinstance(raw_components, list):
        components = [str(component) for component in raw_components if str(component).strip()]
    elif isinstance(raw_components, str):
        components = [raw_components] if raw_components.strip() else []
    else:
        components = []

    return components or ['Unspecified']


def _tickets_by_key(tickets: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {
        str(ticket.get('key')): ticket
        for ticket in tickets
        if ticket.get('key') is not None
    }


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _days_between(start_iso: str, end_iso: str) -> float:
    start = _parse_iso(start_iso)
    end = _parse_iso(end_iso)
    return (end - start).total_seconds() / 86400.0


def _priority_prefix(priority: str) -> str:
    if priority.startswith('P0'):
        return 'P0'
    if priority.startswith('P1'):
        return 'P1'
    return ''


def _is_p0_p1(priority: str) -> bool:
    return _priority_prefix(priority) in {'P0', 'P1'}


def _build_avg_cycle_lookup(
    cycle_stats: list[CycleTimeStats | Mapping[str, Any]],
) -> dict[tuple[str, str], float]:
    lookup: dict[tuple[str, str], float] = {}

    for stat in cycle_stats:
        if isinstance(stat, CycleTimeStats):
            component = stat.component
            priority = stat.priority
            avg_hours = stat.avg_hours
        else:
            component = str(stat.get('component', 'Unspecified'))
            priority = str(stat.get('priority', ''))
            avg_hours = float(stat.get('avg_hours', 0.0) or 0.0)

        lookup[(component, priority)] = avg_hours

    return lookup
