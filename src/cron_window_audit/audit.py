from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations

from .cron import CronExpression
from .models import AuditConfig, Finding, RunEvent


@dataclass(frozen=True)
class AuditResult:
    events: tuple[RunEvent, ...]
    findings: tuple[Finding, ...]


def audit_schedule(config: AuditConfig, start: datetime, hours: int) -> AuditResult:
    """Simulate configured cron jobs and report schedule risk findings."""
    if hours < 1:
        raise ValueError("hours must be greater than zero")

    events = tuple(_simulate_events(config, start, start + timedelta(hours=hours)))
    findings = [
        *_find_start_collisions(events),
        *_find_runtime_overlaps(events),
        *_find_quiet_runs(events, config),
        *_find_idle_gaps(events, config.max_idle_minutes),
    ]
    return AuditResult(events=events, findings=tuple(findings))


def _simulate_events(
    config: AuditConfig,
    start: datetime,
    end: datetime,
) -> list[RunEvent]:
    """Generate all matching job runs in the requested half-open time window."""
    compiled = [(job, CronExpression.parse(job.cron)) for job in config.jobs]
    cursor = start.replace(second=0, microsecond=0)
    events: list[RunEvent] = []

    while cursor < end:
        for job, expression in compiled:
            if expression.matches(cursor):
                events.append(
                    RunEvent(
                        job=job,
                        starts_at=cursor,
                        ends_at=cursor + timedelta(minutes=job.duration_minutes),
                    )
                )
        cursor += timedelta(minutes=1)

    return sorted(events, key=lambda event: (event.starts_at, event.job.name))


def _find_start_collisions(events: tuple[RunEvent, ...]) -> list[Finding]:
    by_start: dict[datetime, list[RunEvent]] = {}
    for event in events:
        by_start.setdefault(event.starts_at, []).append(event)

    findings: list[Finding] = []
    for starts_at, group in sorted(by_start.items()):
        if len(group) > 1:
            names = tuple(event.job.name for event in group)
            findings.append(
                Finding(
                    severity="high",
                    code="start_collision",
                    message=f"{len(group)} jobs start at the same minute",
                    jobs=names,
                    at=starts_at,
                )
            )
    return findings


def _find_runtime_overlaps(events: tuple[RunEvent, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for left, right in combinations(events, 2):
        if left.job.name == right.job.name:
            continue
        if left.starts_at < right.ends_at and right.starts_at < left.ends_at:
            if left.starts_at == right.starts_at:
                continue
            findings.append(
                Finding(
                    severity="medium",
                    code="runtime_overlap",
                    message="job runtimes overlap",
                    jobs=(left.job.name, right.job.name),
                    at=max(left.starts_at, right.starts_at),
                )
            )
    return findings


def _find_quiet_runs(events: tuple[RunEvent, ...], config: AuditConfig) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        if any(window.contains(event.starts_at.time()) for window in config.quiet_windows):
            findings.append(
                Finding(
                    severity="medium",
                    code="quiet_window",
                    message="job starts inside a quiet window",
                    jobs=(event.job.name,),
                    at=event.starts_at,
                )
            )
    return findings


def _find_idle_gaps(
    events: tuple[RunEvent, ...],
    max_idle_minutes: int | None,
) -> list[Finding]:
    if max_idle_minutes is None or len(events) < 2:
        return []

    findings: list[Finding] = []
    for previous, current in zip(events, events[1:]):
        gap = int((current.starts_at - previous.starts_at).total_seconds() // 60)
        if gap > max_idle_minutes:
            findings.append(
                Finding(
                    severity="low",
                    code="idle_gap",
                    message=f"no job starts for {gap} minutes",
                    jobs=(previous.job.name, current.job.name),
                    at=previous.starts_at,
                )
            )
    return findings
