from __future__ import annotations

import json
from dataclasses import asdict

from .audit import AuditResult
from .models import Finding


def format_table(result: AuditResult) -> str:
    if not result.findings:
        return f"ok: {len(result.events)} scheduled runs, no findings"

    rows = [
        ("severity", "code", "time", "jobs", "message"),
        *[_finding_row(finding) for finding in result.findings],
    ]
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    lines = [_render_row(rows[0], widths), _render_row(tuple("-" * w for w in widths), widths)]
    lines.extend(_render_row(row, widths) for row in rows[1:])
    return "\n".join(lines)


def format_json(result: AuditResult) -> str:
    payload = {
        "events": [
            {
                "job": event.job.name,
                "starts_at": event.starts_at.isoformat(timespec="minutes"),
                "ends_at": event.ends_at.isoformat(timespec="minutes"),
            }
            for event in result.events
        ],
        "findings": [_finding_payload(finding) for finding in result.findings],
    }
    return json.dumps(payload, indent=2)


def _finding_row(finding: Finding) -> tuple[str, str, str, str, str]:
    return (
        finding.severity,
        finding.code,
        "" if finding.at is None else finding.at.isoformat(timespec="minutes"),
        ", ".join(finding.jobs),
        finding.message,
    )


def _finding_payload(finding: Finding) -> dict[str, object]:
    payload = asdict(finding)
    payload["at"] = None if finding.at is None else finding.at.isoformat(timespec="minutes")
    return payload


def _render_row(row: tuple[str, ...], widths: list[int]) -> str:
    return "  ".join(value.ljust(width) for value, width in zip(row, widths))
