import copy
import unittest
from unittest.mock import Mock
from memory_preflight import enforce_preflight


class PreflightLoggingChecks(unittest.TestCase):
    def setUp(self):
        self.config = {"preflight_memory_min_bytes": 4026531840,
                       "scratch_budget_bytes": 6442450944}
        self.rows = []
        self.writer = lambda name, data: self.rows.append((name, data))
        self.clock = lambda: "2026-10-11T00:00:00+00:00"

    def check(self, memory, disk):
        return enforce_preflight(memory, self.config, "/tmp", self.writer,
                                 disk_free=lambda path: disk, timestamp=self.clock,
                                 context=lambda: {"memory.max": "max"})

    def test_memory_failure_records_exact_compared_sample_once(self):
        memory = Mock(return_value=3933028352)
        original = copy.deepcopy(self.config)
        with self.assertRaisesRegex(RuntimeError, "memory"):
            self.check(memory, 7000000000)
        memory.assert_called_once_with()
        name, row = self.rows[0]
        self.assertEqual(name, "preflight_guard.json")
        self.assertEqual(row["measured_available_bytes"], 3933028352)
        self.assertEqual(row["minimum_available_bytes"], 4026531840)
        self.assertEqual(row["utc"], self.clock())
        self.assertEqual(row["failed_guards"], ["memory"])
        self.assertEqual(self.config, original)

    def test_exact_thresholds_pass(self):
        row = self.check(lambda: 4026531840, 6442450944)
        self.assertEqual(row["failed_guards"], [])

    def test_disk_failure_is_identified(self):
        with self.assertRaisesRegex(RuntimeError, "disk"):
            self.check(lambda: 5000000000, 6442450943)
        self.assertEqual(self.rows[0][1]["failed_guards"], ["disk"])

    def test_both_failures_are_recorded(self):
        with self.assertRaises(RuntimeError):
            self.check(lambda: 1, 1)
        self.assertEqual(self.rows[0][1]["failed_guards"], ["memory", "disk"])


if __name__ == "__main__":
    unittest.main()
