import copy
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.uc001_contract_check.controls import RunBudget, verify_effective, load_bundle, check_case_state, verify_authentication


ROOT = Path("scripts/uc001_contract_check")
PWSH_AVAILABLE = shutil.which("pwsh") is not None


def effective():
    return {"total_slots": 1, "build_info": "b11429-d81235049", "model_path": r"C:\ResolenaExperiments\qwen3-8b-v1\Qwen3-8B-Q8_0.gguf",
        "default_generation_settings": {"n_ctx": 8192, "params": {"n_predict": 3072, "seed": 42,
            "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0}}}


LOG = """build 11429 (d81235049)
using device Vulkan0 (AMD Radeon RX 6800 XT)
offloaded 37/37 layers to GPU
n_threads = 2 (n_threads_batch = 2)
n_ctx_seq = 8192
n_batch = 64
n_ubatch = 64
K (f16): 576.00 MiB, V (f16): 576.00 MiB
"""


def test_current_settings_must_be_verified_not_merely_requested():
    verify_effective(effective(), LOG)
    for field, value in [("total_slots", 2), ("build_info", "different"), ("model_path", "other.gguf")]:
        wrong = copy.deepcopy(effective()); wrong[field] = value
        with pytest.raises(ValueError):
            verify_effective(wrong, LOG)
    for old, new in [("37/37", "20/37"), ("8192", "2048"), ("Vulkan0", "CPU"), ("n_batch = 64", "n_batch = 128"), ("f16", "q8_0")]:
        with pytest.raises(ValueError):
            verify_effective(effective(), LOG.replace(old, new))
    wrong = effective(); wrong["default_generation_settings"]["params"]["temperature"] = 0.0
    with pytest.raises(ValueError):
        verify_effective(wrong, LOG)


def test_budget_is_fixed_order_count_deadline_and_consumes_before_attempt(tmp_path):
    now = [100.0]
    budget = RunBudget(tmp_path / "ledger.jsonl", ["a", "b"], 140, clock=lambda: now[0])
    with pytest.raises(ValueError):
        budget.consume("b")
    budget.consume("a")
    with pytest.raises(ValueError):
        budget.consume("a")
    now[0] = 140
    with pytest.raises(TimeoutError):
        budget.consume("b")
    assert len((tmp_path / "ledger.jsonl").read_text().splitlines()) == 1
    with pytest.raises(FileExistsError):
        RunBudget(tmp_path / "ledger.jsonl", ["a", "b"], 150)


def test_frozen_manifest_reconciles_meaning_uncertainty_before_language_preference():
    bundle = load_bundle(ROOT)
    cases = bundle["cases"]["cases"]
    assert len(cases) == 14 and [c["id"] for c in cases] == list(range(1, 15))
    assert bundle["cases"]["qualified_review"]["status"] == "pending"
    velo = cases[8]
    assert velo["text"] == "Velo"
    assert velo["allowed_meaning_states"] == ["needs_clarification"]
    assert "veil" in velo["expected_meaning"] and "bicycle" in velo["expected_meaning"]
    assert cases[9]["allowed_meaning_states"] == ["needs_clarification", "understood"]
    assert cases[9]["required_unresolved_quantity"] is True
    assert cases[6]["allowed_meaning_states"] == ["understood", "needs_clarification", "unsupported"]


def test_machine_state_gate_is_not_semantic_approval():
    bundle = load_bundle(ROOT)
    case = bundle["cases"]["cases"][0]
    with pytest.raises(ValueError):
        check_case_state(case, {"meaning_status": "understood", "recognition": {"status": "supported", "language": "en"}})
    check_case_state(case, {"meaning_status": "unsupported", "recognition": {"status": "unsupported", "language": None}, "message": "Rephrase in DE/FR/IT/EN"})


def test_no_execute_flag_starts_no_network_or_process():
    result = subprocess.run([".venv/bin/python", "-m", "scripts.uc001_contract_check.run"], capture_output=True, text=True)
    assert result.returncode == 2 and "--execute" in result.stderr


@pytest.mark.skipif(not PWSH_AVAILABLE, reason="PowerShell is unavailable; Windows script syntax remains unverified")
def test_powershell_scripts_parse_offline_without_running_windows_commands():
    command = "$errors=@(); Get-ChildItem scripts/uc001_contract_check/*.ps1 | ForEach-Object { $t=$null; $e=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$t,[ref]$e); $errors+= $e }; if($errors.Count){$errors | Out-String | Write-Error; exit 1}"
    result = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("unguarded", [False, True])
def test_protected_endpoint_authentication_proof_does_not_use_public_health(unguarded):
    import httpx
    seen = []
    def handle(request):
        seen.append(request)
        assert request.url.path == "/v1/models"
        valid = request.headers.get("Authorization") == "Bearer correct"
        return httpx.Response(200 if valid or unguarded else 401,
            json={"data": [{"id": "uc001-qwen3-8b"}]})
    with httpx.Client(base_url="http://127.0.0.1:49188", headers={"Authorization": "Bearer correct"}, transport=httpx.MockTransport(handle)) as client:
        if unguarded:
            with pytest.raises(ValueError):
                verify_authentication(client)
        else:
            verify_authentication(client)
            assert "Authorization" not in seen[0].headers
            assert seen[1].headers["Authorization"] == "Bearer deliberately-invalid"
            assert seen[2].headers["Authorization"] == "Bearer correct"


@pytest.mark.skipif(not PWSH_AVAILABLE, reason="PowerShell is unavailable; synthetic Windows guards remain unverified")
def test_windows_resource_caps_and_floors_with_synthetic_samples_only():
    command = r'''
    . ./scripts/uc001_contract_check/Common.ps1
    $limits=(Read-ContractJson ./scripts/uc001_contract_check/config.json).limits
    $good=@{ram_free=24GB;gpu_free=15GB;disk_free=10GB;owned_gpu=1GB;owned_rss=1GB;artifact_bytes=0}
    Assert-ContractResources $good $limits $true
    foreach($key in @('ram_free','gpu_free','disk_free','owned_gpu','owned_rss','artifact_bytes')) {
        $bad=$good.Clone()
        if($key -in @('ram_free','gpu_free','disk_free')) {$bad[$key]=0} else {$bad[$key]=32GB}
        $rejected=$false
        try {Assert-ContractResources $bad $limits} catch {$rejected=$true}
        if(-not $rejected){throw "Guard missed $key"}
    }
    Add-Type -Path ./scripts/uc001_contract_check/Dxgi.cs
    Add-Type -Path ./scripts/uc001_contract_check/ProcessTools.cs
    '''
    result = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_qualified_review_gate_rejects_unapproved_machine_expectations():
    from scripts.uc001_contract_check.run import require_review
    with pytest.raises(ValueError):
        require_review(ROOT / "review-template.json", "a" * 64)


def test_schema_configuration_and_source_are_frozen():
    from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter, WireResult
    bundle = load_bundle(ROOT)
    assert json.loads((ROOT / "schema.json").read_text()) == WireResult.model_json_schema()
    assert bundle["config"]["context"] == LlamaCppInterpreter.CONTEXT
    assert bundle["config"]["output_tokens"] == LlamaCppInterpreter.OUTPUT
    assert bundle["config"]["sampling"] == LlamaCppInterpreter.SAMPLING


@pytest.mark.skipif(not PWSH_AVAILABLE, reason="PowerShell is unavailable; synthetic Windows capacity probe remains unverified")
def test_read_only_windows_capacity_probe_uses_64_bit_active_device_data():
    command = r'''
    . ./scripts/uc001_contract_check/Common.ps1
    function Get-CimInstance($ClassName) {
        if($ClassName -eq 'Win32_VideoController') { return [pscustomobject]@{Name='AMD Radeon RX 6800 XT';PNPDeviceID='PCI\synthetic'} }
        return [pscustomobject]@{Name='luid_0x00000000_0x00000001_phys_0';DedicatedUsage=1GB}
    }
    function Get-ItemProperty($LiteralPath) {
        if($LiteralPath -like '*\Enum\*') {return [pscustomobject]@{Driver='{synthetic}\0000'}}
        return [pscustomobject]@{'HardwareInformation.qwMemorySize'=16GB}
    }
    $adapter=Get-ReadOnlyContractAdapter
    if($adapter.DedicatedBytes -ne 16GB -or $adapter.CounterKey -ne 'luid_0x00000000_0x00000001') {throw 'Wrong active 64-bit GPU capacity/mapping'}
    '''
    result = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
