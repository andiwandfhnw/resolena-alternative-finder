"""Linux-available evidence and source checks; not PowerShell runtime validation."""
import hashlib
import importlib.util
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("protocol_tests", HERE / "test_execution.py")
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)


class PatchChecks(unittest.TestCase):
    def setUp(self):
        self.fixture = protocol.ProtocolTests()
        self.fixture.setUp()
        self.log = (HERE / "execution/fixtures/startup-v2-20261014.log").read_bytes()
        self.common = (HERE / "execution/Common.ps1").read_text()

    def test_offload_collection_avoids_automatic_matches_variable(self):
        body = self.common.split("function Test-OffloadText", 1)[1].split("function New-Checkpoint", 1)[0]
        self.assertNotRegex(body, r"(?i)\$matches\b")
        self.assertIn("$layerMatches", body)

    def test_watchdog_uses_exit_aware_owned_process_lookup(self):
        self.assertIn("function Get-OwnedLiveProcess", self.common)
        self.assertIn("Get-OwnedLiveProcess $receipt", (HERE / "execution/Watchdog.ps1").read_text())

    def test_preserved_log_has_full_offload_and_positive_kv(self):
        files = self.fixture.packet(6)
        files["server.stderr.log"] = self.log
        self.assertEqual(protocol.dispatch.runtime_errors(self.fixture.bundle, files), [])
        self.assertIn(b"offloaded 37/37 layers to GPU", self.log)

    def test_missing_or_incomplete_runtime_evidence_denied(self):
        variants = [self.log.replace(b"offloaded 37/37 layers", b"offloaded 36/37 layers"),
            self.log.replace(b"offloaded 37/37 layers", b"offloaded 0/0 layers")]
        for pattern in [rb"offloaded \d+/\d+ layers to GPU", rb"Vulkan0.*RX\s*6800\s*XT", rb"Vulkan0.*model buffer size", rb"Vulkan0.*KV buffer size"]:
            variants.append(re.sub(rb"(?m)^.*" + pattern + rb"[^\r\n]*\r?\n?", b"", self.log))
        for log in variants:
            files = self.fixture.packet(6)
            files["server.stderr.log"] = log
            self.assertTrue(protocol.dispatch.runtime_errors(self.fixture.bundle, files))

    def test_evaluation_payloads_and_scoring_unchanged(self):
        old = HERE.parent / "windows_qwen3_8b_followup_v2/execution"
        names = ["cases.json", "order.json", "config.json", "schema.json", "contract.py", "assess.py", "dispatch.py", "artifacts.json", "runtime-files.json", "Run.ps1", "Base.ps1", "Native.cs", "HardDeadline.cs"]
        names += [str(p.relative_to(old)) for folder in ["prompts", "requests"] for p in (old / folder).rglob("*") if p.is_file()]
        for name in names:
            self.assertEqual((HERE / "execution" / name).read_bytes(), (old / name).read_bytes(), name)


if __name__ == "__main__":
    unittest.main()
