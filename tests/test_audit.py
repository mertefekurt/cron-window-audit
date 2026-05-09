from datetime import datetime, time
from unittest import TestCase

from cron_window_audit.audit import audit_schedule
from cron_window_audit.models import AuditConfig, CronJob, QuietWindow


class AuditScheduleTest(TestCase):
    def test_finds_collisions_overlaps_and_quiet_runs(self) -> None:
        config = AuditConfig(
            jobs=(
                CronJob("nightly-backup", "0 2 * * *", duration_minutes=90),
                CronJob("index-refresh", "30 2 * * *", duration_minutes=20),
                CronJob("fraud-export", "0 2 * * *", duration_minutes=5),
            ),
            quiet_windows=(QuietWindow(time(22, 0), time(6, 0)),),
        )

        result = audit_schedule(config, datetime(2026, 5, 9, 0, 0), hours=4)
        codes = [finding.code for finding in result.findings]

        self.assertIn("start_collision", codes)
        self.assertIn("runtime_overlap", codes)
        self.assertIn("quiet_window", codes)

    def test_finds_idle_gaps(self) -> None:
        config = AuditConfig(
            jobs=(
                CronJob("early", "0 1 * * *"),
                CronJob("late", "0 8 * * *"),
            ),
            max_idle_minutes=120,
        )

        result = audit_schedule(config, datetime(2026, 5, 9, 0, 0), hours=10)

        self.assertEqual("idle_gap", result.findings[0].code)
