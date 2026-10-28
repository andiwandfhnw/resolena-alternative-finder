import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.uc001_granite_contract_v1.package import (
    accept_review, check_approval, freeze_files, reserve_generation, verify_archive,
    verify_files, write_archive,
)


def test_transfer_preserves_current_bytes_and_detects_tampering(tmp_path):
    source = tmp_path / "src/app/current.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"uncommitted current work\n")
    frozen = freeze_files(tmp_path, ["src/app/current.py"])
    archive = tmp_path / "transfer.zip"
    write_archive(tmp_path, frozen, archive)
    verify_archive(archive, frozen)
    with ZipFile(archive) as value:
        assert value.read("src/app/current.py") == source.read_bytes()
    source.write_bytes(b"later changed work\n")
    with pytest.raises(ValueError):
        verify_files(tmp_path, frozen)
    with ZipFile(archive, "w") as value:
        value.writestr("src/app/current.py", b"tampered")
    with pytest.raises(ValueError):
        verify_archive(archive, frozen)


@pytest.mark.parametrize("name", ["../outside.txt", ".env", "build/private.sqlite3", "experiments/held_out.json"])
def test_transfer_rejects_unsafe_or_private_paths(tmp_path, name):
    with pytest.raises(ValueError):
        freeze_files(tmp_path, [name])


def test_transfer_rejects_symlinks_and_unexpected_archive_members(tmp_path):
    source = tmp_path / "src/app/real.py"
    source.parent.mkdir(parents=True)
    source.write_text("current\n")
    link = source.with_name("link.py")
    link.symlink_to(source)
    with pytest.raises(ValueError):
        freeze_files(tmp_path, ["src/app/link.py"])
    frozen = freeze_files(tmp_path, ["src/app/real.py"])
    archive = tmp_path / "transfer.zip"
    write_archive(tmp_path, frozen, archive)
    with ZipFile(archive, "a") as value:
        value.writestr("../outside.py", b"not allowed")
    with pytest.raises(ValueError):
        verify_archive(archive, frozen)


def test_generation_reservations_are_ordered_single_attempt_and_closed_on_failure():
    cases = [f"case-{i}" for i in range(11)]
    ledger = {"bundle_id": "frozen", "generation_attempts": [], "closed": False}
    reserve_generation(ledger, cases[0], cases, "frozen")
    assert ledger["generation_attempts"] == [cases[0]]
    for case in (cases[0], cases[2]):
        with pytest.raises(ValueError):
            reserve_generation(ledger, case, cases, "frozen")
    ledger["closed"] = True
    with pytest.raises(ValueError):
        reserve_generation(ledger, cases[1], cases, "frozen")
    ledger["closed"] = False
    for case in cases[1:]:
        reserve_generation(ledger, case, cases, "frozen")
    with pytest.raises(ValueError):
        reserve_generation(ledger, "twelfth", cases + ["twelfth"], "frozen")


def test_approval_and_review_require_explicit_bound_owner_attestations():
    with pytest.raises(ValueError):
        check_approval({}, "frozen")
    approval = {"bundle_id": "frozen", "owner": "owner", "authorized_on": "2026-10-25",
        "acquisition_approved": True, "build_approved": True, "live_execution_approved": True,
        "maximum_startups": 1, "maximum_generations": 11,
        "desktop_prerequisites_and_resource_supervision_confirmed": True}
    check_approval(approval, "frozen")
    with pytest.raises(ValueError):
        check_approval({**approval, "maximum_generations": 12}, "frozen")
    review = {"bundle_id": "frozen", "case_id": "g01-de", "packet_sha256": "packet",
        "semantic_status": "pass", "qualified_review_status": "confirmed",
        "reviewer": "competent reviewer", "competence_basis": "documented source-language competence"}
    accept_review(review, "frozen", "g01-de", "packet")
    for changed in ({"qualified_review_status": "pending"}, {"semantic_status": "fail"},
            {"packet_sha256": "other"}, {"competence_basis": ""}):
        with pytest.raises(ValueError):
            accept_review({**review, **changed}, "frozen", "g01-de", "packet")


def test_assessment_without_separate_approval_cannot_create_output_or_interpreter(tmp_path, monkeypatch):
    from scripts.uc001_granite_contract_v1 import assess
    monkeypatch.setattr(assess, "load_frozen", lambda root: {"bundle_id": "frozen"})
    monkeypatch.setattr(assess, "GraniteInterpreter", lambda *a, **k: pytest.fail("No model transport may be created"))
    output = tmp_path / "build/test-only/not-authorized"
    with pytest.raises(ValueError):
        assess.run_assessment(tmp_path, {}, output)
    assert not output.exists()


def test_unavailable_or_unqualified_review_cannot_continue(tmp_path):
    from scripts.uc001_granite_contract_v1.assess import wait_review
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"qualified_review_status": "pending"}))
    with pytest.raises(ValueError):
        wait_review(review, "frozen", "g01-de", "packet", 1000, clock=lambda: 0)
    review.unlink()
    times = iter([0, 0, 121])
    with pytest.raises(TimeoutError):
        wait_review(review, "frozen", "g01-de", "packet", 1000,
            clock=lambda: next(times), sleep=lambda _: None)


