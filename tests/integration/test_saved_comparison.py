import json
import sqlite3
from dataclasses import asdict, replace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.interfaces.api import create_app
from tests.support.synthetic import EXAMPLE, create_test_app


def test_valid_empty_knowledge_is_atomically_saved_coverage_and_recoverable(system):
    client, path, service = system

    class EmptyKnowledge:
        def retrieve(self, interpretation, submission):
            return ()

    with TestClient(create_app(replace(service, knowledge=EmptyKnowledge()))) as coverage_client:
        payload = submission()
        headers = {"X-Submission-Proof": "a" * 64}
        response = coverage_client.post("/api/comparisons", json=payload, headers=headers)
        assert response.status_code == 201
        body = response.json()
        assert body["outcome"] == "insufficient_coverage"
        assert body["persistence"]["state"] == "saved"
        assert "comparison" not in body
        assert body["issues"] == [{"code": "no_qualifying_knowledge"}, {"code": "research_unavailable"}]
        assert counts(path) == {"search_request": 1, "request_alternative": 0, "request_alternative_evidence": 0}
        with sqlite3.connect(path) as connection:
            assert json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0]) == body
        recovered = coverage_client.post("/api/comparisons", json=payload, headers=headers).json()
        assert recovered["outcome"] == "submission_recovered"
        assert recovered["saved_outcome"] == "insufficient_coverage"


@pytest.mark.parametrize("mode", ["retrieval_failure", "coverage_save_failure", "expired"])
def test_coverage_is_distinct_from_processing_and_save_failure(system, mode):
    from datetime import timedelta
    client, path, service = system

    class Knowledge:
        def retrieve(self, interpretation, submission):
            if mode == "retrieval_failure":
                raise RuntimeError("synthetic retrieval failure")
            return ()

    if mode == "coverage_save_failure":
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TRIGGER fail_coverage BEFORE INSERT ON search_request BEGIN SELECT RAISE(ABORT, 'synthetic'); END")
    if mode == "expired":
        service = replace(service, clock=lambda: service_time + timedelta(days=366))
        from tests.support.synthetic import FIXTURE_TIME as service_time
    else:
        service = replace(service, knowledge=Knowledge())
    with TestClient(create_app(service)) as other:
        response = other.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64})
    body = response.json()
    assert body["outcome"] == {"retrieval_failure": "processing_error", "coverage_save_failure": "persistence_error", "expired": "insufficient_coverage"}[mode]
    if mode == "coverage_save_failure":
        assert body["assessed_outcome"] == "insufficient_coverage"
        assert body["persistence"]["state"] == "failed"
    if mode == "expired":
        assert "essential_evidence_expired" in body["coverage"]["limitation_codes"]
    assert counts(path)["search_request"] == (1 if mode == "expired" else 0)


def test_qualification_precedes_deterministic_limit_and_saved_projection(system):
    from tests.support.synthetic import candidates
    client, path, service = system
    original = candidates()[0]
    pool = []
    for index, name in enumerate(("Zulu", "Ａlpha", "alpha", "Beta", "A failed match"), 10):
        identity = f"00000000-0000-4000-8000-{index:012d}"
        source = replace(original.evidence[0], alternative_id=identity, version_id=f"10000000-0000-4000-8000-{index:012d}")
        pool.append(replace(original, alternative_id=identity, display_name=name, evidence=(source,),
            claims=original.claims if index != 14 else ()))
    service.store.seed_test_knowledge(tuple(pool))

    class Knowledge:
        def retrieve(self, interpretation, submission):
            return tuple(pool)

    with TestClient(create_app(replace(service, knowledge=Knowledge()))) as other:
        body = other.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64}).json()
    assert body["comparison"]["omitted_count"] == 1
    assert [o["display_name"] for o in body["comparison"]["options"]] == ["Ａlpha", "alpha", "Beta"]
    assert counts(path)["request_alternative"] == 3
    with sqlite3.connect(path) as connection:
        assert json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0]) == body


@pytest.mark.parametrize("outcome,status", [("invalid_input", 422), ("clarification_required", 200), ("interpretation_unavailable", 200)])
def test_input_outcomes_never_reach_qualification_or_save(system, outcome, status):
    from app.application.comparisons import InputOutcome
    _, path, service = system

    class Interpreter:
        def interpret(self, submission):
            raise InputOutcome(outcome, "synthetic_input_outcome")

    class NeverRetrieve:
        def retrieve(self, *args):
            raise AssertionError("Input outcome must bypass retrieval")

    with TestClient(create_app(replace(service, interpreter=Interpreter(), knowledge=NeverRetrieve()))) as other:
        response = other.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == status
    assert response.json()["outcome"] == outcome
    assert response.json()["persistence"]["state"] == "not_attempted"
    assert counts(path)["search_request"] == 0


def test_explicit_retry_reassesses_without_renewing_review_dates(system):
    from datetime import timedelta
    from tests.support.synthetic import FIXTURE_TIME
    _, path, service = system
    payload = submission()
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TRIGGER retry_failure BEFORE INSERT ON search_request BEGIN SELECT RAISE(ABORT, 'synthetic'); END")
    with TestClient(create_app(service)) as other:
        assert other.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64}).status_code == 503
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER retry_failure")
        before = connection.execute("SELECT snapshot FROM evidence ORDER BY version_id").fetchall()
    with TestClient(create_app(replace(service, clock=lambda: FIXTURE_TIME + timedelta(days=2)))) as other:
        body = other.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64}).json()
    assert body["outcome"] == "insufficient_coverage"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT snapshot FROM evidence ORDER BY version_id").fetchall() == before


def test_blank_input_is_not_a_search_record(system):
    client, path, _ = system
    payload = submission()
    payload["text"] = "  "
    assert client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64}).status_code == 422
    assert counts(path)["search_request"] == 0


def test_unavailable_locality_reference_requires_explicit_choice_without_search_writes(system):
    _, path, service = system
    payload = submission()
    payload["search_location"].update(town="Synthetic town", postcode="0001")

    class NeverRetrieve:
        def retrieve(self, *args):
            raise AssertionError("Unresolved locality must not reach assessment")

    with sqlite3.connect(path) as connection:
        evidence_before = connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall()
    with TestClient(create_app(replace(service, knowledge=NeverRetrieve()))) as client:
        for _ in range(2):
            response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
            assert response.status_code == 200
            body = response.json()
            assert body["outcome"] == "clarification_required"
            assert body["persistence"] == {"state": "not_attempted"}
            assert body["issues"] == [{"code": "locality_reference_unavailable"}]
            assert "cannot currently be verified" in body["clarification"]["message"]
            assert "country-only" in body["clarification"]["message"]
            assert "comparison" not in body and "coverage" not in body
            assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall() == evidence_before


def test_country_only_normalizes_effective_location_but_binds_and_recovers_original_payload(system):
    from app.application.comparisons import digest
    from tests.support.synthetic import candidates
    _, path, service = system
    payload = submission()
    payload["location_choice"] = "country_only"
    discarded = {"town": "Discarded synthetic town", "postcode": "0001",
        "reference": {"source": "synthetic-reference", "id": "discarded-id", "release": "unused-release"}}
    payload["search_location"].update(discarded)
    captured_digest = digest({key: value for key, value in payload.items() if key != "submission_key"})

    class Knowledge:
        def retrieve(self, interpretation, effective):
            assert effective.search_location == {"country_code": "CH"}
            assert effective.text == payload["text"]
            return candidates()

    with TestClient(create_app(replace(service, knowledge=Knowledge()))) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "comparison"
    request_id = body["persistence"]["request_id"]
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT original_text, search_location, location_choice, payload_digest, interpretation, projection FROM search_request WHERE id = ?", (request_id,)).fetchone()
        assert row[0] == payload["text"]
        assert json.loads(row[1]) == {"country_code": "CH"}
        assert row[2:4] == ("country_only", captured_digest)
        assert json.loads(row[5]) == body
        snapshots = connection.execute("SELECT snapshot FROM request_alternative WHERE request_id = ? ORDER BY id", (request_id,)).fetchall()
        for discarded_value in ("Discarded synthetic town", "discarded-id", "unused-release"):
            assert discarded_value not in row[1] + row[4] + row[5]
        saved_rows = connection.execute("SELECT * FROM search_request").fetchall()

    class NeverInterpret:
        def interpret(self, *args):
            raise AssertionError("Committed recovery must precede interpretation and locality policy")

    with TestClient(create_app(replace(service, interpreter=NeverInterpret()))) as client:
        recovered = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
        assert recovered.status_code == 200
        assert recovered.json() == {"outcome": "submission_recovered", "persistence": body["persistence"],
            "saved_outcome": body["outcome"], "assessed_at": body["assessed_at"]}
        payload["search_location"]["town"] = "Changed discarded town"
        assert client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64}).status_code == 409
        assert client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64}).status_code == 403
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM search_request").fetchall() == saved_rows
        assert connection.execute("SELECT snapshot FROM request_alternative WHERE request_id = ? ORDER BY id", (request_id,)).fetchall() == snapshots
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}


def test_country_only_fallback_preserves_independent_textual_locality_requirement(system):
    from tests.support.synthetic import represented_locality
    _, path, service = system
    represented = represented_locality()
    payload = submission()
    payload["text"] = represented.original_text
    payload["search_location"].update(town="Genève", postcode="1200")

    class Interpreter:
        def interpret(self, original):
            assert original == represented.original_text
            return represented

    with TestClient(create_app(replace(service, interpreter=Interpreter()))) as client:
        clarification = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
        assert clarification.json()["outcome"] == "clarification_required"
        assert counts(path)["search_request"] == 0
        payload["submission_key"] = str(uuid4())
        payload["location_choice"] = "country_only"
        continued = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64})
    assert continued.status_code == 201
    body = continued.json()
    assert body["outcome"] == "insufficient_coverage"
    assert "comparison" not in body
    assert "essential_support_unverified" in body["coverage"]["limitation_codes"]
    with sqlite3.connect(path) as connection:
        original, interpretation, location = connection.execute(
            "SELECT original_text, interpretation, search_location FROM search_request WHERE id = ?",
            (body["persistence"]["request_id"],)).fetchone()
    assert original == represented.original_text == "repair bicycle in Genève"
    assert json.loads(location) == {"country_code": "CH"}
    saved = json.loads(interpretation)
    assert saved["constraints"] == [{"value": "locality:Genève", "quote": "in Genève"}]
    assert saved["provenance"]["items"] == [asdict(item) for item in represented.items]
    assert counts(path) == {"search_request": 1, "request_alternative": 0, "request_alternative_evidence": 0}


def test_locality_unavailability_does_not_conceal_interpretation_processing_errors(system):
    _, path, service = system
    payload = submission()
    payload["search_location"]["town"] = "Synthetic town"

    class BrokenInterpreter:
        def interpret(self, original):
            raise RuntimeError("Synthetic interpretation processing fault")

    with TestClient(create_app(replace(service, interpreter=BrokenInterpreter()))) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 500
    assert response.json()["outcome"] == "processing_error"
    assert counts(path)["search_request"] == 0


def test_reopening_test_store_preserves_evidence_and_saved_comparison(system):
    from tests.support.synthetic import create_service
    client, path, _ = system
    saved = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64}).json()
    reopened = create_service(path)
    try:
        with sqlite3.connect(path) as connection:
            assert json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0]) == saved
    finally:
        reopened.store.engine.dispose()


def submission():
    return {
        "submission_key": str(uuid4()),
        "text": EXAMPLE,
        "search_location": {"country_code": "CH"},
        "location_choice": "provided",
        "language_context": {},
    }


def counts(path):
    with sqlite3.connect(path) as connection:
        return {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("search_request", "request_alternative", "request_alternative_evidence")
        }


@pytest.fixture
def system(tmp_path):
    path = tmp_path / "comparison.sqlite3"
    app = create_test_app(path)
    with TestClient(app) as client:
        yield client, path, app.state.comparisons
    app.state.comparisons.store.engine.dispose()


