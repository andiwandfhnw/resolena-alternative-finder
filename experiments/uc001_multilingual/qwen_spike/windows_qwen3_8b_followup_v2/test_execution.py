import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent / "execution"
sys.path.insert(0, str(HERE))
import dispatch


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
        self.freeze = encoded({"version": "2.0.0", "files": {
            str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in HERE.rglob("*") if p.is_file() and p.name != "freeze.json" and "__pycache__" not in p.parts}})
        self.bundle = dispatch.Bundle(HERE, self.freeze)

    def output(self, entry):
        c = self.bundle.cases[entry["case"]]
        text, expected = c["text"], c["expected"]
        if expected["status"] == "unsupported":
            return {"status": "unsupported", "language": None,
                "subject": {"value": None, "quote": ""}, "action": {"value": None, "quote": ""},
                "goals": [], "constraints": [], "unresolved": ["Unsupported input; please rephrase in DE/FR/IT/EN."]}
        quotes = {
            "01-C1-known": ["kettle", "Repair", {}], "02-C2-known": ["kettle", "repair", {}],
            "03-C3-known": ["Wasserkocher", "Repariere", {"no_replacement": "ohne ihn zu ersetzen"}],
            "04-C4-known": ["bouilloire", "Répare", {}], "05-C5-known": ["bollitore", "Ripara", {}],
            "F1-DE": ["Drucker", "repariere", {"no_replacement": "ohne ihn zu ersetzen"}],
            "F2-FR": ["ordinateur", "Répare", {"storage_min": "au moins 256 GB"}],
            "F3-IT": ["contenitore", "Riutilizza", {"no_new_purchase": "senza comprarne uno nuovo"}],
            "F4-EN": ["vacuum cleaner", "Repair", {"budget": "85 CHF", "cost_exclusion": "excluding delivery"}],
            "F6-AMB": ["Taxi", "", {}],
        }
        subject, action, constraints = quotes[entry["case"]]
        return {"status": expected["status"], "language": expected["language"],
            "subject": {"value": expected["subject"], "quote": subject},
            "action": {"value": expected["action"], "quote": action}, "goals": [],
            "constraints": [{"kind": k, "value": v, "quote": constraints[k]} for k, v in expected["constraints"].items()],
            "unresolved": []}

    def packet(self, count, change=None):
        run = {"run_id": "synthetic-run", "freeze_sha256": self.bundle.freeze_sha,
            "started_utc": self.now.isoformat(), "deadline_utc": (self.now + timedelta(seconds=1800)).isoformat()}
        files = {"freeze.json": self.freeze, "run.json": encoded(run),
            "server.stderr.log": b"Vulkan0: AMD Radeon RX 6800 XT\nload_tensors: offloaded 33/33 layers to GPU\nload_tensors: Vulkan0 model buffer size = 8000 MiB\nllama_kv_cache: Vulkan0 KV buffer size = 64 MiB\n",
            "server.stdout.log": b"", "resources.jsonl": encoded({"owned_gpu_bytes": 8 * 2**30, "owned_rss_bytes": 2 * 2**30,
                "scratch_bytes": 9 * 2**30, "available_ram_bytes": 24 * 2**30, "adapter_free_bytes": 6 * 2**30,
                "disk_free_bytes": 500 * 2**30}).replace(b"\n", b"") + b"\n",
            "capacity.json": encoded({"context": 2048, "output_tokens": 384, "requests": {
                p["id"]: {"tokens": 800, "request_sha256": self.bundle.request_hash(p), "nonthinking": True}
                for p in self.bundle.order}})}
        receipts = []
        for entry in self.bundle.order[:count]:
            obj = self.output(entry)
            raw = {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)}}],
                "usage": {"prompt_tokens": 800, "completion_tokens": 100, "prompt_tokens_details": {"cached_tokens": 0}},
                "timings": {"cache_n": 0, "prompt_n": 800, "predicted_n": 100, "prompt_ms": 1, "predicted_ms": 1}}
            rec = {"run_id": run["run_id"], "bundle_freeze_sha256": self.bundle.freeze_sha,
                "request_id": entry["id"], "arm": entry["arm"], "case": entry["case"],
                "request_sha256": self.bundle.request_hash(entry), "http_status": 200,
                "wall_seconds": 0.002, "raw_body": json.dumps(raw, ensure_ascii=False)}
            if change:
                change(entry, rec, raw)
            files[entry["request"]] = (HERE / entry["request"]).read_bytes()
            response = "responses/" + entry["id"] + ".json"
            files[response] = encoded(rec)
            receipts.append({"id": entry["id"], "case": entry["case"], "arm": entry["arm"],
                "request_sha256": self.bundle.request_hash(entry), "response_sha256": dispatch.sha(files[response])})
        checkpoint = {"run_id": run["run_id"], "freeze_sha256": self.bundle.freeze_sha,
            "checkpoint_id": f"cp{count:02d}", "nonce": f"synthetic-nonce-{count}",
            "deadline_utc": run["deadline_utc"], "completed_ids": [e["id"] for e in self.bundle.order[:count]],
            "receipts": receipts}
        files["checkpoint.json"] = encoded(checkpoint)
        return files

    def assess(self, files, now=None):
        return dispatch.assess_packet(self.bundle, files, now or self.now + timedelta(seconds=10))

    def test_known_gate_assesses_all_six(self):
        files = self.packet(6)
        assessment, receipt = self.assess(files)
        self.assertEqual(len(assessment["evaluations"]), 6)
        self.assertTrue(receipt["allowed"])
        dispatch.verify_receipt(self.bundle, files, assessment, receipt, self.now + timedelta(seconds=11))

    def test_failing_known_v2_blocks_fresh(self):
        def change(entry, rec, raw):
            if entry["index"] == 3:
                obj = json.loads(raw["choices"][0]["message"]["content"])
                obj["subject"]["value"] = "Wasserkocher"
                raw["choices"][0]["message"]["content"] = json.dumps(obj)
                rec["raw_body"] = json.dumps(raw)
        a, r = self.assess(self.packet(6, change))
        self.assertFalse(r["allowed"])
        self.assertEqual(len(a["evaluations"]), 6)
        self.assertEqual(a["evaluations"][2]["semantic_errors"], [])
        self.assertTrue(a["evaluations"][2]["label_mismatches"])

    def test_v1_content_failure_permitted_v2_failure_stops(self):
        def change(entry, rec, raw):
            if entry["index"] == 7:
                obj = json.loads(raw["choices"][0]["message"]["content"])
                obj["status"] = "unsupported"
                raw["choices"][0]["message"]["content"] = json.dumps(obj)
                rec["raw_body"] = json.dumps(raw)
        a, r = self.assess(self.packet(8, change))
        self.assertTrue(r["allowed"])
        self.assertFalse(a["evaluations"][6]["strict_pass"])
        def v2(entry, rec, raw):
            if entry["index"] == 8:
                obj = json.loads(raw["choices"][0]["message"]["content"])
                obj["constraints"] = []
                raw["choices"][0]["message"]["content"] = json.dumps(obj)
                rec["raw_body"] = json.dumps(raw)
        self.assertFalse(self.assess(self.packet(8, v2))[1]["allowed"])

    def test_either_arm_operational_failure_stops(self):
        for target in [7, 8]:
            def change(entry, rec, raw):
                if entry["index"] == target:
                    raw["choices"][0]["finish_reason"] = "length"
                    rec["raw_body"] = json.dumps(raw)
            self.assertFalse(self.assess(self.packet(8, change))[1]["allowed"])

    def test_wrong_arm_and_wrong_request_are_rejected(self):
        for field, value in [("arm", "v1"), ("request_sha256", "0" * 64), ("bundle_freeze_sha256", "0" * 64)]:
            def change(entry, rec, raw):
                if entry["index"] == 1:
                    rec[field] = value
            with self.assertRaises(ValueError):
                self.assess(self.packet(6, change))

    def test_stale_receipt_rejected(self):
        first = self.packet(6)
        a, r = self.assess(first)
        second = copy.deepcopy(first)
        c = json.loads(second["checkpoint.json"])
        c["nonce"] = "new-active-nonce"
        second["checkpoint.json"] = encoded(c)
        with self.assertRaises(ValueError):
            dispatch.verify_receipt(self.bundle, second, a, r, self.now + timedelta(seconds=11))

    def test_deadline_expiry_refuses_continuation(self):
        files = self.packet(6)
        a, r = self.assess(files)
        with self.assertRaises(ValueError):
            dispatch.verify_receipt(self.bundle, files, a, r, self.now + timedelta(seconds=1800))
        self.assertFalse(self.assess(files, self.now + timedelta(seconds=1800))[1]["allowed"])

    def test_capacity_boundary_and_missing_offload(self):
        files = self.packet(6)
        cap = json.loads(files["capacity.json"])
        cap["requests"][self.bundle.order[0]["id"]]["tokens"] = 1664
        files["capacity.json"] = encoded(cap)
        self.assertTrue(self.assess(files)[1]["allowed"])
        cap["requests"][self.bundle.order[0]["id"]]["tokens"] = 1665
        files["capacity.json"] = encoded(cap)
        self.assertFalse(self.assess(files)[1]["allowed"])
        files = self.packet(6)
        files["server.stderr.log"] = b"Vulkan0: AMD Radeon RX 6800 XT\n"
        self.assertFalse(self.assess(files)[1]["allowed"])

    def test_exact_quote_grounding_not_repaired(self):
        def change(entry, rec, raw):
            if entry["index"] == 1:
                obj = json.loads(raw["choices"][0]["message"]["content"])
                obj["action"]["quote"] = "repair"
                raw["choices"][0]["message"]["content"] = json.dumps(obj)
                rec["raw_body"] = json.dumps(raw)
        a, r = self.assess(self.packet(6, change))
        self.assertFalse(r["allowed"])
        self.assertIn("ungrounded_quote", a["evaluations"][0]["grounding_errors"])

    def test_required_device_and_kv_records_before_generation(self):
        for omitted in [b"Vulkan0: AMD Radeon RX 6800 XT\n", b"llama_kv_cache: Vulkan0 KV buffer size = 64 MiB\n"]:
            files = self.packet(6)
            files["server.stderr.log"] = files["server.stderr.log"].replace(omitted, b"")
            self.assertFalse(self.assess(files)[1]["allowed"])

    def test_all_eight_checkpoints_and_final_v1(self):
        for count in [6, 8, 9, 12, 13, 16, 17, 18]:
            files = self.packet(count)
            a, r = self.assess(files)
            self.assertTrue(r["allowed"], count)
            dispatch.verify_receipt(self.bundle, files, a, r, self.now + timedelta(seconds=11))
        self.assertEqual(a["v2_strict_passes"], 12)
        self.assertEqual(a["v1_request_count"], 6)

    def test_final_export_requires_confirmed_exits_and_cleanup(self):
        files = self.packet(18)
        with self.assertRaises(ValueError):
            dispatch.verify_closeout(files)
        for name in ["server_exit.json", "watchdog_process_exit.json"]:
            files[name] = encoded({"confirmed_exited": True, "exit_code": -1 if name.startswith("server") else 0})
        files["watchdog_exit.json"] = encoded({"status": "server_ended", "exit_code": 0})
        files["cleanup_manifest.json"] = encoded({"artifacts_preserved": True, "files": {}})
        dispatch.verify_closeout(files)
        files["server_exit.json"] = encoded({"confirmed_exited": False})
        with self.assertRaises(ValueError):
            dispatch.verify_closeout(files)

    def test_archive_safety_and_windows_member_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("responses\\case.json", b"{}")
            self.assertEqual(dispatch.read_archive(path), {"responses/case.json": b"{}"})
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("../outside.json", b"{}")
            with self.assertRaises(ValueError):
                dispatch.read_archive(path)
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("responses\\case.json", b"{}")
                z.writestr("responses/case.json", b"{}")
            with self.assertRaises(ValueError):
                dispatch.read_archive(path)

    def test_cli_transfer_and_closeout_on_separate_synthetic_copy(self):
        self.now = datetime.now(timezone.utc)
        files = self.packet(6)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied = root / "bundle"
            shutil.copytree(HERE, copied, ignore=shutil.ignore_patterns("__pycache__", "freeze.json"))
            (copied / "freeze.json").write_bytes(self.freeze)
            archive = root / "cp06.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in files.items():
                    z.writestr(name.replace("/", "\\"), data)
            output = root / "assessed"
            with patch.object(dispatch, "HERE", copied), patch.object(sys, "argv", ["dispatch.py", "assess", str(archive), "--output", str(output)]):
                self.assertEqual(dispatch.main(), 0)
                with self.assertRaises(ValueError):
                    dispatch.main()
            returned = dispatch.read_archive(output / "return-cp06.zip")
            self.assertEqual(returned["assessment.json"], (output / "assessment.json").read_bytes())
            self.assertEqual(returned["receipt.pending.json"], (output / "receipt.json").read_bytes())
            for name in ["server_exit.json", "watchdog_process_exit.json"]:
                files[name] = encoded({"confirmed_exited": True, "exit_code": 0})
            files["watchdog_exit.json"] = encoded({"status": "server_ended", "exit_code": 0})
            files["cleanup_manifest.json"] = encoded({"artifacts_preserved": True, "files": {
                n: {"sha256": dispatch.sha(b), "bytes": len(b)} for n, b in files.items()}})
            for entry in self.bundle.order:
                files[entry["request"]] = (HERE / entry["request"]).read_bytes()
            final = root / "final.zip"
            with zipfile.ZipFile(final, "w") as z:
                for name, data in files.items():
                    z.writestr(name, data)
            with patch.object(dispatch, "HERE", copied), patch.object(sys, "argv", ["dispatch.py", "closeout", str(final), "--output", str(root / "closed")]):
                self.assertEqual(dispatch.main(), 0)
            broken = copy.deepcopy(files)
            broken["freeze.json"] = b"{}"
            with self.assertRaises(ValueError):
                dispatch.verify_closeout(broken, self.bundle)


if __name__ == "__main__":
    unittest.main()
