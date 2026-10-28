import json
import sqlite3
from dataclasses import replace
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