def test_frozen_schema_prompt_cases_and_permissions_match_the_adapter():
    from hashlib import sha256
    from app.infrastructure.granite_interpreter import GraniteInterpreter, transport_schema
    from app.infrastructure.llama_cpp_interpreter import WireResult
    from scripts.uc001_granite_contract_v1.package import PACKAGE, canonical, validate_cases
    root = Path(__file__).resolve().parents[2]
    folder = root / PACKAGE
    config = json.loads((folder / "config.json").read_text())
    assert json.loads((folder / "wire-schema.json").read_text()) == WireResult.model_json_schema()
    schema = json.loads((folder / "schema.json").read_text())
    assert schema == transport_schema()
    system = (folder / "system-prompt.txt").read_bytes()
    assert system == (folder / "prompt.txt").read_bytes() + b"\n\nJSON_SCHEMA:\n" + canonical(schema) + b"\n"
    assert sha256(system).hexdigest() == config["system_prompt_sha256"]
    cases = validate_cases(root)["cases"]
    assert all(case["text"].encode() not in system for case in cases)
    assert config["native_request_settings"] == GraniteInterpreter.REQUEST_SETTINGS
    assert config["model_alias"] == GraniteInterpreter.MODEL
    args = config["server_arguments"]
    assert args[args.index("--alias") + 1] == config["model_alias"]
    assert args.count("--no-warmup") == 1
    assert config["operational_limits"]["maximum_total_inferences"] == 11
    assert config["application_observation"]["additional_generations"] == 0
    assert config["current_permissions"]["adapter_offline_preparation"] is True
    assert all(value is False for key, value in config["current_permissions"].items() if key != "adapter_offline_preparation")
    with pytest.raises(ValueError):
        check_approval(json.loads((folder / "approval-template.json").read_text()), "frozen")


def test_runtime_props_is_one_bounded_mocked_metadata_request():
    import httpx
    import time
    from app.infrastructure.granite_interpreter import GraniteInterpreter
    from scripts.uc001_granite_contract_v1.assess import runtime_properties
    seen = []
    def handle(request):
        seen.append(request.url.path)
        return httpx.Response(200, json={"total_slots": 1})
    with GraniteInterpreter("http://127.0.0.1:9931", "offline-test-secret", "synthetic prompt",
            transport=httpx.MockTransport(handle)) as adapter:
        assert runtime_properties(adapter, time.monotonic() + 10) == {"total_slots": 1}
    assert seen == ["/props"]


def test_runtime_metadata_requires_pinned_build_and_case_states_cannot_be_waived():
    from hashlib import sha256
    from types import SimpleNamespace
    from scripts.uc001_granite_contract_v1.assess import validate_runtime_metadata, validate_case_state
    revision = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
    config = {"runtime": {"revision": revision}, "candidate": {"expected_template_sha256": sha256(b"template").hexdigest()}}
    from app.infrastructure.granite_interpreter import GraniteInterpreter
    props = {"total_slots": 1, "default_generation_settings": {"n_ctx": 8192},
        "model_alias": GraniteInterpreter.MODEL, "chat_template": "template", "build_info": "b0-" + revision}
    validate_runtime_metadata(props, config)
    for build in ("unknown", "b0-deadbee", {"commit": revision}):
        with pytest.raises(ValueError):
            validate_runtime_metadata({**props, "build_info": build}, config)
    with pytest.raises(ValueError):
        validate_case_state(SimpleNamespace(meaning_status="understood"), {"acceptable_meaning_states": ["unsupported", "needs_clarification"]})
    validate_case_state(SimpleNamespace(meaning_status="needs_clarification"), {"acceptable_meaning_states": ["needs_clarification"]})


def test_failed_generation_closes_ledger_without_retry_or_next_case(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from scripts.uc001_granite_contract_v1 import assess
    from scripts.uc001_granite_contract_v1.package import PACKAGE
    import httpx
    root = tmp_path
    folder = root / PACKAGE
    folder.mkdir(parents=True)
    prompt = "frozen synthetic system"
    from hashlib import sha256
    (folder / "system-prompt.txt").write_text(prompt)
    (folder / "config.json").write_text(json.dumps({"endpoint": "http://127.0.0.1:9931",
        "system_prompt_sha256": sha256(prompt.encode()).hexdigest(), "operational_limits": {"assessment_seconds": 1800},
        "candidate": {"expected_template_sha256": sha256(b"template").hexdigest()},
        "runtime": {"revision": "620d2225cc436ab0b001e3200e590e3b286ef9ab"}}))
    calls = []
    class PreparedFailure:
        MODEL = "synthetic-alias"
        TIMEOUT = 120
        def __init__(self, *args): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def interpret(self, text):
            self.before_generation(text)
            calls.append(text)
            raise httpx.ReadTimeout("mocked transport failure")
    monkeypatch.setattr(assess, "GraniteInterpreter", PreparedFailure)
    monkeypatch.setattr(assess, "load_frozen", lambda root: {"bundle_id": "frozen"})
    monkeypatch.setattr(assess, "check_approval", lambda *args: None)
    monkeypatch.setattr(assess, "check_dependencies", lambda *args: None)
    monkeypatch.setattr(assess, "validate_cases", lambda root: {"cases": [{"id": "first", "text": "input"}, {"id": "second", "text": "next"}]})
    monkeypatch.setattr(assess, "runtime_properties", lambda *args: {"total_slots": 1,
        "default_generation_settings": {"n_ctx": 8192}, "model_alias": "synthetic-alias", "chat_template": "template",
        "build_info": "b0-620d2225cc436ab0b001e3200e590e3b286ef9ab"})
    monkeypatch.setenv("RESOLENA_GRANITE_API_KEY", "offline-test-secret")
    output = root / "build/test-only/one-offline-attempt"
    with pytest.raises(httpx.ReadTimeout):
        assess.run_assessment(root, {"assessment_start_utc": datetime.now(timezone.utc).isoformat()}, output)
    ledger = json.loads((output / "ledger.json").read_text())
    assert calls == ["input"] and ledger["generation_attempts"] == ["first"]
    assert ledger["closed"] is True and ledger["structural_results"] == []
