import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from secrets import token_hex
from threading import Event
from time import monotonic
from uuid import uuid4

from fastapi.testclient import TestClient

from app.application.comparisons import digest
from app.interfaces.api import create_app
from tests.support.synthetic import EXAMPLE, candidates, create_service
from tests.support.uncertain_save import install_uncertain_save_fault


def test_uncertain_save_control_isolated_from_seeding_other_saves_and_recovery(tmp_path):
    database = tmp_path / "support.sqlite3"
    control_file = tmp_path / "uncertain.json"
    evidence_file = control_file.with_suffix(".evidence.json")
    service = create_service(database)
    dialect = service.store.engine.dialect
    original_methods = (dialect.do_commit, dialect.do_execute)
    install_uncertain_save_fault(service.store, database, control_file)

    def payload():
        return {"submission_key": str(uuid4()), "text": EXAMPLE,
            "search_location": {"country_code": "CH"}, "location_choice": "provided", "language_context": {}}

    def observe():
        with sqlite3.connect(database) as connection:
            rows = connection.execute("SELECT id, projection FROM search_request ORDER BY rowid").fetchall()
            return {
                "rows": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
                "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    for table in ("search_request", "request_alternative", "request_alternative_evidence")},
                "snapshots": {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                    for table in ("request_alternative", "request_alternative_evidence", "evidence")},
            }

    try:
        service.store.seed_test_knowledge(candidates())
        with TestClient(create_app(service)) as client:
            missing = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert missing.status_code == 201
            assert not evidence_file.exists()

            control_file.write_text(json.dumps({"submission_key_digest": digest(str(uuid4()))}))
            service.store.seed_test_knowledge(candidates())
            unmatched = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert unmatched.status_code == 201
            assert control_file.exists() and not evidence_file.exists()
            assert (dialect.do_commit, dialect.do_execute) == original_methods
            before_fault = observe()

            submission = payload()
            proof = token_hex(32)
            control_file.write_text(json.dumps({"submission_key_digest": digest(submission["submission_key"])}))
            unknown = client.post("/api/comparisons", json=submission, headers={"X-Submission-Proof": proof})
            assert unknown.status_code == 503
            assert unknown.json() == {"outcome": "persistence_error", "persistence": {"state": "unknown"},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
            assert not control_file.exists()
            assert (dialect.do_commit, dialect.do_execute) == original_methods
            evidence = json.loads(evidence_file.read_text())
            assert evidence["fault_counts"] == {"real_commits": 1, "confirmation_losses": 1, "read_failures": 1}
            assert evidence["dialect_methods_restored"] is True
            assert evidence["observer_rows_supplied_to_application"] is False
            assert evidence["independent_after_commit"] == evidence["after_fault"]
            after_fault = observe()
            assert evidence["after_fault"] == json.loads(json.dumps(after_fault))
            assert after_fault["counts"] == {"search_request": 3, "request_alternative": 6, "request_alternative_evidence": 6}
            assert after_fault["rows"][:2] == before_fault["rows"]
            original = after_fault["rows"][-1]["projection"]

            recovered = client.post("/api/comparisons", json=submission, headers={"X-Submission-Proof": proof})
            assert recovered.status_code == 200
            assert recovered.json() == {"outcome": "submission_recovered", "persistence": original["persistence"],
                "saved_outcome": "comparison", "assessed_at": original["assessed_at"]}
            assert observe() == after_fault
            assert json.loads(evidence_file.read_text()) == evidence

            subsequent = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert subsequent.status_code == 201
            assert observe()["counts"] == {"search_request": 4, "request_alternative": 8, "request_alternative_evidence": 8}
            assert (dialect.do_commit, dialect.do_execute) == original_methods
            assert json.loads(evidence_file.read_text()) == evidence
    finally:
        service.store.engine.dispose()


def test_delayed_save_gate_targets_one_submission_and_restores_normal_saves(tmp_path):
    from tests.support.delayed_save import install_delayed_save_gate

    database = tmp_path / "delayed.sqlite3"
    control_file = tmp_path / "delayed.json"
    reached_file = control_file.with_suffix(".reached.json")
    release_file = control_file.with_suffix(".release.json")
    evidence_file = control_file.with_suffix(".evidence.json")
    service = create_service(database)
    dialect = service.store.engine.dialect
    original_save, original_commit = service.store.save, dialect.do_commit
    cleanup = install_delayed_save_gate(service.store, database, control_file, timeout=20)
    executor = ThreadPoolExecutor(max_workers=1)
    future = None
    submission = None

    def payload():
        return {"submission_key": str(uuid4()), "text": EXAMPLE,
            "search_location": {"country_code": "CH"}, "location_choice": "country_only", "language_context": {}}

    def observe():
        with sqlite3.connect(database) as connection:
            rows = connection.execute("SELECT id, projection FROM search_request ORDER BY rowid").fetchall()
            observed = {
                "rows": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
                "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    for table in ("search_request", "request_alternative", "request_alternative_evidence")},
                "snapshots": {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                    for table in ("request_alternative", "request_alternative_evidence", "evidence")},
            }
            return json.loads(json.dumps(observed))

    def release():
        if submission is not None:
            release_file.write_text(json.dumps({"submission_key_digest": digest(submission["submission_key"])}))

    try:
        service.store.seed_test_knowledge(candidates())
        with TestClient(create_app(service)) as client:
            missing = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert missing.status_code == 201
            assert not reached_file.exists() and not evidence_file.exists()
            assert dialect.do_commit == original_commit

            control_file.write_text(json.dumps({"submission_key_digest": digest(str(uuid4()))}))
            service.store.seed_test_knowledge(candidates())
            unmatched = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert unmatched.status_code == 201
            assert control_file.exists() and not reached_file.exists() and not evidence_file.exists()
            assert dialect.do_commit == original_commit
            before = observe()
            assert before["counts"] == {"search_request": 2, "request_alternative": 4, "request_alternative_evidence": 4}

            submission = payload()
            proof = token_hex(32)
            control_file.write_text(json.dumps({"submission_key_digest": digest(submission["submission_key"])}))
            future = executor.submit(client.post, "/api/comparisons", json=submission, headers={"X-Submission-Proof": proof})
            try:
                deadline = monotonic() + 10
                while not reached_file.exists():
                    if future.done():
                        raise AssertionError("The targeted save returned before signalling the pre-commit gate")
                    if monotonic() >= deadline:
                        raise AssertionError("The targeted save did not signal the pre-commit gate")
                    Event().wait(0.01)
                reached = json.loads(reached_file.read_text())
                assert reached["stage"] == "after_required_inserts_before_underlying_commit"
                assert reached["transaction_active"] is True
                assert reached["transaction_rows"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
                assert reached["save_calls"] == 1 and reached["underlying_commit_calls"] == 0
                assert reached["independent_before"] == before
                assert reached["independent_while_paused"] == before
                assert not control_file.exists() and not future.done()
                assert observe() == before
                assert reached["request_id"] not in {row["id"] for row in before["rows"]}

                release()
                response = future.result(timeout=25)
                assert response.status_code == 201
                saved = response.json()
                assert saved["outcome"] == "comparison"
                assert saved["persistence"] == {"state": "saved", "request_id": reached["request_id"]}
                after = observe()
                assert after["counts"] == {"search_request": 3, "request_alternative": 6, "request_alternative_evidence": 6}
                assert [row for row in after["rows"] if row["id"] not in {previous["id"] for previous in before["rows"]}] == [
                    {"id": reached["request_id"], "projection": saved}]
                assert all(row in after["rows"] for row in before["rows"])
                for table in ("request_alternative", "request_alternative_evidence"):
                    assert all(row in after["snapshots"][table] for row in before["snapshots"][table])
                assert after["snapshots"]["evidence"] == before["snapshots"]["evidence"]
                evidence = json.loads(evidence_file.read_text())
                assert evidence["underlying_commit_calls"] == 1 and evidence["save_calls"] == 1
                assert evidence["release_received"] is True
                assert evidence["independent_before"] == before and evidence["independent_while_paused"] == before
                assert evidence["independent_after"] == after
                assert evidence["dialect_method_restored"] is True and evidence["store_save_hook_restored"] is True
                assert evidence["observer_rows_supplied_to_application"] is False
                assert dialect.do_commit == original_commit and service.store.save == original_save
            finally:
                release()
                cleanup()
                future.result(timeout=25)

            subsequent = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert subsequent.status_code == 201
            assert observe()["counts"] == {"search_request": 4, "request_alternative": 8, "request_alternative_evidence": 8}
            assert json.loads(evidence_file.read_text()) == evidence
            assert dialect.do_commit == original_commit and service.store.save == original_save
    finally:
        release()
        cleanup()
        executor.shutdown(wait=False, cancel_futures=True)
        service.store.engine.dispose()


def test_retrieval_failure_control_isolated_and_same_submission_retry_saves_once(tmp_path):
    from tests.support.source_bound_rendering import create_demo_service
    from tests.support.uncertain_save import _observe

    database = tmp_path / "processing.sqlite3"
    control_file = tmp_path / "processing.json"
    evidence_file = control_file.with_suffix(".evidence.json")
    service = create_demo_service(database, processing_error_file=control_file)
    original_store = service.store

    def payload():
        return {"submission_key": str(uuid4()), "text": EXAMPLE,
            "search_location": {"country_code": "CH"}, "location_choice": "provided",
            "language_context": {"browser_language": "en"}}

    def observe():
        return json.loads(json.dumps(_observe(database)))

    try:
        with TestClient(create_app(service)) as client:
            missing = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert missing.status_code == 201
            assert not control_file.exists() and not evidence_file.exists()

            control_file.write_text(json.dumps({"submission_key_digest": digest(str(uuid4()))}))
            service.store.seed_test_knowledge(candidates())
            unmatched = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert unmatched.status_code == 201
            assert control_file.exists() and not evidence_file.exists()
            before = observe()
            assert before["counts"] == {"search_request": 2, "request_alternative": 4, "request_alternative_evidence": 4}
            prior_request_ids = {row["id"] for row in before["rows"]}
            with sqlite3.connect(database) as connection:
                protected_prior_requests = connection.execute("SELECT * FROM search_request ORDER BY id").fetchall()

            submission = payload()
            serialized = json.dumps(submission, separators=(",", ":"))
            proof = token_hex(32)
            headers = {"Content-Type": "application/json", "X-Submission-Proof": proof}
            control_file.write_text(json.dumps({"submission_key_digest": digest(submission["submission_key"])}))
            error = client.post("/api/comparisons", content=serialized, headers=headers)
            assert error.status_code == 500
            expected_error = {"outcome": "processing_error", "persistence": {"state": "not_attempted"},
                "issues": [{"code": "comparison_processing_failed"}]}
            processing_error_only = error.json() == expected_error
            assert processing_error_only
            assert not control_file.exists()
            assert observe() == before
            first_evidence = json.loads(evidence_file.read_text())
            assert len(first_evidence["attempts"]) == 1
            failed_attempt = first_evidence["attempts"][0]
            assert failed_attempt["counts"] == {"interpret": 1, "retrieve": 1, "assess_clock": 0,
                "prepare": 0, "prepare_coverage": 0, "save": 0}
            assert failed_attempt["fault_raised"] is True and failed_attempt["returned_outcome"] is None
            assert first_evidence["total_counts"] == failed_attempt["counts"]
            assert first_evidence["fault_consumed"] is True
            assert first_evidence["original_adapters_unchanged"] is True
            assert first_evidence["raw_originating_proofs_or_requests_recorded"] is False

            retried = client.post("/api/comparisons", content=serialized, headers=headers)
            assert retried.status_code == 201
            saved = retried.json()
            assert saved["outcome"] == "comparison"
            assert saved["assessed_at"] == "2026-10-15T10:00:00+00:00"
            after = observe()
            assert after["counts"] == {"search_request": 3, "request_alternative": 6, "request_alternative_evidence": 6}
            added = [row for row in after["rows"] if row["id"] not in prior_request_ids]
            assert added == [{"id": saved["persistence"]["request_id"], "projection": saved}]
            assert [row for row in after["rows"] if row["id"] in prior_request_ids] == before["rows"]
            for table in ("request_alternative", "request_alternative_evidence"):
                assert all(row in after["snapshots"][table] for row in before["snapshots"][table])
            assert after["snapshots"]["evidence"] == before["snapshots"]["evidence"]
            with sqlite3.connect(database) as connection:
                prior_requests_after = connection.execute("SELECT * FROM search_request WHERE id IN (?, ?) ORDER BY id",
                    tuple(sorted(prior_request_ids))).fetchall()
                unchanged_prior_request_rows = prior_requests_after == protected_prior_requests
                saved_text, saved_context = connection.execute("SELECT original_text, language_context FROM search_request WHERE id = ?",
                    (saved["persistence"]["request_id"],)).fetchone()
            assert unchanged_prior_request_rows
            assert saved_text == EXAMPLE and json.loads(saved_context) == submission["language_context"]
            evidence = json.loads(evidence_file.read_text())
            assert len(evidence["attempts"]) == 2 and evidence["attempts"][0] == failed_attempt
            successful_attempt = evidence["attempts"][1]
            assert successful_attempt["counts"] == {"interpret": 1, "retrieve": 1, "assess_clock": 1,
                "prepare": 1, "prepare_coverage": 0, "save": 1}
            assert successful_attempt["fault_raised"] is False and successful_attempt["returned_outcome"] == "comparison"
            assert evidence["total_counts"] == {"interpret": 2, "retrieve": 2, "assess_clock": 1,
                "prepare": 1, "prepare_coverage": 0, "save": 1}
            assert evidence["fault_consumed"] is True and evidence["original_adapters_unchanged"] is True
            assert evidence["raw_originating_proofs_or_requests_recorded"] is False
            assert not control_file.exists() and service.store is original_store
    finally:
        service.cleanup()
        control_file.unlink(missing_ok=True)
        service.store.engine.dispose()
    assert not control_file.exists()


def test_absent_unknown_save_recovery_reassesses_expired_evidence_without_replacing_submission(tmp_path):
    from datetime import timedelta

    from tests.support.source_bound_rendering import create_demo_service
    from tests.support.synthetic import FIXTURE_TIME
    from tests.support.uncertain_save import _observe

    database = tmp_path / "absent-recovery.sqlite3"
    control_file = tmp_path / "absent.json"
    fault_file = control_file.with_suffix(".evidence.json")
    processing_file = control_file.with_suffix(".processing.json")
    current_time = FIXTURE_TIME
    service = create_demo_service(database, clock=lambda: current_time, uncertain_save_file=control_file)
    dialect = service.store.engine.dialect
    original_save = service.store.save
    original_methods = (dialect.do_commit, dialect.do_execute, dialect.do_rollback)
    cleanup_fault = install_uncertain_save_fault(service.store, database, control_file)

    def payload():
        return {"submission_key": str(uuid4()), "text": EXAMPLE,
            "search_location": {"country_code": "CH"}, "location_choice": "provided",
            "language_context": {"browser_language": "en"}}

    def observe():
        return json.loads(json.dumps(_observe(database)))

    try:
        with TestClient(create_app(service)) as client:
            missing = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert missing.status_code == 201
            assert not fault_file.exists() and not processing_file.exists()
            control_file.write_text(json.dumps({"submission_key_digest": digest(str(uuid4())), "mode": "absent"}))
            service.store.seed_test_knowledge(candidates())
            unmatched = client.post("/api/comparisons", json=payload(), headers={"X-Submission-Proof": token_hex(32)})
            assert unmatched.status_code == 201
            assert control_file.exists() and not fault_file.exists() and not processing_file.exists()
            before = observe()
            assert before["counts"] == {"search_request": 2, "request_alternative": 4, "request_alternative_evidence": 4}
            prior_ids = {row["id"] for row in before["rows"]}
            with sqlite3.connect(database) as connection:
                protected_prior_requests = connection.execute("SELECT * FROM search_request ORDER BY id").fetchall()

            submission = payload()
            serialized = json.dumps(submission, separators=(",", ":"))
            proof = token_hex(32)
            headers = {"Content-Type": "application/json", "X-Submission-Proof": proof}
            control_file.write_text(json.dumps({"submission_key_digest": digest(submission["submission_key"]), "mode": "absent"}))
            unknown = client.post("/api/comparisons", content=serialized, headers=headers)
            assert unknown.status_code == 503
            expected_unknown = {"outcome": "persistence_error", "persistence": {"state": "unknown"},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
            uncertainty_only = unknown.json() == expected_unknown
            assert uncertainty_only
            assert not control_file.exists()
            assert observe() == before
            assert (dialect.do_commit, dialect.do_execute, dialect.do_rollback) == original_methods
            fault = json.loads(fault_file.read_text())
            assert fault["mode"] == "absent"
            assert fault["fault_counts"] == {"real_commits": 0, "confirmation_losses": 1, "read_failures": 0}
            assert fault["real_reconciliation_selects"] == 1 and fault["reconciliation_results"] == [False]
            assert fault["normal_driver_rollback_observed"] is True
            assert fault["independent_after_commit"] is None and fault["after_fault"] == before
            assert fault["dialect_methods_restored"] is True and fault["observer_rows_supplied_to_application"] is False
            first_processing = json.loads(processing_file.read_text())
            assert len(first_processing["attempts"]) == 1
            first = first_processing["attempts"][0]
            assert first["counts"] == {"interpret": 1, "retrieve": 1, "assess_clock": 1,
                "prepare": 1, "prepare_coverage": 0, "save": 1, "underlying_commits": 0}
            assert first["insert_attempts"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            assert first["real_request_selects"] == 2
            assert first["retrieved_count"] == first["qualified_rendered_count"] == 2
            assert first["coverage_limitation_codes"] == []
            assert first["returned_outcome"] is None and first["raised_persistence_state"] == "unknown"
            assert first["lookup_results"] == [{"scope": "application_initial", "found": False, "real_selects": 1}]
            discarded = first["prepared"]
            assert discarded["outcome"] == "comparison" and discarded["assessed_at"] == FIXTURE_TIME.isoformat()
            assert len(set(discarded["option_ids"])) == 2 and discarded["request_id"] not in prior_ids
            assert first_processing["total_counts"] == first["counts"]
            assert first_processing["original_adapters_unchanged"] is True
            assert first_processing["raw_originating_proofs_or_requests_recorded"] is False

            current_time = FIXTURE_TIME + timedelta(days=366)
            recovered = client.post("/api/comparisons", content=serialized, headers=headers)
            assert recovered.status_code == 201
            saved = recovered.json()
            assert saved["outcome"] == "insufficient_coverage" and saved["persistence"]["state"] == "saved"
            assert saved["assessed_at"] == current_time.isoformat()
            assert "essential_evidence_expired" in saved["coverage"]["limitation_codes"]
            assert "comparison" not in saved
            assert saved["persistence"]["request_id"] != discarded["request_id"]
            after = observe()
            assert after["counts"] == {"search_request": 3, "request_alternative": 4, "request_alternative_evidence": 4}
            assert [row for row in after["rows"] if row["id"] not in prior_ids] == [
                {"id": saved["persistence"]["request_id"], "projection": saved}]
            assert [row for row in after["rows"] if row["id"] in prior_ids] == before["rows"]
            assert after["snapshots"] == before["snapshots"]
            with sqlite3.connect(database) as connection:
                prior_rows_after = connection.execute("SELECT * FROM search_request WHERE id IN (?, ?) ORDER BY id",
                    tuple(sorted(prior_ids))).fetchall()
                full_prior_requests_unchanged = prior_rows_after == protected_prior_requests
                saved_digest = connection.execute("SELECT submission_key_digest FROM search_request WHERE id = ?",
                    (saved["persistence"]["request_id"],)).fetchone()[0]
                same_submission_key_saved = saved_digest == digest(submission["submission_key"])
                discarded_identities_absent = (
                    connection.execute("SELECT count(*) FROM search_request WHERE id = ?", (discarded["request_id"],)).fetchone()[0] == 0
                    and connection.execute("SELECT count(*) FROM request_alternative WHERE request_id = ? OR id IN (?, ?)",
                        (discarded["request_id"], *discarded["option_ids"])).fetchone()[0] == 0
                    and connection.execute("SELECT count(*) FROM request_alternative_evidence WHERE option_id IN (?, ?)",
                        discarded["option_ids"]).fetchone()[0] == 0)
            assert full_prior_requests_unchanged and same_submission_key_saved and discarded_identities_absent
            assert json.loads(fault_file.read_text()) == fault
            processing = json.loads(processing_file.read_text())
            assert len(processing["attempts"]) == 2 and processing["attempts"][0] == first
            second = processing["attempts"][1]
            assert second["counts"] == {"interpret": 1, "retrieve": 1, "assess_clock": 1,
                "prepare": 0, "prepare_coverage": 1, "save": 1, "underlying_commits": 1}
            assert second["insert_attempts"] == {"search_request": 1, "request_alternative": 0, "request_alternative_evidence": 0}
            assert second["real_request_selects"] == 2
            assert second["retrieved_count"] == 2 and second["qualified_rendered_count"] == 0
            assert "essential_evidence_expired" in second["coverage_limitation_codes"]
            assert second["prepared"] == {"request_id": saved["persistence"]["request_id"], "option_ids": [],
                "outcome": "insufficient_coverage", "assessed_at": current_time.isoformat()}
            assert second["returned_outcome"] == "insufficient_coverage" and second["raised_persistence_state"] is None
            assert second["lookup_results"] == [{"scope": "application_initial", "found": False, "real_selects": 1}]
            assert processing["total_counts"] == {"interpret": 2, "retrieve": 2, "assess_clock": 2,
                "prepare": 1, "prepare_coverage": 1, "save": 2, "underlying_commits": 1}
            assert processing["original_adapters_unchanged"] is True
            assert processing["raw_originating_proofs_or_requests_recorded"] is False
            assert not control_file.exists()
            assert (dialect.do_commit, dialect.do_execute, dialect.do_rollback) == original_methods
    finally:
        current_time = FIXTURE_TIME
        cleanup_fault()
        service.cleanup()
        control_file.unlink(missing_ok=True)
        service.store.engine.dispose()
    assert service.store.save == original_save
    assert (dialect.do_commit, dialect.do_execute, dialect.do_rollback) == original_methods
    assert not control_file.exists()