def test_returns_only_the_committed_projection_with_saved_ids_and_evidence(system):
    client, path, service = system
    payload = submission()
    response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201
    body = response.json()
    request_id = body["persistence"]["request_id"]
    UUID(request_id)
    assert body["persistence"]["state"] == "saved"
    assert body["outcome"] == "comparison"
    options = body["comparison"]["options"]
    assert [option["display_name"] for option in options] == ["Alpha repair (synthetic)", "Zeta repair (synthetic)"]
    assert [option["position"] for option in options] == [1, 2]
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
    with sqlite3.connect(path) as connection:
        original, interpretation, location, projection = connection.execute(
            "SELECT original_text, interpretation, search_location, projection FROM search_request WHERE id = ?",
            (request_id,),
        ).fetchone()
        assert original == EXAMPLE
        assert json.loads(interpretation)["constraints"] == [{"value": "no_replacement", "quote": "without replacing it"}]
        assert json.loads(location)["country_code"] == "CH"
        assert json.loads(projection) == body
        saved = connection.execute(
            "SELECT id, alternative_id, position, snapshot FROM request_alternative WHERE request_id = ? ORDER BY position",
            (request_id,),
        ).fetchall()
        for option, (option_id, alternative_id, position, snapshot) in zip(options, saved, strict=True):
            UUID(option_id)
            assert (option_id, alternative_id, position) == (option["option_id"], option["alternative_id"], option["position"])
            assert json.loads(snapshot) == option
            assert option["financial"]["amount"] == "45.00"
            assert option["environmental"]["status"] == "unknown"
        connection.execute("UPDATE alternative SET display_name = 'Changed live catalogue'")
        connection.commit()
        assert json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0]) == body
    with service.store.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_required_evidence_write_failure_rolls_back_the_entire_comparison(system):
    client, path, _ = system
    with sqlite3.connect(path) as connection:
        connection.execute("""CREATE TRIGGER reject_second_link BEFORE INSERT ON request_alternative_evidence
            WHEN (SELECT count(*) FROM request_alternative_evidence) = 1
            BEGIN SELECT RAISE(ABORT, 'synthetic required-write failure'); END""")
    response = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 503
    assert response.json()["outcome"] == "persistence_error"
    assert response.json()["persistence"] == {"state": "failed"}
    assert "comparison" not in response.json()
    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM evidence").fetchone()[0] == 2


def test_required_second_option_write_failure_rolls_back_new_submission_and_preserves_baseline(system):
    from secrets import token_hex

    from sqlalchemy import event

    from app.application.comparisons import digest

    client, path, service = system
    baseline_response = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": token_hex(32)})
    assert baseline_response.status_code == 201
    baseline_projection = baseline_response.json()
    assert baseline_projection["outcome"] == "comparison"
    assert baseline_projection["assessed_at"] == "2026-10-15T10:00:00+00:00"

    def observe():
        with sqlite3.connect(path) as connection:
            requests = connection.execute("SELECT id, projection FROM search_request ORDER BY id").fetchall()
            return {
                "counts": counts(path),
                "requests": [{"id": identity, "projection": json.loads(projection)} for identity, projection in requests],
                "options": connection.execute("SELECT * FROM request_alternative ORDER BY 1, 2").fetchall(),
                "links": connection.execute("SELECT * FROM request_alternative_evidence ORDER BY 1, 2").fetchall(),
                "evidence": connection.execute("SELECT * FROM evidence ORDER BY 1, 2").fetchall(),
            }

    def full_request_rows():
        with sqlite3.connect(path) as connection:
            return connection.execute("SELECT * FROM search_request ORDER BY id").fetchall()

    before = observe()
    protected_baseline_requests = full_request_rows()
    assert before["counts"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
    assert before["requests"] == [{"id": baseline_projection["persistence"]["request_id"], "projection": baseline_projection}]
    payload = submission()
    target_key_digest = digest(payload["submission_key"])
    store, engine = service.store, service.store.engine
    real_save = store.save
    calls = {"target_http_posts": 0, "save": 0, "writer_commits": 0, "writer_rollbacks": 0}
    attempted = dict.fromkeys(("search_request", "request_alternative", "request_alternative_evidence"), 0)
    succeeded = attempted.copy()
    planned, timeline, rejection = [], [], []
    writer = None
    writer_observation = None
    independent_during = None

    def save(prepared):
        calls["save"] += 1
        planned.append({"request_id": prepared.projection["persistence"]["request_id"],
            "option_ids": [option["option_id"] for option in prepared.projection["comparison"]["options"]]})
        timeline.append("real_save_entered")
        return real_save(prepared)

    def insert_table(context):
        statement = getattr(getattr(context, "compiled", None), "statement", None)
        return statement.table.name if getattr(statement, "is_insert", False) else None

    def before_insert(connection, _cursor, _statement, _parameters, context, _executemany):
        nonlocal writer, writer_observation, independent_during
        table = insert_table(context)
        if table == "search_request" and writer is None:
            writer = connection
        if connection is not writer or table not in attempted:
            return
        attempted[table] += 1
        timeline.append(f"{table}:insert_attempted")
        if table == "request_alternative" and attempted[table] == 2:
            request_id = planned[0]["request_id"]
            cursor = connection.connection.cursor()
            try:
                writer_observation = {
                    "transaction_active": connection.in_transaction() and connection.connection.in_transaction,
                    "target_rows": {
                        "search_request": cursor.execute("SELECT count(*) FROM search_request WHERE id = ?", (request_id,)).fetchone()[0],
                        "request_alternative": cursor.execute("SELECT count(*) FROM request_alternative WHERE request_id = ?", (request_id,)).fetchone()[0],
                        "request_alternative_evidence": cursor.execute("""SELECT count(*) FROM request_alternative_evidence link
                            JOIN request_alternative option ON option.id = link.option_id WHERE option.request_id = ?""", (request_id,)).fetchone()[0],
                    },
                }
            finally:
                cursor.close()
            independent_during = observe()
            timeline.append("preceding_writes_observed_in_active_transaction")

    def after_insert(connection, _cursor, _statement, _parameters, context, _executemany):
        table = insert_table(context)
        if connection is writer and table in succeeded:
            succeeded[table] += 1
            timeline.append(f"{table}:insert_succeeded")

    def rejected_insert(context):
        if context.connection is writer and insert_table(context.execution_context) == "request_alternative":
            rejection.append({"sqlite_integrity_error": isinstance(context.original_exception, sqlite3.IntegrityError),
                "sqlite_trigger_rejection": getattr(context.original_exception, "sqlite_errorname", None) == "SQLITE_CONSTRAINT_TRIGGER",
                "second_option_attempt": attempted["request_alternative"] == 2})
            timeline.append("sqlite_rejected_second_option_insert")

    def committed(connection):
        if connection is writer:
            calls["writer_commits"] += 1

    def rolled_back(connection):
        if connection is writer:
            calls["writer_rollbacks"] += 1
            timeline.append("production_writer_rollback")

    listeners = (("before_cursor_execute", before_insert), ("after_cursor_execute", after_insert),
        ("handle_error", rejected_insert), ("commit", committed), ("rollback", rolled_back))
    app = create_app(service)

    async def count_target_posts(scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "POST" and scope["path"] == "/api/comparisons":
            calls["target_http_posts"] += 1
            timeline.append("target_http_post")
        await app(scope, receive, send)

    try:
        with sqlite3.connect(path) as connection:
            connection.execute(f"""CREATE TRIGGER reject_target_second_option BEFORE INSERT ON request_alternative
                WHEN NEW.position = 2 AND EXISTS (SELECT 1 FROM search_request
                    WHERE id = NEW.request_id AND submission_key_digest = '{target_key_digest}')
                BEGIN SELECT RAISE(ABORT, 'synthetic required-option write rejection'); END""")
        store.save = save
        for name, listener in listeners:
            event.listen(engine, name, listener)
        with TestClient(count_target_posts) as target_client:
            response = target_client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": token_hex(32)})
        timeline.append("actual_api_response")
        expected_body = {"outcome": "persistence_error", "persistence": {"state": "failed"},
            "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
        assert response.status_code == 503
        body = response.json()
        accepted_response_only = body == expected_body
        assert accepted_response_only
        assert calls == {"target_http_posts": 1, "save": 1, "writer_commits": 0, "writer_rollbacks": 1}
        assert attempted == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 1}
        assert succeeded == {"search_request": 1, "request_alternative": 1, "request_alternative_evidence": 1}
        assert rejection == [{"sqlite_integrity_error": True, "sqlite_trigger_rejection": True, "second_option_attempt": True}]
        assert writer_observation == {"transaction_active": True,
            "target_rows": {"search_request": 1, "request_alternative": 1, "request_alternative_evidence": 1}}
        assert independent_during == before
        assert timeline == ["target_http_post", "real_save_entered", "search_request:insert_attempted", "search_request:insert_succeeded",
            "request_alternative:insert_attempted", "request_alternative:insert_succeeded",
            "request_alternative_evidence:insert_attempted", "request_alternative_evidence:insert_succeeded",
            "request_alternative:insert_attempted", "preceding_writes_observed_in_active_transaction",
            "sqlite_rejected_second_option_insert", "production_writer_rollback", "actual_api_response"]
        assert len(planned) == 1 and len(set(planned[0]["option_ids"])) == 2
        failed_request_id, failed_option_ids = planned[0]["request_id"], planned[0]["option_ids"]
        with sqlite3.connect(path) as connection:
            absent = {
                "request_id": connection.execute("SELECT count(*) FROM search_request WHERE id = ?", (failed_request_id,)).fetchone()[0] == 0,
                "submission_key": connection.execute("SELECT count(*) FROM search_request WHERE submission_key_digest = ?", (target_key_digest,)).fetchone()[0] == 0,
                "options": connection.execute("SELECT count(*) FROM request_alternative WHERE request_id = ? OR id IN (?, ?)",
                    (failed_request_id, *failed_option_ids)).fetchone()[0] == 0,
                "evidence_links": connection.execute("SELECT count(*) FROM request_alternative_evidence WHERE option_id IN (?, ?)",
                    failed_option_ids).fetchone()[0] == 0,
            }
        assert all(absent.values())
        after = observe()
        assert after == before
        full_request_rows_preserved = full_request_rows() == protected_baseline_requests
        assert full_request_rows_preserved
    finally:
        store.save = real_save
        for name, listener in listeners:
            if event.contains(engine, name, listener):
                event.remove(engine, name, listener)
        with sqlite3.connect(path) as connection:
            connection.execute("DROP TRIGGER IF EXISTS reject_target_second_option")

    with sqlite3.connect(path) as connection:
        trigger_removed = connection.execute("SELECT count(*) FROM sqlite_master WHERE type = 'trigger' AND name = 'reject_target_second_option'").fetchone()[0] == 0
    cleanup = {"trigger_removed": trigger_removed, "observers_removed": all(not event.contains(engine, name, listener) for name, listener in listeners),
        "save_wrapper_restored": store.save == real_save}
    assert all(cleanup.values())
    (path.parent / "option-write-failure-evidence.json").write_text(json.dumps({
        "scope": "One required second-option INSERT rejection; no retry journey.",
        "failed_stage": "second_request_alternative_insert", "planned_failed_identities": planned[0],
        "calls": calls, "counter_scope": "Target request after the separate successful preservation baseline.",
        "attempted_inserts": attempted, "successful_inserts": succeeded, "sqlite_rejection": rejection,
        "writer_before_rejected_insert": writer_observation, "timeline": timeline,
        "actual_response": {"status": response.status_code, "body": body},
        "before": before, "independent_during": independent_during, "after": after,
        "failed_identities_absent": absent, "full_prior_request_rows_preserved": full_request_rows_preserved,
        "cleanup": cleanup, "observer_rows_supplied_to_application": False,
        "raw_proofs_headers_complete_requests_bindings_parameters_or_exception_contexts_recorded": False,
    }, indent=2) + "\n")


def test_same_submission_is_acknowledged_without_replaying_a_comparison(system):
    client, path, _ = system
    payload = submission()
    headers = {"X-Submission-Proof": "a" * 64}
    saved = client.post("/api/comparisons", json=payload, headers=headers).json()
    again = client.post("/api/comparisons", json=payload, headers=headers)
    assert again.status_code == 200
    assert again.json()["outcome"] == "submission_recovered"
    assert again.json()["persistence"] == saved["persistence"]
    assert "comparison" not in again.json()
    assert client.post("/api/comparisons", json=payload).status_code == 403
    assert client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64}).status_code == 403
    payload["text"] += " changed"
    assert client.post("/api/comparisons", json=payload, headers=headers).status_code == 409
    assert counts(path)["search_request"] == 1


def test_committed_save_with_lost_response_recovers_only_original_acknowledgement(system):
    _, path, service = system
    payload = submission()
    headers = {"X-Submission-Proof": "a" * 64}
    app = create_app(service)
    delivered = []

    class ResponseLost(RuntimeError):
        pass

    async def lose_committed_response(scope, receive, send):
        async def drop_after_commit(message):
            if message["type"] == "http.response.start" and message["status"] == 201:
                assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
                raise ResponseLost("Synthetic delivery loss after successful commit")
            delivered.append(message)
            await send(message)

        await app(scope, receive, drop_after_commit if scope["type"] == "http" else send)

    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}
    with TestClient(lose_committed_response) as lost_client:
        with pytest.raises(ResponseLost, match="after successful commit"):
            lost_client.post("/api/comparisons", json=payload, headers=headers)
    assert delivered == []

    def stored_state():
        with sqlite3.connect(path) as connection:
            return {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                for table in ("search_request", "request_alternative", "request_alternative_evidence", "evidence")}

    committed = stored_state()
    with sqlite3.connect(path) as connection:
        original = json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0])

    class NeverReassess:
        def __getattr__(self, name):
            pytest.fail(f"Committed recovery must not invoke {name}")

    def never_read_clock():
        pytest.fail("Acknowledgement must retain the original assessment timestamp")

    recovery_service = replace(service, interpreter=NeverReassess(), knowledge=NeverReassess(),
        renderer=NeverReassess(), clock=never_read_clock)
    with TestClient(create_app(recovery_service)) as recovery_client:
        recovered = recovery_client.post("/api/comparisons", json=payload, headers=headers)
        assert recovered.status_code == 200
        assert recovered.json() == {
            "outcome": "submission_recovered", "persistence": original["persistence"],
            "saved_outcome": "comparison", "assessed_at": original["assessed_at"],
        }
        denied = recovery_client.post("/api/comparisons", json=payload)
        unknown = recovery_client.post("/api/comparisons", json={**payload, "submission_key": str(uuid4())})
        wrong_proof = recovery_client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64})
        assert denied.status_code == unknown.status_code == wrong_proof.status_code == 403
        assert denied.json() == unknown.json() == wrong_proof.json() == {
            "outcome": "recovery_not_authorized", "persistence": {"state": "not_attempted"},
            "issues": [{"code": "originating_proof_required"}],
        }
        changed = recovery_client.post("/api/comparisons", json={**payload, "text": EXAMPLE + " changed"}, headers=headers)
        assert changed.status_code == 409
        assert changed.json() == {
            "outcome": "submission_key_conflict", "persistence": {"state": "not_attempted"},
            "issues": [{"code": "payload_changed"}],
        }
    assert stored_state() == committed
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}


