import copy
import unittest
from calibrate import assess


class AssessmentChecks(unittest.TestCase):
    def setUp(self):
        self.expected = {"status": "understood", "language": "en", "subject": "kettle",
                         "action": "repair", "goals": [], "constraints": {}}
        self.output = {"status": "understood", "language": "en",
                       "subject": {"value": "kettle", "quote": "kettle"},
                       "action": {"value": "repair", "quote": "Repair"},
                       "goals": [], "constraints": [], "unresolved": []}

    def test_correct_response_passes_without_mutating_raw_object(self):
        original = copy.deepcopy(self.output)
        result = assess(self.output, "Repair my kettle.", self.expected, "stop")
        self.assertTrue(result["pass"])
        self.assertEqual(self.output, original)

    def test_unsupported_does_not_hide_incorrect_supported_status(self):
        self.output["status"] = "unsupported"
        result = assess(self.output, "Repair my kettle.", self.expected, "stop")
        self.assertFalse(result["status_correct"])
        self.assertTrue(result["meaning_correct"])
        self.assertFalse(result["pass"])
        self.assertEqual(result["frozen_semantic"]["category"], "unsupported")

    def test_case_changed_quote_fails_unchanged_grounding(self):
        self.output["action"]["quote"] = "repair"
        result = assess(self.output, "Repair my kettle.", self.expected, "stop")
        self.assertFalse(result["quotes_grounded"])
        self.assertFalse(result["pass"])

    def test_missing_constraint_and_wrong_language_fail(self):
        self.expected["constraints"] = {"no_replacement": "true"}
        self.expected["language"] = "de"
        result = assess(self.output, "Repair my kettle.", self.expected, "stop")
        self.assertFalse(result["constraints_preserved"])
        self.assertFalse(result["language_correct"])
        self.assertFalse(result["pass"])

    def test_unsupported_needs_explicit_uncertainty(self):
        self.output.update(status="unsupported", language=None)
        expected = {"status": "unsupported", "language": None, "unresolved_nonempty": True}
        result = assess(self.output, "Repair my kettle.", expected, "stop")
        self.assertFalse(result["uncertainty_preserved"])
        self.assertFalse(result["pass"])
        self.output["unresolved"] = ["Unsupported language"]
        self.assertTrue(assess(self.output, "Repair my kettle.", expected, "stop")["pass"])


if __name__ == "__main__":
    unittest.main()
