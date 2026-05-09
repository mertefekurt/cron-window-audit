from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


FIELD_RANGES = (
    (0, 59),
    (0, 23),
    (1, 31),
    (1, 12),
    (0, 7),
)


@dataclass(frozen=True)
class CronExpression:
    minutes: frozenset[int]
    hours: frozenset[int]
    days: frozenset[int]
    months: frozenset[int]
    weekdays: frozenset[int]

    @classmethod
    def parse(cls, expression: str) -> "CronExpression":
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"cron expression must have 5 fields: {expression!r}")

        parsed = [
            _parse_field(raw, minimum, maximum)
            for raw, (minimum, maximum) in zip(parts, FIELD_RANGES)
        ]
        weekdays = frozenset(0 if value == 7 else value for value in parsed[4])
        return cls(parsed[0], parsed[1], parsed[2], parsed[3], weekdays)

    def matches(self, value: datetime) -> bool:
        cron_weekday = (value.weekday() + 1) % 7
        return (
            value.minute in self.minutes
            and value.hour in self.hours
            and value.day in self.days
            and value.month in self.months
            and cron_weekday in self.weekdays
        )


def _parse_field(raw: str, minimum: int, maximum: int) -> frozenset[int]:
    values: set[int] = set()
    for token in raw.split(","):
        values.update(_expand_token(token.strip(), minimum, maximum))
    if not values:
        raise ValueError(f"empty cron field: {raw!r}")
    return frozenset(values)


def _expand_token(token: str, minimum: int, maximum: int) -> range:
    if not token:
        raise ValueError("cron field contains an empty token")

    base, step = _split_step(token)
    if base == "*":
        start, stop = minimum, maximum
    elif "-" in base:
        left, right = base.split("-", 1)
        start, stop = int(left), int(right)
    else:
        start = stop = int(base)

    if start < minimum or stop > maximum or start > stop:
        raise ValueError(f"cron token out of range: {token!r}")
    if step < 1:
        raise ValueError(f"cron step must be positive: {token!r}")
    return range(start, stop + 1, step)


def _split_step(token: str) -> tuple[str, int]:
    if "/" not in token:
        return token, 1
    base, raw_step = token.split("/", 1)
    if not base or not raw_step:
        raise ValueError(f"invalid cron step token: {token!r}")
    return base, int(raw_step)