def test_fresh_search_after_recovered_save_reassesses_at_later_clock_without_mutating_original(tmp_path, monkeypatch):
    from datetime import timedelta
    from secrets import token_hex

    from tests.support.source_bound_rendering import create_demo_service
    from tests.support.synthetic import FIXTURE_TIME, SyntheticInterpreter, SyntheticKnowledge, SyntheticRenderer

    path = tmp_path / "fresh-search.sqlite3"
    assessed_at = FIXTURE_TIME
    calls = dict.fromkeys(("interpret", "retrieve", "prepare", "prepare_coverage", "clock"), 0)

    def spy(adapter, method):
        original = getattr(adapter, method)

        def counted(self, *args, **kwargs):
            calls[method] += 1
            return original(self, *args, **kwargs)

        monkeypatch.setattr(adapter, method, counted)

    for adapter, method in ((SyntheticInterpreter, "interpret"), (SyntheticKnowledge, "retrieve"),
            (SyntheticRenderer, "prepare"), (SyntheticRenderer, "prepare_coverage")):
        spy(adapter, method)

    def clock():
        calls["clock"] += 1
        return assessed_at

    service = create_demo_service(path, clock=clock)
    calls.update(dict.fromkeys(calls, 0))
    payload = {**submission(), "language_context": {"browser_language": "en"}}
    original_proof = token_hex(32)
    headers = {"X-Submission-Proof": original_proof}

    def original_state(request_id):
        with sqlite3.connect(path) as connection:
            return {
                "request": connection.execute("SELECT * FROM search_request WHERE id = ?", (request_id,)).fetchall(),
                "options": connection.execute(
                    "SELECT * FROM request_alternative WHERE request_id = ? ORDER BY position", (request_id,)).fetchall(),
                "associations": connection.execute(
                    "SELECT association.* FROM request_alternative_evidence AS association "
                    "JOIN request_alternative AS option ON association.option_id = option.id "
                    "WHERE option.request_id = ? ORDER BY 1, 2", (request_id,)).fetchall(),
                "evidence": connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall(),
            }

    try:
        with TestClient(create_app(service)) as client:
            saved = client.post("/api/comparisons", json=payload, headers=headers)
            assert saved.status_code == 201
            original = saved.json()
            assert original["outcome"] == "comparison"
            assert original["assessed_at"] == FIXTURE_TIME.isoformat()
            assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            snapshot = original_state(original["persistence"]["request_id"])
            expected_acknowledgement = {
                "outcome": "submission_recovered", "persistence": original["persistence"],
                "saved_outcome": "comparison", "assessed_at": original["assessed_at"],
            }
            initial_calls = {"interpret": 1, "retrieve": 1, "prepare": 1, "prepare_coverage": 0, "clock": 1}
            assert calls == initial_calls
            recovered = client.post("/api/comparisons", json=payload, headers=headers)
            assert recovered.status_code == 200
            assert recovered.json() == expected_acknowledgement
            assert calls == initial_calls

            assessed_at = FIXTURE_TIME + timedelta(days=366)
            recovered_later = client.post("/api/comparisons", json=payload, headers=headers)
            assert recovered_later.status_code == 200
            assert recovered_later.json() == expected_acknowledgement
            assert calls == initial_calls
            assert original_state(original["persistence"]["request_id"]) == snapshot

            fresh_payload = {**payload, "submission_key": str(uuid4()), "text": "Velo"}
            fresh_proof = token_hex(32)
            proof_changed = fresh_proof != original_proof
            assert proof_changed
            fresh = client.post("/api/comparisons", json=fresh_payload,
                headers={"X-Submission-Proof": fresh_proof})
            assert fresh.status_code == 201
            body = fresh.json()
            assert body["outcome"] == "insufficient_coverage"
            assert body["persistence"]["state"] == "saved"
            fresh_id = body["persistence"]["request_id"]
            UUID(fresh_id)
            assert fresh_id != original["persistence"]["request_id"]
            assert body["assessed_at"] == assessed_at.isoformat()
            assert "essential_evidence_expired" in body["coverage"]["limitation_codes"]
            assert "comparison" not in body
            assert calls == {"interpret": 2, "retrieve": 2, "prepare": 1, "prepare_coverage": 1, "clock": 2}
            assert counts(path) == {"search_request": 2, "request_alternative": 2, "request_alternative_evidence": 2}
            assert original_state(original["persistence"]["request_id"]) == snapshot
            with sqlite3.connect(path) as connection:
                text, location, language_context, projection = connection.execute(
                    "SELECT original_text, search_location, language_context, projection FROM search_request WHERE id = ?",
                    (fresh_id,),
                ).fetchone()
            assert text == "Velo"
            assert json.loads(location) == {"country_code": "CH"}
            assert json.loads(language_context) == {"browser_language": "en"}
            assert json.loads(projection) == body
    finally:
        service.store.engine.dispose()


@pytest.mark.parametrize("case", ["matching", "wrong_proof_changed_payload", "same_proof_changed_payload"])
def test_concurrent_same_submission_commits_one_winner_and_acknowledges_loser(tmp_path, monkeypatch, case):
    from concurrent.futures import ThreadPoolExecutor
    from secrets import token_hex
    from threading import Barrier, Event, Lock

    from sqlalchemy import event

    from app.application import comparisons
    from app.application.comparisons import DuplicateSubmission, digest
    from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
    from tests.support.synthetic import FIXTURE_TIME, create_service

    path = tmp_path / "concurrent.sqlite3"
    base = create_service(path)
    stores = {"winner": base.store, "loser": SQLiteComparisonStore(path)}
    initial_reads = Barrier(2, timeout=5)
    prepared_saves = Barrier(2, timeout=5)
    winner_committed = Event()
    lock = Lock()
    timeline, proof_payload_checks = [], []
    missed, prepared, bindings = {}, {}, {}
    calls = {role: {"find": 0, "save": 0} for role in stores}
    connections = {role: set() for role in stores}
    collisions, collision_connections, rollbacks = [], [], []

    def record(value):
        with lock:
            timeline.append(value)

    for role, store in stores.items():
        def checkout(connection, _record, _proxy, role=role):
            connections[role].add(id(connection))

        event.listen(store.engine, "checkout", checkout)

    def collision(context):
        error = context.original_exception
        collisions.append({"sqlite_errorname": getattr(error, "sqlite_errorname", None),
            "unique_submission_key": isinstance(error, sqlite3.IntegrityError)
                and str(error) == "UNIQUE constraint failed: search_request.submission_key_digest"})
        collision_connections.append(context.connection)
        record("loser:unique_insert_rejected")

    def rollback(connection):
        if collision_connections and connection is collision_connections[0]:
            rollbacks.append(True)
            record("loser:rollback")

    event.listen(stores["loser"].engine, "handle_error", collision)
    event.listen(stores["loser"].engine, "rollback", rollback)
    original_compare = comparisons.compare_digest

    def checked_compare(left, right):
        result = original_compare(left, right)
        proof_payload_checks.append(result)
        record("loser:ownership_check" if len(proof_payload_checks) == 1 else "loser:payload_check")
        return result

    monkeypatch.setattr(comparisons, "compare_digest", checked_compare)

    class CoordinatedStore:
        def __init__(self, role):
            self.role = role
            self.store = stores[role]

        def find(self, key):
            calls[self.role]["find"] += 1
            saved = self.store.find(key)
            if calls[self.role]["find"] == 1:
                missed[self.role] = saved is None
                assert saved is None
                record(f"{self.role}:initial_lookup_missed")
                initial_reads.wait()
            else:
                assert saved is not None
                record(f"{self.role}:committed_lookup")
            return saved

        def save(self, value):
            calls[self.role]["save"] += 1
            prepared[self.role] = json.loads(json.dumps(value.projection))
            bindings[self.role] = (value.key_digest, value.proof_binding, value.payload_digest)
            record(f"{self.role}:prepared")
            prepared_saves.wait()
            if self.role == "loser":
                assert winner_committed.wait(timeout=5)
            try:
                committed = self.store.save(value)
            except DuplicateSubmission:
                record(f"{self.role}:duplicate_submission")
                raise
            record(f"{self.role}:committed")
            winner_committed.set()
            return committed

    payload = submission()
    proof = token_hex(32)
    payloads = {"winner": payload, "loser": json.loads(json.dumps(payload))}
    proofs = {"winner": proof, "loser": token_hex(32) if case == "wrong_proof_changed_payload" else proof}
    if case != "matching":
        payloads["loser"]["language_context"] = {"preferred_language": "en"}
    before = counts(path)
    with sqlite3.connect(path) as connection:
        evidence_before = connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall()

    def execute(role):
        service = replace(base, store=CoordinatedStore(role))
        with TestClient(create_app(service)) as client:
            response = client.post("/api/comparisons", json=payloads[role], headers={"X-Submission-Proof": proofs[role]})
            return {"status": response.status_code, "body": response.json()}

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {role: executor.submit(execute, role) for role in stores}
            responses = {role: future.result(timeout=15) for role, future in futures.items()}

        assert missed == {"winner": True, "loser": True}
        assert calls == {"winner": {"find": 1, "save": 1}, "loser": {"find": 2, "save": 1}}
        same_key = bindings["winner"][0] == bindings["loser"][0]
        same_proof_binding = bindings["winner"][1] == bindings["loser"][1]
        same_payload_binding = bindings["winner"][2] == bindings["loser"][2]
        assert same_key
        assert same_proof_binding == (case != "wrong_proof_changed_payload")
        assert same_payload_binding == (case == "matching")
        assert connections["winner"] and connections["loser"]
        assert connections["winner"].isdisjoint(connections["loser"])
        assert collisions == [{"sqlite_errorname": "SQLITE_CONSTRAINT_UNIQUE", "unique_submission_key": True}]
        assert rollbacks == [True]
        expected_checks = {"matching": [True, True], "wrong_proof_changed_payload": [False],
            "same_proof_changed_payload": [True, False]}[case]
        assert proof_payload_checks == expected_checks
        committed_index = timeline.index("winner:committed")
        for role in stores:
            assert timeline.index(f"{role}:initial_lookup_missed") < timeline.index(f"{role}:prepared") < committed_index
        branch = ["winner:committed", "loser:unique_insert_rejected", "loser:rollback",
            "loser:duplicate_submission", "loser:committed_lookup", "loser:ownership_check"]
        if case != "wrong_proof_changed_payload":
            branch.append("loser:payload_check")
        else:
            assert "loser:payload_check" not in timeline
        assert [timeline.index(item) for item in branch] == sorted(timeline.index(item) for item in branch)

        winner, loser = responses["winner"], responses["loser"]
        assert winner["status"] == 201
        assert winner["body"] == prepared["winner"]
        assert winner["body"]["outcome"] == "comparison"
        assert winner["body"]["assessed_at"] == FIXTURE_TIME.isoformat()
        if case == "matching":
            assert loser == {"status": 200, "body": {
                "outcome": "submission_recovered", "persistence": winner["body"]["persistence"],
                "saved_outcome": "comparison", "assessed_at": FIXTURE_TIME.isoformat(),
            }}
        elif case == "wrong_proof_changed_payload":
            assert loser == {"status": 403, "body": {
                "outcome": "recovery_not_authorized", "persistence": {"state": "not_attempted"},
                "issues": [{"code": "originating_proof_required"}],
            }}
        else:
            assert loser == {"status": 409, "body": {
                "outcome": "submission_key_conflict", "persistence": {"state": "not_attempted"},
                "issues": [{"code": "payload_changed"}],
            }}
        winner_id = winner["body"]["persistence"]["request_id"]
        loser_id = prepared["loser"]["persistence"]["request_id"]
        assert winner_id != loser_id
        assert prepared["loser"]["outcome"] == "comparison"
        assert prepared["loser"]["assessed_at"] == FIXTURE_TIME.isoformat()
        winner_options = winner["body"]["comparison"]["options"]
        loser_options = prepared["loser"]["comparison"]["options"]
        assert {o["option_id"] for o in winner_options}.isdisjoint(o["option_id"] for o in loser_options)
        after = counts(path)
        assert before == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}
        assert after == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT id, submission_key_digest, projection FROM search_request").fetchall()
            saved_options = connection.execute("SELECT id, request_id, snapshot FROM request_alternative ORDER BY position").fetchall()
            associations = connection.execute("SELECT * FROM request_alternative_evidence ORDER BY 1, 2").fetchall()
            evidence_after = connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall()
        committed_row_matches = [(identity, key_digest, json.loads(projection)) for identity, key_digest, projection in rows] == [
            (winner_id, digest(payload["submission_key"]), winner["body"])]
        assert committed_row_matches
        for (option_id, request_id, snapshot), option in zip(saved_options, winner_options, strict=True):
            assert (option_id, request_id, json.loads(snapshot)) == (option["option_id"], winner_id, option)
        assert associations == sorted((option["option_id"], source["version_id"])
            for option in winner_options for source in option["evidence"])
        assert evidence_after == evidence_before
        artifact = {"case": case, "both_initial_lookups_missed": missed, "timeline": timeline,
            "requests": 2, "store_port_calls": calls,
            "separate_connection_counts": {role: len(values) for role, values in connections.items()},
            "execution_connections_disjoint": True,
            "input_binding_equality": {"same_submission_key": same_key, "same_originating_proof": same_proof_binding,
                "same_canonical_payload": same_payload_binding},
            "sqlite_collisions": collisions, "collision_rollback_count": len(rollbacks),
            "ownership_payload_check_results": proof_payload_checks,
            "payload_check_performed": case != "wrong_proof_changed_payload",
            "prepared_outcomes": {role: value["outcome"] for role, value in prepared.items()},
            "winner": winner, "loser": loser, "before_counts": before, "after_counts": after,
            "discarded_loser_request_id": loser_id,
            "discarded_loser_option_ids": [option["option_id"] for option in loser_options],
            "committed_evidence_associations": associations, "evidence_unchanged": True,
            "source_evidence_sha256": digest(evidence_after), "raw_originating_proofs_recorded": False}
        (tmp_path / "concurrent-save-evidence.json").write_text(json.dumps(artifact, indent=2) + "\n")
    finally:
        for store in stores.values():
            store.engine.dispose()


