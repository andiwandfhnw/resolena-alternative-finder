import unittest

from supervise import check_limits, owned_identity, required_clear_correct


class Operations(unittest.TestCase):
    def test_deadline_is_not_extended(self):
        with self.assertRaisesRegex(RuntimeError, 'deadline'):
            check_limits(10, 10, 0, 0)

    def test_memory_and_scratch_limits(self):
        for rss, scratch in [(1073741825, 0), (0, 1073741825)]:
            with self.assertRaises(RuntimeError):
                check_limits(1, 10, rss, scratch)
        check_limits(1, 10, 1073741824, 1073741824)

    def test_live_identity_mismatch_is_not_owned(self):
        self.assertFalse(owned_identity(12, 99, {'pid': 12, 'start_ticks': 100, 'pgrp': 12}))
        self.assertFalse(owned_identity(12, 99, {'pid': 12, 'start_ticks': 99, 'pgrp': 14}))
        self.assertTrue(owned_identity(12, 99, {'pid': 12, 'start_ticks': 99, 'pgrp': 12}))

    def test_unsupported_misclassification_cannot_pass(self):
        self.assertFalse(required_clear_correct({'required_clear_top1': 'es'}, 'en'))
        self.assertTrue(required_clear_correct({'required_clear_top1': 'es'}, 'es'))
        self.assertIsNone(required_clear_correct({'expected_language_candidates': None}, 'en'))


if __name__ == '__main__':
    unittest.main()
