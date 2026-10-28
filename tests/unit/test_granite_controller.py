import math

import pytest

from scripts.uc001_granite_controller.controller import ControllerFailure, SafetyState


INITIAL_DISK = 51539607552
DISK_FLOOR = 8589934592
HOST_FLOOR = 4294967296
MEMORY_CAP = 25769803776
OUTPUT_CAP = 12884901888


def observation(now, **changes):
    value = {
        "sampled_mono": now,
        "disk_free_bytes": INITIAL_DISK,
        "host_free_bytes": 32 * 1024**3,
        "job_committed_bytes": 1024,
        "build_output_bytes": 0,
    }
    value.update(changes)
    return value


def initialized_guard(start=100.0):
    guard = SafetyState(started_mono=start, max_observation_age=1.0)
    guard.assess("acquisition", start, observation(start))
    return guard


def test_initial_disk_at_frozen_minimum_is_allowed():
    guard = SafetyState(started_mono=100.0)
    guard.assess("acquisition", 100.0, observation(100.0, disk_free_bytes=INITIAL_DISK))


def test_initial_disk_one_byte_below_minimum_prevents_work():
    guard = SafetyState(started_mono=100.0)
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 100.0, observation(100.0, disk_free_bytes=INITIAL_DISK - 1))


def test_acquisition_uses_one_original_deadline_across_steps():
    guard = initialized_guard()
    guard.assess("acquisition", 700.0, observation(700.0))  # initialization/proxy time consumed
    guard.assess("acquisition", 1899.999, observation(1899.999))
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 1900.0, observation(1900.0))


def test_configure_and_build_share_the_same_2700_second_budget():
    guard = initialized_guard()
    guard.start_build(1100.0)
    guard.assess("configure", 2000.0, observation(2000.0))
    guard.assess("build", 3799.999, observation(3799.999))
    with pytest.raises(ControllerFailure):
        guard.assess("build", 3800.0, observation(3800.0))


def test_configure_has_no_hidden_extra_build_allowance():
    guard = initialized_guard()
    guard.start_build(1100.0)
    with pytest.raises(ControllerFailure):
        guard.assess("configure", 3800.0, observation(3800.0))


def test_build_clock_cannot_be_reset_between_subphases():
    guard = initialized_guard()
    guard.start_build(1100.0)
    guard.assess("configure", 2000.0, observation(2000.0))
    with pytest.raises(ControllerFailure):
        guard.start_build(2000.0)


def test_build_without_anchored_phase_clock_fails_closed():
    guard = initialized_guard()
    with pytest.raises(ControllerFailure):
        guard.assess("build", 1100.0, observation(1100.0))


@pytest.mark.parametrize("field,limit", [
    ("job_committed_bytes", MEMORY_CAP),
    ("build_output_bytes", OUTPUT_CAP),
])
def test_memory_and_build_output_equal_to_cap_are_allowed(field, limit):
    guard = initialized_guard()
    guard.start_build(200.0)
    guard.assess("build", 200.0, observation(200.0, **{field: limit}))


@pytest.mark.parametrize("field,limit", [
    ("job_committed_bytes", MEMORY_CAP),
    ("build_output_bytes", OUTPUT_CAP),
])
def test_memory_or_build_output_one_byte_over_is_failure(field, limit):
    guard = initialized_guard()
    guard.start_build(200.0)
    with pytest.raises(ControllerFailure):
        guard.assess("build", 200.0, observation(200.0, **{field: limit + 1}))


@pytest.mark.parametrize("field,limit", [
    ("disk_free_bytes", DISK_FLOOR),
    ("host_free_bytes", HOST_FLOOR),
])
def test_host_headroom_at_floor_is_allowed_after_initial_check(field, limit):
    guard = initialized_guard()
    guard.assess("acquisition", 101.0, observation(101.0, **{field: limit}))


@pytest.mark.parametrize("field,limit", [
    ("disk_free_bytes", DISK_FLOOR),
    ("host_free_bytes", HOST_FLOOR),
])
def test_host_headroom_one_byte_below_floor_stops(field, limit):
    guard = initialized_guard()
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 101.0, observation(101.0, **{field: limit - 1}))


def test_stale_resource_observation_cannot_be_treated_as_current():
    guard = initialized_guard()
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 102.001, observation(101.0))


def test_observation_at_maximum_age_uses_the_declared_staleness_bound():
    guard = initialized_guard()
    guard.assess("acquisition", 102.0, observation(101.0))


@pytest.mark.parametrize("missing", [
    "sampled_mono", "disk_free_bytes", "host_free_bytes", "job_committed_bytes", "build_output_bytes"
])
def test_missing_observation_is_failure_not_zero(missing):
    guard = initialized_guard()
    sample = observation(101.0)
    del sample[missing]
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 101.0, sample)


@pytest.mark.parametrize("field,value", [
    ("sampled_mono", math.nan),
    ("sampled_mono", math.inf),
    ("sampled_mono", 102.0),
    ("disk_free_bytes", None),
    ("disk_free_bytes", -1),
    ("disk_free_bytes", True),
    ("host_free_bytes", "unknown"),
    ("job_committed_bytes", math.nan),
    ("build_output_bytes", -1),
])
def test_failed_or_invalid_measurement_cannot_pass(field, value):
    guard = initialized_guard()
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 101.0, observation(101.0, **{field: value}))