def test_unconfirmed_commit_and_unavailable_readback_stay_unknown_until_explicit_recovery(tmp_path, monkeypatch):
    from secrets import token_hex

    from sqlalchemy.engine.base import RootTransaction

    from tests.support.synthetic import FIXTURE_TIME, create_service

    path = tmp_path / "uncertain.sqlite3"
    service = create_service(path)
    store = service.store
    calls = dict.fromkeys(("interpret", "retrieve", "prepare", "prepare_coverage", "find", "save", "clock", "api"), 0)
    faults = {"real_commits": 0, "confirmation_losses": 0, "read_failures": 0}
    writes = dict.fromkeys(("search_request", "request_alternative", "request_alternative_evidence"), 0)
    timeline, cleanup, driver_rollbacks = [], [], []
    observer_after_commit = []
    commit_unconfirmed = False

    def watch(adapter, method, name):
        original = getattr(adapter, method)

        def counted(*args, **kwargs):
            calls[name] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(adapter, method, counted)

    for adapter, method, name in ((service.interpreter, "interpret", "interpret"),
            (service.knowledge, "retrieve", "retrieve"), (service.renderer, "prepare", "prepare"),
            (service.renderer, "prepare_coverage", "prepare_coverage"), (store, "find", "find"), (store, "save", "save")):
        watch(adapter, method, name)

    def clock():
        calls["clock"] += 1
        return FIXTURE_TIME

    service = replace(service, clock=clock)

    def observe():
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT id, projection FROM search_request ORDER BY id").fetchall()
            return {
                "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in writes},
                "requests": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
                "options": connection.execute("SELECT id, request_id, snapshot FROM request_alternative ORDER BY position").fetchall(),
                "links": connection.execute("SELECT * FROM request_alternative_evidence ORDER BY 1, 2").fetchall(),
                "evidence": connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall(),
            }

    dialect = store.engine.dialect
    real_commit, real_execute, real_rollback = dialect.do_commit, dialect.do_execute, dialect.do_rollback
    real_cleanup = RootTransaction.rollback

    def lose_commit_confirmation(connection):
        nonlocal commit_unconfirmed
        timeline.append("dbapi_commit_entered")
        real_commit(connection)
        faults["real_commits"] += 1
        timeline.append("real_sqlite_commit_returned_to_test_shim")
        observer_after_commit.append(observe())
        timeline.append("independent_observer_sees_committed_rows_test_only")
        commit_unconfirmed = True
        faults["confirmation_losses"] += 1
        timeline.append("commit_confirmation_error_before_return_to_production")
        raise sqlite3.OperationalError("Synthetic commit confirmation unavailable")

    def fail_reconciliation(cursor, statement, parameters, context=None):
        normalized = statement.lstrip().lower()
        for table in writes:
            if normalized.startswith(f"insert into {table} "):
                writes[table] += 1
        if commit_unconfirmed and faults["read_failures"] == 0 and normalized.startswith("select search_request."):
            faults["read_failures"] += 1
            timeline.append("production_reconciliation_select_unavailable")
            raise sqlite3.OperationalError("Synthetic committed readback unavailable")
        return real_execute(cursor, statement, parameters, context)

    def observe_cleanup(transaction):
        if transaction.connection.engine is store.engine and commit_unconfirmed:
            cleanup.append({"active_before": transaction.is_active})
            timeline.append("commit_error_transaction_rollback_cleanup_entered")
            result = real_cleanup(transaction)
            timeline.append("commit_error_transaction_rollback_cleanup_returned")
            return result
        return real_cleanup(transaction)

    def observe_driver_rollback(connection):
        driver_rollbacks.append({"after_confirmation_loss": commit_unconfirmed,
            "sqlite_in_transaction_before": connection.in_transaction})
        return real_rollback(connection)

    monkeypatch.setattr(RootTransaction, "rollback", observe_cleanup)
    monkeypatch.setattr(dialect, "do_rollback", observe_driver_rollback)
    app = create_app(service)

    @app.middleware("http")
    async def count_api(request, call_next):
        calls["api"] += 1
        return await call_next(request)

    payload = submission()
    captured_payload = json.loads(json.dumps(payload))
    proof = token_hex(32)
    before = observe()
    try:
        with TestClient(app) as client:
            with monkeypatch.context() as injected:
                injected.setattr(dialect, "do_commit", lose_commit_confirmation)
                injected.setattr(dialect, "do_execute", fail_reconciliation)
                response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": proof})
                timeline.append("first_api_response")
            timeline.append("injected_faults_removed")
            after_error = observe()
            first_calls = dict(calls)
            (tmp_path / "uncertain-error-evidence.json").write_text(json.dumps({
                "status": response.status_code, "body": response.json(), "faults": faults,
                "calls": first_calls, "timeline": timeline, "independent_after_error": after_error,
                "raw_originating_proofs_recorded": False}, indent=2) + "\n")
            assert response.status_code == 503
            assert response.json() == {"outcome": "persistence_error", "persistence": {"state": "unknown"},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
            assert faults == {"real_commits": 1, "confirmation_losses": 1, "read_failures": 1}
            assert cleanup == [{"active_before": False}]
            assert first_calls == {"interpret": 1, "retrieve": 1, "prepare": 1, "prepare_coverage": 0,
                "find": 2, "save": 1, "clock": 1, "api": 1}
            assert before["counts"] == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}
            assert after_error["counts"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            assert observer_after_commit == [after_error]
            assert before["evidence"] == after_error["evidence"]
            original = after_error["requests"][0]["projection"]
            assert original["outcome"] == "comparison"
            assert original["assessed_at"] == FIXTURE_TIME.isoformat()
            branch = ["commit_confirmation_error_before_return_to_production",
                "commit_error_transaction_rollback_cleanup_returned", "production_reconciliation_select_unavailable", "first_api_response"]
            assert [timeline.index(item) for item in branch] == sorted(timeline.index(item) for item in branch)

            timeline.append("explicit_recovery_requested")
            recovered = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": proof})
            assert recovered.status_code == 200
            assert recovered.json() == {"outcome": "submission_recovered", "persistence": original["persistence"],
                "saved_outcome": "comparison", "assessed_at": original["assessed_at"]}
            assert calls == {**first_calls, "find": 3, "api": 2}
            assert writes == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            assert payload == captured_payload
            after_recovery = observe()
            assert after_recovery == after_error
            artifact = {"fault_boundaries": timeline, "fault_counts": faults,
                "transaction_rollback_cleanup": cleanup, "driver_rollback_observations": driver_rollbacks,
                "calls_at_error": first_calls, "calls_after_recovery": calls, "insert_attempts": writes,
                "before": before, "independent_after_real_commit": observer_after_commit[0],
                "after_error": after_error, "after_recovery": after_recovery,
                "initial_response": {"status": response.status_code, "body": response.json()},
                "recovery_response": {"status": recovered.status_code, "body": recovered.json()},
                "observer_rows_supplied_to_application": False, "same_key_proof_captured_payload": True,
                "raw_originating_proofs_recorded": False}
            (tmp_path / "uncertain-recovery-evidence.json").write_text(json.dumps(artifact, indent=2) + "\n")
    finally:
        store.engine.dispose()


@pytest.mark.parametrize("reconciliation", ["found", "absent"])
def test_unconfirmed_commit_reconciliation_found_or_absent(tmp_path, monkeypatch, reconciliation):
    from secrets import token_hex

    from sqlalchemy.engine.base import RootTransaction

    from app.application import comparisons
    from app.application.comparisons import DuplicateSubmission
    from tests.support.synthetic import FIXTURE_TIME, create_service

    path = tmp_path / "reconciliation.sqlite3"
    service = create_service(path)
    store = service.store
    calls = dict.fromkeys(("interpret", "retrieve", "prepare", "prepare_coverage", "save", "clock", "api"), 0)
    lookups = dict.fromkeys(("application_initial", "adapter_reconciliation", "application_duplicate_lookup"), 0)
    selects = dict.fromkeys(lookups, 0)
    writes = dict.fromkeys(("search_request", "request_alternative", "request_alternative_evidence"), 0)
    faults = {"real_commits": 0, "confirmation_errors": 0, "duplicate_submissions": 0}
    timeline, lookup_results, checks, prepared_projections = [], [], [], []
    cleanup, driver_rollbacks, observer_after_commit = [], [], []
    bindings = ()
    in_save, commit_unconfirmed, lookup_scope = False, False, None

    def watch(adapter, method):
        original = getattr(adapter, method)

        def counted(*args, **kwargs):
            calls[method] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(adapter, method, counted)

    for adapter, method in ((service.interpreter, "interpret"), (service.knowledge, "retrieve"),
            (service.renderer, "prepare"), (service.renderer, "prepare_coverage")):
        watch(adapter, method)

    real_find, real_save = store.find, store.save

    def find(key):
        nonlocal lookup_scope
        scope = "adapter_reconciliation" if in_save else (
            "application_initial" if lookups["application_initial"] == 0 else "application_duplicate_lookup")
        lookups[scope] += 1
        lookup_scope = scope
        try:
            saved = real_find(key)
        finally:
            lookup_scope = None
        lookup_results.append({"scope": scope, "found": saved is not None})
        timeline.append(f"{scope}:{'found' if saved is not None else 'absent'}")
        return saved

    def save(prepared):
        nonlocal in_save, bindings
        calls["save"] += 1
        prepared_projections.append(json.loads(json.dumps(prepared.projection)))
        bindings = (prepared.proof_binding, prepared.payload_digest)
        in_save = True
        try:
            return real_save(prepared)
        except DuplicateSubmission:
            faults["duplicate_submissions"] += 1
            timeline.append("actual_duplicate_submission")
            raise
        finally:
            in_save = False

    real_compare = comparisons.compare_digest

    def checked_compare(left, right):
        result = real_compare(left, right)
        check = "ownership" if left == bindings[0] else "payload" if left == bindings[1] else "unexpected"
        checks.append({"check": check, "matched": result})
        timeline.append(f"{check}_check")
        return result

    monkeypatch.setattr(store, "find", find)
    monkeypatch.setattr(store, "save", save)
    monkeypatch.setattr(comparisons, "compare_digest", checked_compare)

    def clock():
        calls["clock"] += 1
        return FIXTURE_TIME

    service = replace(service, clock=clock)

    def observe():
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT id, projection FROM search_request ORDER BY id").fetchall()
            return {
                "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in writes},
                "requests": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
                "options": connection.execute("SELECT id, request_id, snapshot FROM request_alternative ORDER BY position").fetchall(),
                "links": connection.execute("SELECT * FROM request_alternative_evidence ORDER BY 1, 2").fetchall(),
                "evidence": connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall(),
            }

    dialect = store.engine.dialect
    real_commit, real_execute, real_rollback = dialect.do_commit, dialect.do_execute, dialect.do_rollback
    real_cleanup = RootTransaction.rollback

    def lose_commit_confirmation(connection):
        nonlocal commit_unconfirmed
        timeline.append("dbapi_commit_entered")
        if reconciliation == "found":
            real_commit(connection)
            faults["real_commits"] += 1
            timeline.append("real_sqlite_commit_returned_to_test_shim")
            observer_after_commit.append(observe())
            timeline.append("independent_observer_sees_committed_rows_test_only")
        else:
            timeline.append("test_fault_before_underlying_dbapi_commit")
        commit_unconfirmed = True
        faults["confirmation_errors"] += 1
        timeline.append("generic_commit_error_before_return_to_production")
        raise sqlite3.OperationalError("Synthetic commit confirmation unavailable")

    def count_execute(cursor, statement, parameters, context=None):
        normalized = statement.lstrip().lower()
        for table in writes:
            if normalized.startswith(f"insert into {table} "):
                writes[table] += 1
        if normalized.startswith("select search_request."):
            assert lookup_scope in selects
            selects[lookup_scope] += 1
        return real_execute(cursor, statement, parameters, context)

    def observe_cleanup(transaction):
        if transaction.connection.engine is store.engine and commit_unconfirmed:
            cleanup.append({"active_before": transaction.is_active})
            result = real_cleanup(transaction)
            timeline.append("commit_error_transaction_cleanup_returned")
            return result
        return real_cleanup(transaction)

    def observe_driver_rollback(connection):
        driver_rollbacks.append({"after_commit_error": commit_unconfirmed,
            "sqlite_in_transaction_before": connection.in_transaction})
        return real_rollback(connection)

    app = create_app(service)

    @app.middleware("http")
    async def count_api(request, call_next):
        calls["api"] += 1
        return await call_next(request)

    before = observe()
    try:
        with TestClient(app) as client, monkeypatch.context() as injected:
            injected.setattr(dialect, "do_commit", lose_commit_confirmation)
            injected.setattr(dialect, "do_execute", count_execute)
            injected.setattr(dialect, "do_rollback", observe_driver_rollback)
            injected.setattr(RootTransaction, "rollback", observe_cleanup)
            response = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": token_hex(32)})
            timeline.append("original_api_response")
        after = observe()
        assert calls == {"interpret": 1, "retrieve": 1, "prepare": 1, "prepare_coverage": 0,
            "save": 1, "clock": 1, "api": 1}
        assert writes == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
        assert len(prepared_projections) == 1
        prepared = prepared_projections[0]
        assert prepared["outcome"] == "comparison"
        assert prepared["assessed_at"] == FIXTURE_TIME.isoformat()
        assert before["counts"] == {table: 0 for table in writes}
        assert before["evidence"] == after["evidence"]
        assert cleanup == [{"active_before": False}]
        expected_lookups = {"application_initial": 1, "adapter_reconciliation": 1,
            "application_duplicate_lookup": 1 if reconciliation == "found" else 0}
        assert lookups == selects == expected_lookups
        expected_results = [{"scope": "application_initial", "found": False},
            {"scope": "adapter_reconciliation", "found": reconciliation == "found"}]
        branch = ["generic_commit_error_before_return_to_production", "commit_error_transaction_cleanup_returned",
            f"adapter_reconciliation:{reconciliation}"]
        if reconciliation == "found":
            assert faults == {"real_commits": 1, "confirmation_errors": 1, "duplicate_submissions": 1}
            assert after["counts"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            assert observer_after_commit == [after]
            assert after["requests"] == [{"id": prepared["persistence"]["request_id"], "projection": prepared}]
            for (option_id, request_id, snapshot), option in zip(after["options"], prepared["comparison"]["options"], strict=True):
                assert (option_id, request_id, json.loads(snapshot)) == (option["option_id"], prepared["persistence"]["request_id"], option)
            assert after["links"] == sorted((option["option_id"], source["version_id"])
                for option in prepared["comparison"]["options"] for source in option["evidence"])
            expected_results.append({"scope": "application_duplicate_lookup", "found": True})
            assert checks == [{"check": "ownership", "matched": True}, {"check": "payload", "matched": True}]
            assert response.status_code == 200
            assert response.json() == {"outcome": "submission_recovered", "persistence": prepared["persistence"],
                "saved_outcome": "comparison", "assessed_at": FIXTURE_TIME.isoformat()}
            branch.extend(["actual_duplicate_submission", "application_duplicate_lookup:found", "ownership_check", "payload_check"])
        else:
            assert faults == {"real_commits": 0, "confirmation_errors": 1, "duplicate_submissions": 0}
            assert after == before
            assert not observer_after_commit and not checks
            assert any(item["after_commit_error"] and item["sqlite_in_transaction_before"] for item in driver_rollbacks)
            assert response.status_code == 503
            assert response.json() == {"outcome": "persistence_error", "persistence": {"state": "unknown"},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
        assert lookup_results == expected_results
        branch.append("original_api_response")
        assert [timeline.index(item) for item in branch] == sorted(timeline.index(item) for item in branch)
        artifact = {"scenario": reconciliation, "timeline": timeline, "fault_counts": faults,
            "processing_save_api_calls": calls, "logical_lookup_calls": lookups, "real_lookup_selects": selects,
            "lookup_results": lookup_results, "ownership_then_payload_checks": checks, "insert_attempts": writes,
            "transaction_cleanup": cleanup, "driver_rollback_observations": driver_rollbacks,
            "prepared_identity_count": len(prepared_projections), "prepared_request_id": prepared["persistence"]["request_id"],
            "prepared_assessed_at": prepared["assessed_at"], "before": before,
            "independent_after_real_commit": observer_after_commit, "after_response": after,
            "response": {"status": response.status_code, "body": response.json()},
            "observer_rows_supplied_to_application": False, "raw_originating_proofs_recorded": False}
        (tmp_path / f"reconciliation-{reconciliation}-evidence.json").write_text(json.dumps(artifact, indent=2) + "\n")
    finally:
        store.engine.dispose()


def test_commit_confirmation_loss_and_explicit_cleanup_failure_preserve_uncertainty_until_recovery(tmp_path, monkeypatch):
    from secrets import token_hex

    from sqlalchemy import event
    from sqlalchemy.engine.base import RootTransaction
    from sqlalchemy.exc import OperationalError

    from app.application import comparisons
    from tests.support.synthetic import FIXTURE_TIME, create_service

    path = tmp_path / "cleanup-uncertain.sqlite3"
    service = create_service(path)
    store = service.store
    calls = dict.fromkeys(("interpret", "retrieve", "prepare", "prepare_coverage", "find", "save", "clock", "api"), 0)
    faults = {"real_commits": 0, "confirmation_losses": 0, "explicit_cleanup_failures": 0, "read_failures": 0}
    writes = dict.fromkeys(("search_request", "request_alternative", "request_alternative_evidence"), 0)
    timeline, cleanup, prepared_ids, checks, observer_after_commit = [], [], [], [], []
    target_transaction = None
    commit_unconfirmed = False

    def watch(adapter, method, name):
        original = getattr(adapter, method)

        def counted(*args, **kwargs):
            calls[name] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(adapter, method, counted)

    for adapter, method, name in ((service.interpreter, "interpret", "interpret"),
            (service.knowledge, "retrieve", "retrieve"), (service.renderer, "prepare", "prepare"),
            (service.renderer, "prepare_coverage", "prepare_coverage"), (store, "find", "find")):
        watch(adapter, method, name)
    real_save = store.save

    def save(prepared):
        calls["save"] += 1
        prepared_ids.append(prepared.projection["persistence"]["request_id"])
        return real_save(prepared)

    monkeypatch.setattr(store, "save", save)
    real_compare = comparisons.compare_digest

    def checked_compare(left, right):
        matched = real_compare(left, right)
        checks.append(matched)
        return matched

    monkeypatch.setattr(comparisons, "compare_digest", checked_compare)

    def clock():
        calls["clock"] += 1
        return FIXTURE_TIME

    service = replace(service, clock=clock)

    def observe():
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT id, projection FROM search_request ORDER BY id").fetchall()
            return {
                "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in writes},
                "requests": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
                "options": connection.execute("SELECT id, request_id, snapshot FROM request_alternative ORDER BY position").fetchall(),
                "links": connection.execute("SELECT * FROM request_alternative_evidence ORDER BY 1, 2").fetchall(),
                "evidence": connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall(),
            }

    def capture_commit_transaction(connection):
        nonlocal target_transaction
        assert target_transaction is None
        target_transaction = connection.get_transaction()
        assert target_transaction is not None and target_transaction.is_active
        timeline.append("actual_commit_transaction_captured")

    event.listen(store.engine, "commit", capture_commit_transaction)
    dialect = store.engine.dialect
    real_commit, real_execute, real_cleanup = dialect.do_commit, dialect.do_execute, RootTransaction.rollback

    def lose_confirmation(connection):
        nonlocal commit_unconfirmed
        real_commit(connection)
        faults["real_commits"] += 1
        timeline.append("real_sqlite_commit_returned_to_test_shim")
        observer_after_commit.append(observe())
        timeline.append("independent_observer_sees_committed_rows_test_only")
        commit_unconfirmed = True
        faults["confirmation_losses"] += 1
        timeline.append("confirmation_error_before_return_to_production")
        raise sqlite3.OperationalError("Synthetic commit confirmation unavailable")

    def fail_explicit_cleanup(transaction):
        if transaction is target_transaction and commit_unconfirmed and faults["explicit_cleanup_failures"] == 0:
            cleanup.append({"captured_commit_transaction": True, "active_before": transaction.is_active})
            assert not transaction.is_active
            faults["explicit_cleanup_failures"] += 1
            timeline.append("explicit_commit_error_transaction_rollback_failed")
            raise OperationalError(None, None, sqlite3.OperationalError("Synthetic explicit cleanup unavailable"), hide_parameters=True)
        return real_cleanup(transaction)

    def unavailable_reconciliation(cursor, statement, parameters, context=None):
        normalized = statement.lstrip().lower()
        for table in writes:
            if normalized.startswith(f"insert into {table} "):
                writes[table] += 1
        if commit_unconfirmed and faults["read_failures"] == 0 and normalized.startswith("select search_request."):
            faults["read_failures"] += 1
            timeline.append("reconciliation_select_unavailable")
            raise sqlite3.OperationalError("Synthetic committed readback unavailable")
        return real_execute(cursor, statement, parameters, context)

    app = create_app(service)

    @app.middleware("http")
    async def count_api(request, call_next):
        calls["api"] += 1
        return await call_next(request)

    payload = submission()
    proof = token_hex(32)
    before = observe()
    try:
        with TestClient(app) as client:
            with monkeypatch.context() as injected:
                injected.setattr(dialect, "do_commit", lose_confirmation)
                injected.setattr(dialect, "do_execute", unavailable_reconciliation)
                injected.setattr(RootTransaction, "rollback", fail_explicit_cleanup)
                response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": proof})
                timeline.append("initial_api_response")
            timeline.append("all_injected_faults_removed")
            after_error = observe()
            first_calls = dict(calls)
            (tmp_path / "cleanup-error-evidence.json").write_text(json.dumps({
                "response": {"status": response.status_code, "body": response.json()},
                "fault_counts": faults, "timeline": timeline, "explicit_cleanup": cleanup,
                "calls_at_error": first_calls, "independent_after_error": after_error,
                "observer_rows_supplied_to_application": False, "raw_originating_proofs_recorded": False}, indent=2) + "\n")
            assert response.status_code == 503
            assert response.json() == {"outcome": "persistence_error", "persistence": {"state": "unknown"},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": "comparison"}
            assert faults == {"real_commits": 1, "confirmation_losses": 1, "explicit_cleanup_failures": 1, "read_failures": 0}
            assert cleanup == [{"captured_commit_transaction": True, "active_before": False}]
            assert first_calls == {"interpret": 1, "retrieve": 1, "prepare": 1, "prepare_coverage": 0,
                "find": 1, "save": 1, "clock": 1, "api": 1}
            assert not checks
            assert before["counts"] == {table: 0 for table in writes}
            assert after_error["counts"] == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            assert observer_after_commit == [after_error]
            assert before["evidence"] == after_error["evidence"]
            original = after_error["requests"][0]["projection"]
            assert original["outcome"] == "comparison"
            assert original["assessed_at"] == FIXTURE_TIME.isoformat()
            assert prepared_ids == [original["persistence"]["request_id"]]

            timeline.append("explicit_same_submission_recovery")
            recovered = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": proof})
            assert recovered.status_code == 200
            assert recovered.json() == {"outcome": "submission_recovered", "persistence": original["persistence"],
                "saved_outcome": "comparison", "assessed_at": original["assessed_at"]}
            assert calls == {**first_calls, "find": 2, "api": 2}
            assert checks == [True, True]
            assert writes == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
            after_recovery = observe()
            assert after_recovery == after_error
            assert prepared_ids == [original["persistence"]["request_id"]]
            artifact = {"timeline": timeline, "fault_counts": faults, "explicit_cleanup": cleanup,
                "reconciliation": {"attempted": False, "read_fault_armed_but_unconsumed": True,
                    "reason": "Explicit commit-error cleanup failed; persistence outcome cannot safely be established."},
                "calls_at_error": first_calls, "calls_after_recovery": calls, "initial_request_insert_attempts": writes,
                "prepared_request_ids": prepared_ids, "actual_recovery_ownership_payload_checks": checks,
                "before": before, "independent_after_real_commit": observer_after_commit[0],
                "after_error": after_error, "after_recovery": after_recovery,
                "initial_response": {"status": response.status_code, "body": response.json()},
                "recovery_response": {"status": recovered.status_code, "body": recovered.json()},
                "same_key_proof_unchanged_payload": True, "observer_rows_supplied_to_application": False,
                "raw_originating_proofs_recorded": False}
            (tmp_path / "cleanup-recovery-evidence.json").write_text(json.dumps(artifact, indent=2) + "\n")
    finally:
        event.remove(store.engine, "commit", capture_commit_transaction)
        store.engine.dispose()


def test_normal_runtime_never_enables_synthetic_adapters():
    with TestClient(create_app()) as client:
        response = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 503
    assert response.json()["outcome"] == "configuration_unavailable"
    assert "comparison" not in response.json()


def test_fixture_does_not_pretend_to_interpret_other_requests(system):
    client, path, _ = system
    payload = submission()
    payload["text"] = "An arbitrary request not in the fixture"
    response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 503
    assert response.json()["outcome"] == "configuration_unavailable"
    assert counts(path)["search_request"] == 0


def test_evidence_versions_are_immutable(system):
    _, path, _ = system
    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE evidence SET snapshot = '{}'")


@pytest.mark.parametrize("example", [
    {
        "kind": "product", "text": "Find a secondhand laptop", "subject": "laptop", "actions": [],
        "subject_span": {"quote": "laptop", "start": 18, "end": 24},
        "constraints": [{"value": "secondhand", "quote": "secondhand", "start": 7, "end": 17}],
        "alternative_id": "00000000-0000-4000-8000-000000000510",
        "evidence_id": "30000000-0000-4000-8000-000000000510",
        "name": "Reused laptop (synthetic product)", "scope": {"country_code": "CH"},
        "requirements": {"relevance": "laptop", "applicability": True, "secondhand": True},
        "amount": "240.00", "unit": "secondhand laptop", "basis": "fictional item price",
        "exclusions": ["delivery", "accessories"], "attribution": "retailer-stated",
        "publisher": "Fictional laptop retailer", "reference": "synthetic:secondhand-laptop-v1",
        "quote": "Fictional test listing: a secondhand laptop for delivery to CH, CHF 240.00 per secondhand laptop. Delivery and accessories excluded; no real offer or stock claim.",
        "description_contains": ["Fictional", "secondhand laptop", "CH"],
        "explanation_contains": ["240.00", "delivery", "accessories", "fictional"],
    },
    {
        "kind": "habit", "text": "Refill my existing bottle with potable tap water instead of buying bottled water",
        "subject": "drinking_water", "actions": ["refill"],
        "subject_span": {"quote": "potable tap water", "start": 31, "end": 48},
        "action_span": {"quote": "Refill", "start": 0, "end": 6},
        "constraints": [
            {"value": "existing_bottle", "quote": "my existing bottle", "start": 7, "end": 25},
            {"value": "potable_tap_water", "quote": "potable tap water", "start": 31, "end": 48},
            {"value": "avoid_bottled_water", "quote": "instead of buying bottled water", "start": 49, "end": 80,
                "negation": {"quote": "instead of", "start": 49, "end": 59}},
        ],
        "alternative_id": "00000000-0000-4000-8000-000000000520",
        "evidence_id": "30000000-0000-4000-8000-000000000520",
        "name": "Refill an existing bottle (synthetic habit)",
        "scope": {"country_code": "CH", "conditions": ["existing_bottle", "potable_tap_water"]},
        "requirements": {"relevance": "drinking_water", "applicability": True, "action:refill": True,
            "existing_bottle": True, "potable_tap_water": True, "avoid_bottled_water": True},
        "amount": "0.10", "unit": "refill", "basis": "hypothetical flat charge per refill",
        "exclusions": ["bottle purchase", "cleaning"], "attribution": "provider-stated",
        "publisher": "Fictional refill guide", "reference": "synthetic:bottle-refill-habit-v1",
        "quote": "Fictional habit example in CH: refill an existing bottle with potable tap water instead of buying bottled water, conditional on an existing bottle and potable tap water. Hypothetical flat charge CHF 0.10 per refill; bottle purchase and cleaning excluded. No bottle capacity, local water quality, real tariff or environmental advantage is established.",
        "description_contains": ["Fictional", "existing bottle", "potable tap water"],
        "explanation_contains": ["0.10", "flat charge per refill", "bottle purchase", "cleaning", "local tap-water"],
    },
], ids=("product", "habit"))
def test_exact_product_and_habit_examples_qualify_and_persist_with_original_provenance(tmp_path, example):
    from secrets import token_hex

    from tests.support.source_bound_rendering import candidate as hourly_candidate, create_demo_service
    from tests.support.synthetic import FIXTURE_TIME, candidates

    path = tmp_path / "exact-example.sqlite3"
    service = create_demo_service(path)
    legacy_candidates = (*candidates(), hourly_candidate())
    legacy_alternative_ids = {candidate.alternative_id for candidate in legacy_candidates}
    legacy_evidence = {source.version_id: json.loads(json.dumps(source.snapshot))
        for candidate in legacy_candidates for source in candidate.evidence}
    with sqlite3.connect(path) as connection:
        before_evidence = connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall()
        before_alternatives = connection.execute("SELECT * FROM alternative ORDER BY id").fetchall()
    before_counts = counts(path)
    try:
        with TestClient(create_app(service)) as client:
            response = client.post("/api/comparisons", json={"submission_key": str(uuid4()), "text": example["text"],
                "search_location": {"country_code": "CH"}, "location_choice": "provided",
                "language_context": {"browser_language": "en"}}, headers={"X-Submission-Proof": token_hex(32)})
        body = response.json()
        assert response.status_code == 201, body.get("outcome")
        assert body["outcome"] == "comparison" and body["persistence"]["state"] == "saved"
        assert body["assessed_at"] == FIXTURE_TIME.isoformat()
        request_id = body["persistence"]["request_id"]
        UUID(request_id)
        assert body["comparison"]["request_id"] == request_id
        assert body["comparison"]["omitted_count"] == 0
        assert len(body["comparison"]["options"]) == 1
        option = body["comparison"]["options"][0]
        UUID(option["option_id"])
        assert option["alternative_id"] == example["alternative_id"]
        assert option["display_name"] == example["name"] and option["position"] == 1
        assert example["alternative_id"] not in legacy_alternative_ids
        assert example["evidence_id"] not in legacy_evidence
        for needle in example["description_contains"]:
            assert needle.casefold() in option["description"].casefold()
        for needle in example["explanation_contains"]:
            assert needle.casefold() in option["explanation"].casefold()
        assert all(word not in json.dumps(option).casefold() for word in ("bicycle", "repair", "workshop"))
        assert option["rendering"]["language"] == "en" and option["rendering"]["version"]
        assert option["synthetic"] is True
        financial = option["financial"]
        assert {name: financial[name] for name in ("status", "amount", "currency", "unit", "period", "basis", "charges_known", "exclusions")} == {
            "status": "supported", "amount": example["amount"], "currency": "CHF", "unit": example["unit"],
            "period": "once", "basis": example["basis"], "charges_known": False, "exclusions": example["exclusions"]}
        assert financial["total_cost"] is None and financial["difference"] is None and financial["baseline"] is None
        assert option["environmental"]["status"] == "unknown"
        assert option["availability"] == {"status": "unknown", "value": None}
        assert option["geographic_scope"] == example["scope"]
        labels = {claim["claim"]: claim for claim in option["claims"]}
        assert set(labels) == {*example["requirements"], "financial"}
        for key, value in example["requirements"].items():
            assert labels[key]["value"] == value
            assert labels[key]["requirement"] == "satisfied"
        for label in labels.values():
            assert label["support"] == "supported" and label["freshness"] == "fresh"
            assert label["attribution"] == [example["attribution"]]
            assert label["evidence_version_ids"] == [example["evidence_id"]]
            assert label["checked_at"] == [FIXTURE_TIME.isoformat()]
        assert len(option["evidence"]) == 1
        source = option["evidence"][0]
        assert source["version_id"] == example["evidence_id"]
        assert source["publisher"] == example["publisher"] and source["source_reference"] == example["reference"]
        assert source["source_language"] == "en" and source["attribution"] == example["attribution"]
        assert source["supporting_quote"] == example["quote"] and source["scope"] == example["scope"]
        assert source["reviewed_at"] == FIXTURE_TIME.isoformat() and source["synthetic"] is True
        assert set(source["competent_claims"]) == set(labels)
        assert {key: source["assertions"][key] for key in example["requirements"]} == example["requirements"]
        assert counts(path) == {"search_request": before_counts["search_request"] + 1,
            "request_alternative": before_counts["request_alternative"] + 1,
            "request_alternative_evidence": before_counts["request_alternative_evidence"] + 1}
        with sqlite3.connect(path) as connection:
            original, serialized_interpretation, location, choice, context, assessed_at, outcome, projection = connection.execute(
                "SELECT original_text,interpretation,search_location,location_choice,language_context,assessed_at,outcome,projection FROM search_request WHERE id = ?",
                (request_id,)).fetchone()
            saved_options = connection.execute("SELECT id,request_id,alternative_id,position,snapshot FROM request_alternative WHERE request_id = ?",
                (request_id,)).fetchall()
            saved_links = connection.execute("SELECT association.* FROM request_alternative_evidence association JOIN request_alternative option ON option.id = association.option_id WHERE option.request_id = ?",
                (request_id,)).fetchall()
            after_evidence = connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall()
            after_alternatives = connection.execute("SELECT * FROM alternative ORDER BY id").fetchall()
        assert original == example["text"]
        assert json.loads(location) == {"country_code": "CH"} and choice == "provided"
        assert json.loads(context) == {"browser_language": "en"}
        assert assessed_at == FIXTURE_TIME.isoformat() and outcome == "comparison" and json.loads(projection) == body
        interpretation = json.loads(serialized_interpretation)
        assert interpretation["subject"] == example["subject"] and interpretation["subjects"] == [example["subject"]]
        assert interpretation["actions"] == example["actions"]
        assert interpretation["constraints"] == [{"value": constraint["value"], "quote": constraint["quote"]} for constraint in example["constraints"]]
        assert interpretation["goals"] == [] and interpretation["baseline"] is None and interpretation["budget"] is None
        assert interpretation["request_language"] == interpretation["explanation_language"] == "en"
        provenance = interpretation["provenance"]
        assert provenance["meaning_status"] == "understood" and provenance["recognition"]["status"] == "supported"
        assert provenance["recognition"]["language"] == "en"
        expected_items = [("subject", example["subject"], example["subject_span"], None)]
        if example["actions"]:
            expected_items.append(("action", example["actions"][0], example["action_span"], None))
        for constraint in example["constraints"]:
            expected_items.append(("constraint", constraint["value"], {key: constraint[key] for key in ("quote", "start", "end")}, constraint.get("negation")))
        assert len(provenance["items"]) == len(expected_items)
        for kind, normalized, span, negation in expected_items:
            matching = [item for item in provenance["items"] if item["kind"] == kind and item["normalized"] == normalized]
            assert len(matching) == 1
            assert matching[0]["span"] == span and matching[0]["negation"] == negation
            assert original[span["start"]:span["end"]] == span["quote"]
        assert any(clause["span"] == {"start": 0, "end": len(original), "quote": original}
            for clause in provenance["clauses"])
        assert len(saved_options) == 1
        assert saved_options[0][:4] == (option["option_id"], request_id, example["alternative_id"], 1)
        assert json.loads(saved_options[0][4]) == option
        assert saved_links == [(option["option_id"], example["evidence_id"])]
        assert before_evidence == after_evidence and before_alternatives == after_alternatives
        saved_sources = {identity: json.loads(snapshot) for identity, _alternative, snapshot in after_evidence}
        assert {identity: saved_sources[identity] for identity in legacy_evidence} == legacy_evidence
        assert saved_sources[example["evidence_id"]] == source
    finally:
        service.cleanup()
        service.store.engine.dispose()


@pytest.mark.parametrize("country", [None, ""])
def test_missing_or_cleared_country_remains_invalid_without_search_writes(system, country):
    client, path, _ = system
    payload = submission()
    payload["search_location"] = {} if country is None else {"country_code": country}
    response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 422
    assert response.json() == {"outcome": "invalid_input", "persistence": {"state": "not_attempted"},
        "issues": [{"code": "request_fields_invalid"}]}
    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}


@pytest.mark.parametrize("country", ["AN", "CS", "ZZ"])
def test_new_country_nonmembers_are_rejected_before_interpretation_or_save(system, country):
    _, path, service = system

    class NeverInterpret:
        def interpret(self, text):
            raise AssertionError("Invalid country must not reach interpretation")

    payload = submission()
    payload["search_location"]["country_code"] = country
    with TestClient(create_app(replace(service, interpreter=NeverInterpret()))) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 422
    assert response.json() == {"outcome": "invalid_input", "persistence": {"state": "not_attempted"},
        "issues": [{"code": "country_not_in_catalogue"}]}
    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}


@pytest.mark.parametrize("country", ["CH", "XK", "AX", "BQ"])
def test_approved_country_membership_and_reference_version_are_saved_server_side(system, country):
    client, path, _ = system
    payload = submission()
    payload["search_location"]["country_code"] = country
    response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == ("comparison" if country == "CH" else "insufficient_coverage")
    assert body["persistence"]["state"] == "saved"
    with sqlite3.connect(path) as connection:
        original, location, interpretation, projection = connection.execute(
            "SELECT original_text,search_location,interpretation,projection FROM search_request WHERE id = ?",
            (body["persistence"]["request_id"],)).fetchone()
    assert original == payload["text"] and json.loads(location) == payload["search_location"]
    assert json.loads(projection) == body
    assert json.loads(interpretation)["provenance"]["reference_versions"]["country"] == {
        "source": "GeoNames countryInfo", "release": "geonames-countryInfo-2026-10-23-v1",
        "sha256": "8044346fd37ccc6fa1fa99da3068bb69c9bb987bc6ac7a96f04b3618940fe885"}
    expected_options = 2 if country == "CH" else 0
    assert counts(path) == {"search_request": 1, "request_alternative": expected_options,
        "request_alternative_evidence": expected_options}


def test_country_endpoint_exposes_exact_canonical_approved_membership(system):
    from pathlib import Path

    client, _, service = system
    response = client.get("/api/countries")
    assert response.status_code == 200
    catalogue = response.json()
    assert catalogue["version"] == "geonames-countryInfo-2026-10-23-v1"
    assert catalogue["countries"] == json.loads(Path("docs/reference/COUNTRIES-GEONAMES-2026-10-23.json").read_text())
    assert len(catalogue["countries"]) == len({row["code"] for row in catalogue["countries"]}) == 250
    assert {row["code"] for row in service.countries.load().countries} == {row["code"] for row in catalogue["countries"]}
    assert catalogue["attribution"]["source_link"] == "https://download.geonames.org/export/dump/countryInfo.txt"
    assert catalogue["attribution"]["license_link"] == "https://creativecommons.org/licenses/by/4.0/"


@pytest.mark.parametrize("change", ["draft", "unapproved", "wrong_release", "corrupt", "missing", "changed_bytes", "bad_attribution"])
def test_bad_country_reference_is_configuration_failure_not_invalid_input(system, tmp_path, change):
    from hashlib import sha256
    from pathlib import Path
    from app.infrastructure.country_reference import LocalCountryCatalogue

    _, path, service = system
    manifest_path, catalogue_path = tmp_path / "countries-manifest.json", tmp_path / "countries.json"
    manifest = json.loads(Path("docs/reference/COUNTRIES-GEONAMES-2026-10-23-MANIFEST.json").read_text())
    catalogue = Path("docs/reference/COUNTRIES-GEONAMES-2026-10-23.json").read_bytes()
    if change == "draft":
        manifest = json.loads(Path("docs/reference/COUNTRIES-GEONAMES-MANIFEST.json").read_text())
        catalogue = Path("docs/reference/COUNTRIES-GEONAMES-DRAFT.json").read_bytes()
    elif change == "unapproved":
        manifest["approval"]["owner_approved"] = False
    elif change == "wrong_release":
        manifest["release_id"] = "arbitrary-reference"
    elif change == "bad_attribution":
        manifest["attribution"]["credit"] = None
    elif change == "changed_bytes":
        countries = json.loads(catalogue)
        countries[0]["name"] += " changed"
        catalogue = json.dumps(countries).encode()
        manifest["normalized_output"]["sha256"] = sha256(catalogue).hexdigest()
    catalogue_path.write_bytes(catalogue)
    if change != "missing":
        manifest_path.write_text("invalid JSON" if change == "corrupt" else json.dumps(manifest))
    altered = replace(service, countries=LocalCountryCatalogue(manifest_path, catalogue_path))
    with TestClient(create_app(altered)) as client:
        reference = client.get("/api/countries")
        response = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64})
    for result in (reference, response):
        assert result.status_code == 503
        assert result.json() == {"outcome": "configuration_unavailable", "persistence": {"state": "not_attempted"},
            "issues": [{"code": "country_reference_unavailable"}]}
    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}


