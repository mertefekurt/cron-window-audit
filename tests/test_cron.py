from datetime import datetime
from unittest import TestCase

from cron_window_audit.cron import CronExpression


class CronExpressionTest(TestCase):
    def test_matches_steps_and_ranges(self) -> None:
        expression = CronExpression.parse("*/15 9-17 * * 1-5")

        self.assertTrue(expression.matches(datetime(2026, 5, 11, 9, 30)))
        self.assertFalse(expression.matches(datetime(2026, 5, 11, 8, 30)))
        self.assertFalse(expression.matches(datetime(2026, 5, 10, 9, 30)))

    def test_rejects_invalid_field_count(self) -> None:
        with self.assertRaises(ValueError):
            CronExpression.parse("* * *")