def test_monotonic_clock_cannot_move_backwards_to_restore_budget():
    guard = initialized_guard()
    guard.assess("acquisition", 102.0, observation(102.0))
    with pytest.raises(ControllerFailure):
        guard.assess("acquisition", 101.0, observation(101.0))


def test_unknown_phase_cannot_create_an_unbounded_execution_window():
    guard = initialized_guard()
    with pytest.raises(ControllerFailure):
        guard.assess("unbounded", 101.0, observation(101.0))


def proxy_ledger(tmp_path, prior=7, pid=1234):
    from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING, utc
    path = tmp_path / "proxy.jsonl"
    ledger = BudgetLedger(path, allowance=CEILING, prior_bytes=prior)
    try:
        ledger.record("acquisition_clock", acquisition_started_utc=utc(), remaining_seconds=1799.0)
        ledger.record("listening", address=["127.0.0.1", 12345], pid=pid)
        ledger.record("tunnel_start", "one", "github.com:443")
        ledger.charge("one", "github.com:443", b"abc")
        ledger.record("tunnel_start", "two", "github.com:443")
        ledger.charge("two", "github.com:443", b"de")
        ledger.record("tunnel_end", "one", "github.com:443", reason="upstream_eof")
        ledger.record("tunnel_end", "two", "github.com:443", reason="client_eof")
        ledger.record("end", status="closed_unqualified", sockets_closed=True, reason="owner_close")
    finally:
        ledger.close()
    return path


def read_records(path):
    import json
    return [json.loads(line) for line in path.read_text().splitlines()]


def write_records(path, records, final_newline=True):
    import json
    path.write_text("\n".join(json.dumps(row) for row in records) + ("\n" if final_newline else ""))


def test_accepted_proxy_ledger_is_authority_for_prior_plus_all_tunnels(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path)
    assert validate_proxy_terminal(path, expected_prior_bytes=7, expected_pid=1234) == 12


def test_missing_proxy_ledger_cannot_be_assumed_zero(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(tmp_path / "missing.jsonl", expected_prior_bytes=0)


@pytest.mark.parametrize("kind", ["malformed", "missing_end", "partial_end", "wrong_status", "cleanup_unknown"])
def test_incomplete_or_failed_proxy_terminal_never_passes(tmp_path, kind):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path)
    rows = read_records(path)
    if kind == "malformed":
        path.write_text('{"event":')
    elif kind == "missing_end":
        write_records(path, rows[:-1])
    elif kind == "partial_end":
        write_records(path, rows, final_newline=False)
    elif kind == "wrong_status":
        rows[-1]["status"] = "failure"
        write_records(path, rows)
    else:
        rows[-1]["sockets_closed"] = False
        write_records(path, rows)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path, expected_prior_bytes=7, expected_pid=1234)


def test_prior_download_charge_cannot_be_reset_in_terminal_validation(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path, expected_prior_bytes=0, expected_pid=1234)


def test_terminal_listening_pid_is_bound_to_owned_proxy(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path, expected_prior_bytes=7, expected_pid=9999)


@pytest.mark.parametrize("kind", [
    "cumulative_rewind", "debit_not_integer", "final_count_differs", "tunnel_total_differs",
    "unclosed_tunnel", "unapproved_destination", "different_allowance", "duplicate_end",
])
def test_proxy_ledger_inconsistent_accounting_cannot_establish_remaining_budget(tmp_path, kind):
    from scripts.uc001_granite_acquisition_proxy.proxy import CEILING
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path)
    rows = read_records(path)
    debits = [row for row in rows if row["event"] == "debit"]
    if kind == "cumulative_rewind":
        debits[1]["cumulative_bytes"] = 8
    elif kind == "debit_not_integer":
        debits[1]["bytes_read"] = True
    elif kind == "final_count_differs":
        rows[-1]["cumulative_bytes"] += 1
    elif kind == "tunnel_total_differs":
        next(row for row in rows if row["event"] == "tunnel_end")["tunnel_bytes"] = 4
    elif kind == "unclosed_tunnel":
        rows.remove(next(row for row in rows if row["event"] == "tunnel_end"))
    elif kind == "unapproved_destination":
        debits[1]["destination"] = "unapproved.invalid:443"
    elif kind == "different_allowance":
        rows[0]["allowance_bytes"] = CEILING + 1
    else:
        rows.append(dict(rows[-1]))
    write_records(path, rows)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path, expected_prior_bytes=7, expected_pid=1234)


def test_exact_exhaustion_is_failure_even_with_a_forged_clean_terminal(tmp_path):
    from scripts.uc001_granite_acquisition_proxy.proxy import CEILING
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path = proxy_ledger(tmp_path, prior=CEILING - 5)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path, expected_prior_bytes=CEILING - 5, expected_pid=1234)


def test_duplicate_proxy_json_keys_are_unknown_accounting(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path=proxy_ledger(tmp_path)
    data=path.read_text().replace('"cumulative_bytes": 7','"cumulative_bytes": 7, "cumulative_bytes": 7',1)
    path.write_text(data)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path,expected_prior_bytes=7,expected_pid=1234)


def test_boolean_prior_is_not_an_integer_download_receipt(tmp_path):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    path=proxy_ledger(tmp_path,prior=0)
    rows=read_records(path);rows[0]['prior_bytes']=False;write_records(path,rows)
    with pytest.raises(ControllerFailure):
        validate_proxy_terminal(path,expected_prior_bytes=0,expected_pid=1234)
