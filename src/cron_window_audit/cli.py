from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .audit import audit_schedule
from .config import load_config
from .formatters import format_json, format_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cron-window-audit",
        description="Audit cron schedules for collisions, quiet-hour runs, and idle gaps.",
    )
    parser.add_argument("config", type=Path, help="Path to a JSON schedule config.")
    parser.add_argument(
        "--from",
        dest="start",
        default=None,
        help="Start time in ISO format, for example 2026-05-09T00:00.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to simulate.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with status 1 when findings exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        start = _parse_start(args.start)
        result = audit_schedule(config, start=start, hours=args.hours)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    output = format_json(result) if args.format == "json" else format_table(result)
    print(output)
    return 1 if args.exit_code and result.findings else 0


def _parse_start(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now().replace(second=0, microsecond=0)
    return datetime.fromisoformat(raw)


if __name__ == "__main__":
    sys.exit(main())