def test_checked_recovery_precedes_country_reference_availability_and_membership(system):
    _, path, service = system
    payload = submission()
    with TestClient(create_app(service)) as client:
        original = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64}).json()
    before = counts(path)

    class UnavailableReference:
        calls = 0

        def load(self):
            self.calls += 1
            raise AssertionError("Committed recovery must not load or validate current countries")

    unavailable = UnavailableReference()
    with TestClient(create_app(replace(service, countries=unavailable))) as client:
        recovered = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
        edited = {**payload, "search_location": {"country_code": "AN"}}
        conflict = client.post("/api/comparisons", json=edited, headers={"X-Submission-Proof": "a" * 64})
        denied = client.post("/api/comparisons", json=edited, headers={"X-Submission-Proof": "b" * 64})
    assert recovered.status_code == 200
    assert recovered.json() == {"outcome": "submission_recovered", "persistence": original["persistence"],
        "saved_outcome": original["outcome"], "assessed_at": original["assessed_at"]}
    assert "comparison" not in recovered.json()
    assert conflict.status_code == 409 and conflict.json()["outcome"] == "submission_key_conflict"
    assert denied.status_code == 403 and denied.json()["outcome"] == "recovery_not_authorized"
    assert unavailable.calls == 0 and counts(path) == before
    with sqlite3.connect(path) as connection:
        saved = json.loads(connection.execute("SELECT projection FROM search_request WHERE id = ?",
            (original["persistence"]["request_id"],)).fetchone()[0])
    assert saved == original


