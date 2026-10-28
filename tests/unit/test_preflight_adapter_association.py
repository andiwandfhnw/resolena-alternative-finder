from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess
import zipfile

import pytest


PWSH = shutil.which("pwsh")
ROOT = Path("scripts/uc001_preflight_association_v1_1_0")


def test_correction_preserves_pins_budgets_and_original_preparation():
    original = Path("scripts/uc001_contract_check")
    for name in ("config.json", "runtime-files.json"):
        assert (ROOT / name).read_bytes() == (original / name).read_bytes()
    baseline = json.loads(Path("build/uc001-preflight-association-v1_1_0/baseline.json").read_text())
    for name, expected in baseline.items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name


def test_correction_package_matches_new_hashes_and_has_no_launcher():
    freeze = json.loads((ROOT / "freeze.json").read_text())
    assert freeze["version"] == "uc001-preflight-association-v1.1.0"
    archive = Path("build/uc001-preflight-association-v1_1_0/windows-preflight-association-v1_1_0.zip")
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(freeze["files"]) | {"freeze.json"}
        assert "Run-Windows.ps1" not in bundle.namelist()
        for name, expected in freeze["files"].items():
            assert bundle.read(name) == (ROOT / name).read_bytes()
            assert sha256(bundle.read(name)).hexdigest() == expected
        assert bundle.read("freeze.json") == (ROOT / "freeze.json").read_bytes()


@pytest.mark.skipif(PWSH is None, reason="PowerShell unavailable; adapter preflight remains unverified")
@pytest.mark.parametrize("case", [
    "hardware_and_software", "counter_order", "zero_usage", "fresh_luid", "null_flags", "invalid_flags", "wrong_descriptor", "wrong_pci", "wrong_subsystem", "wrong_revision",
    "missing_cim", "duplicate_cim", "missing_registry", "missing_driver", "bad_pnp", "failed_cim", "failed_registry",
    "missing_dxgi", "duplicate_dxgi", "duplicate_luid", "failed_dxgi", "partial_dxgi", "software_only", "software_impersonation", "capacity_mismatch",
    "missing_capacity", "invalid_capacity", "missing_counter", "duplicate_counter", "failed_counter", "missing_usage", "null_usage",
    "invalid_usage", "usage_over_capacity", "counter_name_lookalike", "unexpected_physical_index", "multiple_physical_counters", "headroom_below",
    "headroom_exact", "all_resource_limits", "preflight_routing", "native_layout",
])
def test_corrected_preflight_offline(case):
    result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(ROOT / "Test-Offline.ps1"), "-Case", case],
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS {case}" in result.stdout


CAPACITY_ROOT = Path("scripts/uc001_preflight_capacity_v1_2_0")
CAPACITY_BUILD = Path("build/uc001-preflight-capacity-v1_2_0")


@pytest.mark.skipif(PWSH is None, reason="PowerShell unavailable; DXGI capacity correction remains unverified")
@pytest.mark.parametrize("case", [
    "hardware_and_software", "counter_order", "zero_usage", "fresh_luid", "null_flags", "invalid_flags", "wrong_descriptor", "wrong_pci", "wrong_subsystem", "wrong_revision",
    "missing_cim", "duplicate_cim", "missing_registry", "missing_driver", "bad_pnp", "failed_cim", "failed_registry",
    "missing_dxgi", "duplicate_dxgi", "duplicate_luid", "failed_dxgi", "partial_dxgi", "software_only", "software_impersonation",
    "capacity_mismatch", "capacity_dxgi_lower", "capacity_dxgi_higher", "missing_capacity", "invalid_capacity", "registry_binary", "registry_overflow", "registry_null", "registry_negative",
    "dxgi_capacity_missing", "dxgi_capacity_null", "dxgi_capacity_string", "dxgi_capacity_fraction", "dxgi_capacity_negative", "dxgi_capacity_zero", "dxgi_capacity_overflow",
    "missing_counter", "duplicate_counter", "failed_counter", "missing_usage", "null_usage", "invalid_usage", "usage_over_capacity", "counter_name_lookalike",
    "unexpected_physical_index", "multiple_physical_counters", "headroom_below", "headroom_exact", "all_resource_limits", "threshold_boundaries", "preflight_routing", "native_layout",
])
def test_dxgi_capacity_preflight_offline(case):
    result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(CAPACITY_ROOT / "Test-Offline.ps1"), "-Case", case],
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS {case}" in result.stdout


def test_capacity_correction_preserves_all_prior_bundles_and_limits():
    for name in ("config.json", "runtime-files.json", "AdapterIdentity.cs"):
        assert (CAPACITY_ROOT / name).read_bytes() == (ROOT / name).read_bytes()
    baseline = json.loads((CAPACITY_BUILD / "baseline.json").read_text())
    for name, expected in baseline.items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name


def test_capacity_correction_package_is_complete_and_matches_freeze():
    freeze = json.loads((CAPACITY_ROOT / "freeze.json").read_text())
    assert freeze["version"] == "uc001-preflight-capacity-v1.2.0"
    archive = CAPACITY_BUILD / "windows-preflight-capacity-v1_2_0.zip"
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(freeze["files"]) | {"freeze.json"}
        assert "Run-Windows.ps1" not in bundle.namelist()
        for name, expected in freeze["files"].items():
            assert bundle.read(name) == (CAPACITY_ROOT / name).read_bytes()
            assert sha256(bundle.read(name)).hexdigest() == expected
        assert bundle.read("freeze.json") == (CAPACITY_ROOT / "freeze.json").read_bytes()


@pytest.mark.skipif(PWSH is None, reason="PowerShell unavailable; remaining desktop check unverified")
@pytest.mark.parametrize("case", ["ok", "missing_gh", "wrong_gh", "missing_ssh", "other_ssh", "version_failure", "port_busy", "ports_failed", "version_io"])
def test_remaining_desktop_readiness_offline(case):
    result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", "build/uc001-desktop-readiness/offline-check.ps1", "-Case", case],
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS {case}" in result.stdout


def test_windows_snapshot_scope_and_prior_evidence_preservation():
    root = Path("build/uc001-desktop-readiness")
    raw = json.loads((root / "windows-v1_2_0-result.raw.json").read_text())
    limits = json.loads((CAPACITY_ROOT / "config.json").read_text())["limits"]
    assert raw["limits"] == limits
    assert raw["version"] == "uc001-preflight-capacity-v1.2.0"
    assert raw["outcome"] == "preflight_passed" and raw["association"] == "verified" and raw["error"] is None
    assert raw["resources"]["gpu_free"] - limits["gpu_preflight_free_bytes"] == 13099008
    assert raw["adapter"]["CapacitySource"] == "DXGI_ADAPTER_DESC1.DedicatedVideoMemory"
    assert raw["verification_scope"] == "identity and one resource snapshot only; no model/runtime or transport verification"
    for name, expected in json.loads((root / "baseline.json").read_text()).items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name
