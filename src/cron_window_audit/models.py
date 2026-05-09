from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass(frozen=True)
class CronJob:
    name: str
    cron: str
    duration_minutes: int = 1
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuietWindow:
    start: time
    end: time

    def contains(self, value: time) -> bool:
        if self.start <= self.end:
            return self.start <= value < self.end
        return value >= self.start or value < self.end


@dataclass(frozen=True)
class AuditConfig:
    jobs: tuple[CronJob, ...]
    quiet_windows: tuple[QuietWindow, ...] = ()
    max_idle_minutes: int | None = None


@dataclass(frozen=True)
class RunEvent:
    job: CronJob
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    jobs: tuple[str, ...] = field(default_factory=tuple)
    at: datetime | None = None