def confirmed_scope():
    return {"country_code": "CH", "town": "  Synthetic optional town  ", "postcode": " 0123 ",
        "locality": {"confirmation": "user_confirmed", "verification": "reference_unverified",
            "normalized": {"town": "synthetic optional town", "postcode": "0123"}}}


def test_explicit_locality_confirmation_retains_minimal_unverified_intent_and_saves_coverage(system):
    from app.application.comparisons import digest

    client, path, _ = system
    baseline = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64}).json()
    with sqlite3.connect(path) as connection:
        evidence = connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall()
        options = connection.execute("SELECT * FROM request_alternative ORDER BY id").fetchall()
        links = connection.execute("SELECT * FROM request_alternative_evidence ORDER BY option_id").fetchall()
    payload = submission()
    payload["search_location"].update(town=confirmed_scope()["town"], postcode=confirmed_scope()["postcode"],
        reference={"source": "do-not-retain-reference", "id": "unverified-id", "release": "unverified-version"})
    payload["language_context"] = {"browser_language": "en", "preferred_language": "en"}
    first = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64})
    assert first.status_code == 200 and first.json()["outcome"] == "clarification_required"
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
    payload = {**payload, "submission_key": str(uuid4()), "location_choice": "confirmed_unverified"}
    response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "c" * 64})
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "insufficient_coverage" and body["persistence"]["state"] == "saved"
    assert body["search_scope"] == confirmed_scope()
    assert "geographic_applicability_unverified" in body["coverage"]["limitation_codes"]
    assert "comparison" not in body
    assert counts(path) == {"search_request": 2, "request_alternative": 2, "request_alternative_evidence": 2}
    with sqlite3.connect(path) as connection:
        original, location, choice, context, interpretation, binding, projection = connection.execute(
            "SELECT original_text,search_location,location_choice,language_context,interpretation,payload_digest,projection FROM search_request WHERE id=?",
            (body["persistence"]["request_id"],)).fetchone()
        assert json.loads(location) == confirmed_scope() and choice == "confirmed_unverified"
        assert original == EXAMPLE and json.loads(context) == payload["language_context"]
        assert binding == digest({key: value for key, value in payload.items() if key != "submission_key"})
        assert json.loads(projection) == body
        meaning = json.loads(interpretation)
        assert meaning["constraints"] == [{"value": "no_replacement", "quote": "without replacing it"}]
        constraint = next(item for item in meaning["provenance"]["items"] if item["kind"] == "constraint")
        assert constraint["span"] == {"start": 18, "end": 38, "quote": "without replacing it"}
        assert meaning["provenance"]["reference_versions"]["country"]["release"] == "geonames-countryInfo-2026-10-23-v1"
        assert "do-not-retain-reference" not in location + interpretation + projection
        assert connection.execute("SELECT * FROM evidence ORDER BY version_id").fetchall() == evidence
        assert connection.execute("SELECT * FROM request_alternative ORDER BY id").fetchall() == options
        assert connection.execute("SELECT * FROM request_alternative_evidence ORDER BY option_id").fetchall() == links
        assert json.loads(connection.execute("SELECT projection FROM search_request WHERE id=?",
            (baseline["persistence"]["request_id"],)).fetchone()[0]) == baseline


