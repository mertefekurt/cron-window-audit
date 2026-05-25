from __future__ import annotations

import json
from datetime import time
from pathlib import Path
from typing import Any

from .models import AuditConfig, CronJob, QuietWindow


def load_config(path: Path) -> AuditConfig:
    """Load and validate a JSON audit configuration file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = tuple(_parse_job(item) for item in data.get("jobs", []))
    quiet_windows = tuple(
        _parse_quiet_window(item) for item in data.get("quiet_hours", [])
    )
    max_idle = data.get("max_idle_minutes")

    if not jobs:
        raise ValueError("config must define at least one job")
    if max_idle is not None and int(max_idle) < 1:
        raise ValueError("max_idle_minutes must be greater than zero")

    return AuditConfig(
        jobs=jobs,
        quiet_windows=quiet_windows,
        max_idle_minutes=None if max_idle is None else int(max_idle),
    )


def _parse_job(data: dict[str, Any]) -> CronJob:
    try:
        name = str(data["name"])
        cron = str(data["cron"])
    except KeyError as exc:
        raise ValueError(f"job is missing required field: {exc.args[0]}") from exc

    duration = int(data.get("duration_minutes", 1))
    if duration < 1:
        raise ValueError(f"job duration must be greater than zero: {name}")

    return CronJob(
        name=name,
        cron=cron,
        duration_minutes=duration,
        tags=tuple(str(tag) for tag in data.get("tags", [])),
    )


def _parse_quiet_window(data: dict[str, Any]) -> QuietWindow:
    try:
        return QuietWindow(
            start=_parse_time(str(data["start"])),
            end=_parse_time(str(data["end"])),
        )
    except KeyError as exc:
        raise ValueError(f"quiet window is missing required field: {exc.args[0]}") from exc


def _parse_time(raw: str) -> time:
    hour, minute = raw.split(":", 1)
    return time(hour=int(hour), minute=int(minute))
