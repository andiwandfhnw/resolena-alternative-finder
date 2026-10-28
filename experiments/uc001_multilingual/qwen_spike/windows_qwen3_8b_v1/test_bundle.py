"""Offline synthetic gate checks; never starts a server or reads held-out cases."""
import copy
import json
import unittest
from pathlib import Path

import assess


class GateTests(unittest.TestCase):
    def setUp(self):
        self.case = {"id": "C1", "text": "Repair my kettle.", "expected": {
            "status": "understood", "language": "en", "subject": "kettle",
            "action": "repair", "goals": [], "constraints": {}}}
        self.output = {"status": "understood", "language": "en",
            "subject": {"value": "kettle", "quote": "kettle"},
            "action": {"value": "repair", "quote": "Repair"},
            "goals": [], "constraints": [], "unresolved": []}

    def test_correct_known_output_passes(self):
        self.assertTrue(assess.classify(self.case, self.output)["strict_pass"])

    def test_unsupported_does_not_hide_wrong_classification(self):
        self.output.update(status="unsupported", unresolved=["unsupported"])
        result = assess.classify(self.case, self.output)
        self.assertFalse(result["strict_pass"])
        self.assertIn("status", result["semantic_errors"])

    def test_case_changed_quote_fails_even_with_correct_meaning(self):
        self.output["action"]["quote"] = "repair"
        result = assess.classify(self.case, self.output)
        self.assertFalse(result["strict_pass"])
        self.assertTrue(result["grounding_errors"])
        self.assertFalse(result["semantic_errors"])

    def test_normalized_label_mismatch_is_separate_and_blocks_gate(self):
        self.output["subject"]["value"] = "water_kettle"
        result = assess.classify(self.case, self.output)
        self.assertFalse(result["strict_pass"])
        self.assertTrue(result["label_mismatches"])
        self.assertFalse(result["semantic_errors"])

    def test_unsupported_fabricated_constraints_are_semantic_failure(self):
        self.case["expected"] = {"status": "unsupported", "language": None,
            "unresolved_nonempty": True}
        self.output.update(status="unsupported", language=None, unresolved=["Spanish"])
        self.output["constraints"] = [{"kind": "no_repair", "value": "true", "quote": "Repair"}]
        self.assertIn("constraints", assess.classify(self.case, self.output)["semantic_errors"])

    def test_all_saved_known_point_seven_responses_fail_gate(self):
        root = Path(__file__).resolve().parent.parent / "portable_2026_10_11"
        cases = json.loads((root / "cases.json").read_text())["cases"]
        names = ["01-C1-t0.7.json", "04-C2-t0.7.json", "05-C3-t0.7.json",
                 "08-C4-t0.7.json", "09-C5-t0.7.json", "12-C6-t0.7.json"]
        for case, name in zip(cases, names):
            raw = json.loads((root / "responses" / name).read_text())["raw_body"]
            output = json.loads(json.loads(raw)["choices"][0]["message"]["content"])
            with self.subTest(case=case["id"]):
                self.assertFalse(assess.classify(case, output)["strict_pass"])

    def test_numeric_ambiguity_requires_specific_uncertainty(self):
        self.case["expected"] = {"status": "clarification", "language": "en",
            "unresolved_nonempty": True, "uncertainty_terms": ["amount", "numeric", "1,200"],
            "allowed_subjects": [None, "kettle"], "allowed_actions": [None, "repair"]}
        self.output.update(status="clarification", unresolved=["language"])
        self.assertIn("uncertainty_target", assess.classify(self.case, self.output)["semantic_errors"])

    def test_complete_requests_preserve_contract_and_fixed_order(self):
        import contract
        root = Path(__file__).resolve().parent
        cases = json.loads((root / "cases.json").read_text())
        order = json.loads((root / "order.json").read_text())
        self.assertEqual(len(cases["new_cases"]), 24)
        self.assertEqual(len(order), 34)
        self.assertEqual([p["case"] for p in order[:6]], ["C1", "C2", "C3", "C4", "C5", "C6"])
        for row in order:
            request = json.loads((root / row["request"]).read_text())
            self.assertEqual(request["messages"][0]["content"], contract.PROMPT)
            self.assertEqual(request["response_format"]["schema"], contract.SCHEMA)
            self.assertEqual(request["temperature"], .7)
            self.assertEqual(request["seed"], 42)
            self.assertFalse(request["chat_template_kwargs"]["enable_thinking"])
            self.assertFalse(request["cache_prompt"])

    def test_exact_artifact_bytes_fit_decimal_download_cap(self):
        root = Path(__file__).resolve().parent
        artifacts = json.loads((root / "artifacts.json").read_text())
        total = sum(a["bytes"] for a in artifacts["artifacts"])
        self.assertEqual(total, 8742855881)
        self.assertLess(total + artifacts["reserved_bundle_and_metadata_bytes"], 10000000000)

    def test_contract_block_is_verbatim_without_original_import(self):
        root = Path(__file__).resolve().parent
        source = (root.parent / "evaluate_model.py").read_text()
        self.assertEqual((root / "contract.py").read_text(), source[source.index("SUPPORTED="):source.index("class LocalHTTP")])


if __name__ == "__main__":
    unittest.main()