@pytest.mark.parametrize("independent_constraint", [False, True])
def test_source_backed_countrywide_fixture_uses_real_O1_qualification_and_preserves_requirements(system, independent_constraint):
    from tests.support.locality_confirmation import candidate
    from tests.support.synthetic import represented_locality

    _, path, service = system
    prepared = candidate()
    service.store.seed_test_knowledge((prepared,))

    class Knowledge:
        def retrieve(self, interpretation, command):
            assert command.search_location == confirmed_scope()
            return (prepared,)

    class Interpreter:
        def interpret(self, text):
            return represented_locality()

    configured = replace(service, knowledge=Knowledge())
    payload = submission()
    payload["location_choice"] = "confirmed_unverified"
    payload["search_location"] = {key: value for key, value in confirmed_scope().items() if key != "locality"}
    if independent_constraint:
        configured = replace(configured, interpreter=Interpreter())
        payload["text"] = represented_locality().original_text
    with TestClient(create_app(configured)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201
    body = response.json()
    assert body["search_scope"] == confirmed_scope()
    if independent_constraint:
        assert body["outcome"] == "insufficient_coverage" and "comparison" not in body
        expected = 0
    else:
        assert body["outcome"] == "comparison"
        option, = body["comparison"]["options"]
        assert option["alternative_id"] == "00000000-0000-4000-8000-000000000540"
        assert option["evidence"][0]["version_id"] == "30000000-0000-4000-8000-000000000540"
        assert option["geographic_scope"] == {"country_code": "CH", "country_wide": True}
        assert option["financial"]["amount"] == "45.00" and option["financial"]["unit"] == "repair"
        assert option["environmental"]["status"] == "unknown"
        assert all(label["requirement"] == "satisfied" for label in option["claims"] if label["claim"] != "financial")
        expected = 1
    assert counts(path) == {"search_request": 1, "request_alternative": expected, "request_alternative_evidence": expected}
    with sqlite3.connect(path) as connection:
        meaning, projection = connection.execute("SELECT interpretation,projection FROM search_request").fetchone()
        assert json.loads(projection) == body
        if independent_constraint:
            assert json.loads(meaning)["constraints"] == [{"value": "locality:Genève", "quote": "in Genève"}]


def test_confirmed_locality_edits_need_fresh_choice_and_checked_recovery_skips_new_policy(system):
    _, path, service = system
    payload = submission()
    payload["location_choice"] = "confirmed_unverified"
    payload["search_location"] = {key: value for key, value in confirmed_scope().items() if key != "locality"}
    with TestClient(create_app(service)) as client:
        initial = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
        assert initial.status_code == 201
        saved = initial.json()
        changed = {**payload, "search_location": {**payload["search_location"], "town": "Changed intended town"}}
        assert client.post("/api/comparisons", json=changed, headers={"X-Submission-Proof": "a" * 64}).status_code == 409
        fresh = {**changed, "submission_key": str(uuid4()), "location_choice": "provided"}
        clarification = client.post("/api/comparisons", json=fresh, headers={"X-Submission-Proof": "b" * 64})
        assert clarification.status_code == 200 and clarification.json()["outcome"] == "clarification_required"
        invalid_country = {**payload, "submission_key": str(uuid4()), "search_location": {**payload["search_location"], "country_code": "AN"}}
        assert client.post("/api/comparisons", json=invalid_country, headers={"X-Submission-Proof": "b" * 64}).status_code == 422
    before = counts(path)

    class NeverProcess:
        def load(self):
            raise AssertionError("Acknowledgement cannot consult current reference")

        def interpret(self, text):
            raise AssertionError("Acknowledgement cannot reinterpret current locality")

    with TestClient(create_app(replace(service, countries=NeverProcess(), interpreter=NeverProcess()))) as client:
        recovered = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert recovered.status_code == 200 and recovered.json() == {"outcome": "submission_recovered",
        "persistence": saved["persistence"], "saved_outcome": saved["outcome"], "assessed_at": saved["assessed_at"]}
    assert counts(path) == before


def locality_matching_service(system):
    from app.infrastructure.locality_reference import LocalLocalityCatalogue
    _, path, service = system
    return path, replace(service, localities=LocalLocalityCatalogue())


def association_pointer(record):
    return {"source": "swisstopo", "release": "swisstopo-chli-associations-2026-10-01-v1", "source_record": record}


@pytest.mark.parametrize("country,town,postcode,record", [
    ("CH", "  jouxtens-me\u0301zery  ", " 1008 ", 10),
    ("LI", "Vaduz", "9490", 5590),
    ("LI", None, "9490", 5590),
])
def test_exact_locality_association_saves_honest_scope_and_bound_payload(system, country, town, postcode, record):
    from app.application.comparisons import digest
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"] = {"country_code": country, "postcode": postcode}
    if town is not None:
        payload["search_location"]["town"] = town
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "insufficient_coverage"
    scope = body["search_scope"]
    assert {key: value for key, value in scope.items() if key != "locality"} == payload["search_location"]
    assert scope["locality"]["verification"] == "matched_in_reference"
    assert scope["locality"]["selection"] == "single_match"
    assert scope["locality"]["association"]["reference"] == association_pointer(record)
    assert counts(path) == {"search_request": 1, "request_alternative": 0, "request_alternative_evidence": 0}
    with sqlite3.connect(path) as connection:
        location, meaning, binding, projection = connection.execute(
            "SELECT search_location,interpretation,payload_digest,projection FROM search_request").fetchone()
    assert json.loads(location) == scope and json.loads(projection) == body
    assert binding == digest({key: value for key, value in payload.items() if key != "submission_key"})
    interpreted = json.loads(meaning)
    assert interpreted["constraints"] == [{"value": "no_replacement", "quote": "without replacing it"}]
    constraint = next(item for item in interpreted["provenance"]["items"] if item["kind"] == "constraint")
    assert constraint["span"] == {"start": 18, "end": 38, "quote": "without replacing it"}
    reference = interpreted["provenance"]["reference_versions"]
    assert reference["country"]["release"] == "geonames-countryInfo-2026-10-23-v1"
    assert reference["locality"] == {"source": "swisstopo", "release": association_pointer(record)["release"],
        "sha256": "eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9",
        "snapshot_at": "2026-10-01T00:00:00Z"}
    assert '"associations":' not in location + meaning + projection


def test_multiple_reference_associations_stay_unsaved_until_checked_selection(system):
    path, service = locality_matching_service(system)
    with TestClient(create_app(service)) as client:
        baseline = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64}).json()
        with sqlite3.connect(path) as connection:
            prior = {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall()
                for table in ("request_alternative", "request_alternative_evidence", "evidence")}
        payload = submission()
        payload["search_location"].update(town="Lausanne", postcode="1015")
        unresolved = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64})
        assert unresolved.status_code == 200
        assert unresolved.json()["outcome"] == "clarification_required"
        assert unresolved.json()["issues"] == [{"code": "locality_reference_ambiguous"}]
        choices = unresolved.json()["clarification"]["associations"]
        assert [item["reference"]["source_record"] for item in choices] == [15, 16, 17]
        assert {item["source_postcode_id"] for item in choices} == {"163"}
        assert len({item["administrative"]["municipality_id"] for item in choices}) == 3
        assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
        selected = {**payload, "submission_key": str(uuid4()), "search_location": {
            **payload["search_location"], "reference": choices[1]["reference"]}}
        response = client.post("/api/comparisons", json=selected, headers={"X-Submission-Proof": "c" * 64})
    assert response.status_code == 201 and response.json()["outcome"] == "insufficient_coverage"
    body = response.json()
    assert body["search_scope"]["locality"]["selection"] == "explicit"
    assert body["search_scope"]["locality"]["association"] == choices[1]
    assert counts(path) == {"search_request": 2, "request_alternative": 2, "request_alternative_evidence": 2}
    with sqlite3.connect(path) as connection:
        assert json.loads(connection.execute("SELECT projection FROM search_request WHERE id=?",
            (baseline["persistence"]["request_id"],)).fetchone()[0]) == baseline
        assert {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall() for table in prior} == prior


