"""Verify this receipt offline; never enter controller native_run."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
FORBIDDEN = []


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn",
                 "socket.connect", "socket.connect_ex", "socket.bind",
                 "ctypes.dlopen", "ctypes.dlsym"}:
        FORBIDDEN.append(event)
        raise RuntimeError("Forbidden during offline receipt verification: " + event)


sys.addaudithook(audit)

from scripts.uc001_granite_acquisition_proxy import proxy
from scripts.uc001_granite_controller import controller


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected(call, exception, expected):
    try:
        call()
    except exception as error:
        assert str(error) == expected, str(error)
    else:
        raise AssertionError("Expected fail-closed rejection: " + expected)


def main():
    path = HERE / "prior-budget.json"
    expected_hash = (HERE / "prior-budget.json.sha256").read_text().split()[0]
    receipt = json.loads(path.read_bytes())
    assert sha(path) == expected_hash
    assert receipt["receipt_schema"] == "uc001-granite-prior-accounting"
    assert type(receipt["receipt_schema_version"]) is int
    assert receipt["receipt_schema_version"] == 1
    assert receipt["bundle_id"] == proxy.BUNDLE
    assert receipt["acquisition_ceiling_bytes"] == proxy.CEILING == controller.DOWNLOAD_CEILING == 10737418240
    assert receipt["allowance_reset_or_renewed"] is False
    assert receipt["execution_authorized"] is False
    assert receipt["accepted_proxy_sha256"] == proxy_hash == controller.PROXY_SHA256
    assert type(receipt["previously_charged_bytes"]) is int
    assert receipt["previously_charged_bytes"] == 0
    assert receipt["accounting_complete"] is True
    assert receipt["evidence"]["basis"] == "explicit_complete_owner_accounting_statement"
    assert receipt["evidence"]["independently_measured_by_codex"] is False
    assert sha(HERE / receipt["evidence"]["file"]) == receipt["evidence"]["sha256"]
    for relative, expected in receipt["preparation_bindings"].items():
        assert sha(ROOT / relative) == expected, relative
    helper_dir = ROOT / "scripts/uc001_granite_controller"
    assert set(receipt["helper_hashes"]) == controller.HELPER_NAMES
    assert all(sha(helper_dir / name) == value for name, value in receipt["helper_hashes"].items())
    assert receipt["frozen_config_sha256"] == controller.FROZEN_CONFIG_SHA256
    frozen = ROOT / "scripts/uc001_granite_contract_v1/config.json"
    assert sha(frozen) == receipt["frozen_config_sha256"]
    assert json.loads(frozen.read_bytes())["runtime"]["revision"] == receipt["runtime_revision"]
    checks = ["versioned_metadata_evidence_and_preparation_hashes"]

    prior = proxy.load_prior(path, expected_hash)
    assert type(prior) is int and prior == 0
    checks.append("actual_proxy_accepts_owner_attested_integer_zero")

    # Synthetic validation input only; no config file or execution entry point.
    cfg = dict(execution_authorized=True, owner="synthetic-preflight-validation-only",
               root=controller.FIXED_ROOT, helper_hashes=receipt["helper_hashes"],
               frozen_config=str(frozen), proxy_helper=str(proxy_path),
               prior_receipt=str(path), prior_sha256=expected_hash)
    validated = controller.validate_native_config(cfg, helper_dir)
    assert type(validated["prior_bytes"]) is int and validated["prior_bytes"] == 0
    checks.append("actual_controller_preflight_accepts_same_receipt")

    rejected(lambda: proxy.load_prior(path, "0" * 64), proxy.ProxyFailure,
             "prior_receipt_hash_differs")
    rejected(lambda: controller.validate_native_config(dict(cfg, prior_sha256="0" * 64), helper_dir),
             controller.ControllerFailure, "native_preflight_failed:prior_receipt_hash_differs")
    checks.append("both_validators_reject_wrong_external_hash")

    with TemporaryDirectory(prefix="granite-prior-offline-") as temp:
        changed = Path(temp) / "prior.json"
        changed.write_bytes(path.read_bytes() + b"\n")
        rejected(lambda: proxy.load_prior(changed, expected_hash), proxy.ProxyFailure,
                 "prior_receipt_hash_differs")
        rejected(lambda: controller.validate_native_config(dict(cfg, prior_receipt=str(changed)), helper_dir),
                 controller.ControllerFailure, "native_preflight_failed:prior_receipt_hash_differs")
        checks.append("both_validators_reject_changed_receipt_bytes")
        incomplete = dict(receipt, accounting_complete=False)
        changed.write_text(json.dumps(incomplete), encoding="utf-8")
        changed_hash = sha(changed)
        rejected(lambda: proxy.load_prior(changed, changed_hash), proxy.ProxyFailure,
                 "prior_accounting_unknown")
        rejected(lambda: controller.validate_native_config(dict(cfg, prior_receipt=str(changed),
                     prior_sha256=changed_hash), helper_dir), controller.ControllerFailure,
                 "native_preflight_failed:prior_accounting_unknown")
        checks.append("both_validators_reject_incomplete_accounting_with_matching_hash")

    rejected(lambda: controller.validate_native_config(dict(cfg, execution_authorized=False), helper_dir),
             controller.ControllerFailure, "native_preflight_failed:native_execution_not_authorized")
    checks.append("separate_controller_execution_gate_remains_closed")
    assert not FORBIDDEN
    checks.append("no_process_network_or_native_symbol_attempts")
    print(json.dumps(dict(offline_receipt_verification_passed=True, checks=checks,
                         prior_bytes=prior, receipt_sha256=expected_hash,
                         native_api_invoked=False, native_binding_verified=False,
                         resource_fit_established=False, execution_config_written=False,
                         acquisition_or_build=False, forbidden_attempts=FORBIDDEN), indent=2))


proxy_path = ROOT / "scripts/uc001_granite_acquisition_proxy/proxy.py"
proxy_hash = sha(proxy_path)
if __name__ == "__main__":
    main()
