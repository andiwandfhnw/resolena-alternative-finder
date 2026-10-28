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


def test_concurrent_same_submission_commits_one_winner_and_acknowledges_loser(tmp_path, monkeypatch):
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
    before = counts(path)
    with sqlite3.connect(path) as connection:
        evidence_before = connection.execute("SELECT version_id, snapshot FROM evidence ORDER BY version_id").fetchall()

    def execute(role):
        service = replace(base, store=CoordinatedStore(role))
        with TestClient(create_app(service)) as client:
            response = client.post("/api/comparisons", json=payload, headers={"X-Submission-Proof": proof})
            return {"status": response.status_code, "body": response.json()}

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {role: executor.submit(execute, role) for role in stores}
            responses = {role: future.result(timeout=15) for role, future in futures.items()}

        assert missed == {"winner": True, "loser": True}
        assert calls == {"winner": {"find": 1, "save": 1}, "loser": {"find": 2, "save": 1}}
        assert bindings["winner"] == bindings["loser"]
        assert connections["winner"] and connections["loser"]
        assert connections["winner"].isdisjoint(connections["loser"])
        assert collisions == [{"sqlite_errorname": "SQLITE_CONSTRAINT_UNIQUE", "unique_submission_key": True}]
        assert rollbacks == [True]
        assert proof_payload_checks == [True, True]
        committed_index = timeline.index("winner:committed")
        for role in stores:
            assert timeline.index(f"{role}:initial_lookup_missed") < timeline.index(f"{role}:prepared") < committed_index
        branch = ["winner:committed", "loser:unique_insert_rejected", "loser:rollback",
            "loser:duplicate_submission", "loser:committed_lookup", "loser:ownership_check", "loser:payload_check"]
        assert [timeline.index(item) for item in branch] == sorted(timeline.index(item) for item in branch)

        winner, loser = responses["winner"], responses["loser"]
        assert winner["status"] == 201
        assert winner["body"] == prepared["winner"]
        assert winner["body"]["outcome"] == "comparison"
        assert winner["body"]["assessed_at"] == FIXTURE_TIME.isoformat()
        assert loser == {"status": 200, "body": {
            "outcome": "submission_recovered", "persistence": winner["body"]["persistence"],
            "saved_outcome": "comparison", "assessed_at": FIXTURE_TIME.isoformat(),
        }}
        winner_id = winner["body"]["persistence"]["request_id"]
        loser_id = prepared["loser"]["persistence"]["request_id"]
        assert winner_id != loser_id
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
        assert [(identity, key_digest, json.loads(projection)) for identity, key_digest, projection in rows] == [
            (winner_id, digest(payload["submission_key"]), winner["body"])]
        for (option_id, request_id, snapshot), option in zip(saved_options, winner_options, strict=True):
            assert (option_id, request_id, json.loads(snapshot)) == (option["option_id"], winner_id, option)
        assert associations == sorted((option["option_id"], source["version_id"])
            for option in winner_options for source in option["evidence"])
        assert evidence_after == evidence_before
        artifact = {"both_initial_lookups_missed": missed, "timeline": timeline,
            "requests": 2, "store_port_calls": calls,
            "separate_connection_counts": {role: len(values) for role, values in connections.items()},
            "execution_connections_disjoint": True, "same_input_bindings": True,
            "sqlite_collisions": collisions, "collision_rollback_count": len(rollbacks),
            "acknowledgement_ownership_payload_checks": proof_payload_checks,
            "winner": winner, "loser": loser, "before_counts": before, "after_counts": after,
            "discarded_loser_request_id": loser_id,
            "discarded_loser_option_ids": [option["option_id"] for option in loser_options],
            "committed_evidence_associations": associations, "evidence_unchanged": True,
            "source_evidence_sha256": digest(evidence_after), "raw_originating_proofs_recorded": False}
        (tmp_path / "concurrent-save-evidence.json").write_text(json.dumps(artifact, indent=2) + "\n")
    finally:
        for store in stores.values():
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