@pytest.mark.parametrize("case", ["stale", "fabricated", "wrong_fields", "foreign_country", "edited_label"])
def test_selected_association_is_checked_against_release_country_and_all_fields(system, case):
    path, service = locality_matching_service(system)
    payload = submission()
    pointer = association_pointer(10)
    payload["search_location"].update(town="Jouxtens-Mézery", postcode="1008", reference=pointer)
    if case == "stale": pointer["release"] = "older-unapproved-release"
    if case == "fabricated": pointer["source_record"] = 999999
    if case == "wrong_fields": payload["search_location"]["postcode"] = "1015"
    if case == "foreign_country": payload["search_location"]["country_code"] = "LI"
    if case == "edited_label": pointer["locality_name"] = "Client-edited label"
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == (422 if case == "foreign_country" else 200)
    assert response.json()["outcome"] == ("invalid_input" if case == "foreign_country" else "clarification_required")
    assert response.json()["issues"] == [{"code": "locality_country_mismatch" if case == "foreign_country" else "locality_selection_inconsistent"}]
    assert response.json()["persistence"] == {"state": "not_attempted"}
    assert counts(path) == {"search_request": 0, "request_alternative": 0, "request_alternative_evidence": 0}


@pytest.mark.parametrize("country,town,postcode", [("CH", "Lausanne", "9490"), ("DE", "Vaduz", "9490")])
def test_missing_or_out_of_scope_associations_are_unknown_not_invalid(system, country, town, postcode):
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"] = {"country_code": country, "town": town, "postcode": postcode}
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    body = response.json()
    assert response.status_code == 200 and body["outcome"] == "clarification_required"
    assert body["issues"] == [{"code": "locality_reference_unknown"}]
    assert "not proof" in body["clarification"]["message"]
    assert body["clarification"]["associations"] == []
    assert counts(path)["search_request"] == 0


@pytest.mark.parametrize("mode,status,outcome", [("unusable", 503, "configuration_unavailable"), ("processing", 500, "processing_error")])
def test_broken_locality_loading_cannot_masquerade_as_missing_match(system, mode, status, outcome):
    from app.application.localities import LocalityReferenceUnavailable
    path, service = locality_matching_service(system)

    class BrokenReference:
        def load(self):
            raise LocalityReferenceUnavailable if mode == "unusable" else RuntimeError("test-only lookup failure")

    payload = submission()
    payload["search_location"].update(town="Jouxtens-Mézery", postcode="1008")
    with TestClient(create_app(replace(service, localities=BrokenReference()))) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == status and response.json()["outcome"] == outcome
    assert response.json()["persistence"] == {"state": "not_attempted"}
    assert counts(path)["search_request"] == 0


def test_matched_association_recovery_precedes_references_and_keeps_payload_binding(system):
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"].update(town="Lausanne", postcode="1015", reference=association_pointer(16))
    headers = {"X-Submission-Proof": "a" * 64}
    with TestClient(create_app(service)) as client:
        saved = client.post("/api/comparisons", json=payload, headers=headers).json()
    before = counts(path)

    class NeverProcess:
        def load(self): raise AssertionError("Committed acknowledgement precedes current reference")
        def interpret(self, text): raise AssertionError("Committed acknowledgement precedes reinterpretation")

    with TestClient(create_app(replace(service, countries=NeverProcess(), localities=NeverProcess(), interpreter=NeverProcess()))) as client:
        recovered = client.post("/api/comparisons", json=payload, headers=headers)
        changed = {**payload, "search_location": {**payload["search_location"], "reference": association_pointer(15)}}
        conflict = client.post("/api/comparisons", json=changed, headers=headers)
    assert recovered.status_code == 200 and recovered.json() == {"outcome": "submission_recovered",
        "persistence": saved["persistence"], "saved_outcome": saved["outcome"], "assessed_at": saved["assessed_at"]}
    assert conflict.status_code == 409
    assert counts(path) == before


@pytest.mark.parametrize("independent_constraint", [False, True])
def test_matched_reference_does_not_replace_independent_applicability_evidence(system, independent_constraint):
    from tests.support.locality_confirmation import candidate
    from tests.support.synthetic import represented_locality
    path, service = locality_matching_service(system)
    prepared = candidate()
    service.store.seed_test_knowledge((prepared,))

    class Knowledge:
        def retrieve(self, interpretation, command): return (prepared,)

    class Interpreter:
        def interpret(self, text): return represented_locality()

    payload = submission()
    payload["search_location"].update(town="Jouxtens-Mézery", postcode="1008")
    service = replace(service, knowledge=Knowledge())
    if independent_constraint:
        payload["text"] = represented_locality().original_text
        service = replace(service, interpreter=Interpreter())
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    body = response.json()
    assert response.status_code == 201 and body["outcome"] == ("insufficient_coverage" if independent_constraint else "comparison")
    assert counts(path) == {"search_request": 1, "request_alternative": int(not independent_constraint), "request_alternative_evidence": int(not independent_constraint)}
    with sqlite3.connect(path) as connection:
        meaning = json.loads(connection.execute("SELECT interpretation FROM search_request").fetchone()[0])
    if independent_constraint:
        assert meaning["constraints"] == [{"value": "locality:Genève", "quote": "in Genève"}]


@pytest.mark.parametrize("country,postcode,choice", [
    ("CH", "10A8", "provided"), ("LI", "949", "confirmed_unverified"),
    ("CH", "10080", "confirmed_unverified"),
])
def test_declared_postcode_format_rejects_malformed_retained_input_without_writes(system, country, postcode, choice):
    path, service = locality_matching_service(system)
    with TestClient(create_app(service)) as client:
        baseline = client.post("/api/comparisons", json=submission(), headers={"X-Submission-Proof": "a" * 64}).json()
        with sqlite3.connect(path) as connection:
            before = {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall()
                for table in ("request_alternative", "request_alternative_evidence", "evidence")}
        payload = submission()
        payload["search_location"].update(country_code=country, town="Jouxtens-Mézery", postcode=postcode)
        payload["location_choice"] = choice
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "b" * 64})
    body = response.json()
    assert response.status_code == 422 and body["outcome"] == "invalid_input"
    assert body["persistence"] == {"state": "not_attempted"}
    assert body["issues"] == [{"code": "postcode_format_invalid"}]
    assert "four-digit postcode" in body["clarification"]["message"]
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}
    with sqlite3.connect(path) as connection:
        assert json.loads(connection.execute("SELECT projection FROM search_request").fetchone()[0]) == baseline
        assert {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall() for table in before} == before


def test_declared_postcode_format_keeps_well_formed_unmatched_input_unknown_and_confirmable(system):
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"].update(town="Synthetic optional town", postcode=" 0123 ")
    with TestClient(create_app(service)) as client:
        unknown = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
        assert unknown.status_code == 200 and unknown.json()["outcome"] == "clarification_required"
        assert unknown.json()["issues"] == [{"code": "locality_reference_unknown"}]
        assert "not proof" in unknown.json()["clarification"]["message"]
        assert counts(path)["search_request"] == 0
        confirmed = {**payload, "submission_key": str(uuid4()), "location_choice": "confirmed_unverified"}
        response = client.post("/api/comparisons", json=confirmed, headers={"X-Submission-Proof": "b" * 64})
    assert response.status_code == 201 and response.json()["outcome"] == "insufficient_coverage"
    scope = response.json()["search_scope"]
    assert scope["postcode"] == " 0123 " and scope["locality"]["normalized"]["postcode"] == "0123"
    assert scope["locality"]["verification"] == "reference_unverified"
    assert counts(path) == {"search_request": 1, "request_alternative": 0, "request_alternative_evidence": 0}


def test_declared_postcode_format_does_not_validate_discarded_country_only_input(system):
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"].update(town="Synthetic optional town", postcode="10A8")
    payload["location_choice"] = "country_only"
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    assert response.status_code == 201 and response.json()["outcome"] == "comparison"
    with sqlite3.connect(path) as connection:
        location, interpretation = connection.execute("SELECT search_location,interpretation FROM search_request").fetchone()
    assert json.loads(location) == {"country_code": "CH"}
    assert json.loads(interpretation)["constraints"] == [{"value": "no_replacement", "quote": "without replacing it"}]
    assert counts(path) == {"search_request": 1, "request_alternative": 2, "request_alternative_evidence": 2}


@pytest.mark.parametrize("choice", ["provided", "confirmed_unverified"])
def test_declared_postcode_format_does_not_apply_CH_LI_rule_to_other_countries(system, choice):
    path, service = locality_matching_service(system)
    payload = submission()
    payload["search_location"].update(country_code="DE", town="Synthetic optional town", postcode="unreviewed-format")
    payload["location_choice"] = choice
    with TestClient(create_app(service)) as client:
        response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": "a" * 64})
    if choice == "provided":
        assert response.status_code == 200 and response.json()["outcome"] == "clarification_required"
        assert response.json()["issues"] == [{"code": "locality_reference_unknown"}]
        assert counts(path)["search_request"] == 0
    else:
        assert response.status_code == 201 and response.json()["outcome"] == "insufficient_coverage"
        scope = response.json()["search_scope"]
        assert scope["postcode"] == "unreviewed-format"
        assert scope["locality"]["verification"] == "reference_unverified"
