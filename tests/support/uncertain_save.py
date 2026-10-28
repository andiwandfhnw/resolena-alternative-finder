from contextlib import ExitStack
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from app.application.comparisons import PersistenceFailure, digest
from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from tests.support.synthetic import EXAMPLE


def _observe(database: Path):
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT id, projection FROM search_request ORDER BY rowid").fetchall()
        return {
            "rows": [{"id": identity, "projection": json.loads(projection)} for identity, projection in rows],
            "counts": {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("search_request", "request_alternative", "request_alternative_evidence")},
            "snapshots": {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                for table in ("request_alternative", "request_alternative_evidence", "evidence")},
        }


def install_uncertain_save_fault(store: SQLiteComparisonStore, database: Path, control_file: Path):
    real_save = store.save

    def save(prepared):
        try:
            control = json.loads(control_file.read_text())
        except FileNotFoundError:
            return real_save(prepared)
        if control.get("submission_key_digest") != prepared.key_digest:
            return real_save(prepared)
        control_file.unlink()
        absent = control.get("mode") == "absent"
        dialect = store.engine.dialect
        real_commit, real_execute = dialect.do_commit, dialect.do_execute
        real_find, real_rollback = store.find, dialect.do_rollback
        faults = {"real_commits": 0, "confirmation_losses": 0, "read_failures": 0}
        timeline = ["matching_control_consumed"]
        observer_after_commit = None
        commit_unconfirmed = False
        reconciliation_results = []
        real_reconciliation_selects = 0
        normal_driver_rollback_observed = False

        def lose_confirmation(connection):
            nonlocal observer_after_commit, commit_unconfirmed
            if absent:
                timeline.append("test_fault_before_underlying_dbapi_commit")
            else:
                real_commit(connection)
                faults["real_commits"] += 1
                timeline.append("real_sqlite_commit_returned_to_test_shim")
                observer_after_commit = _observe(database)
                timeline.append("independent_observer_sees_committed_rows_test_only")
            commit_unconfirmed = True
            faults["confirmation_losses"] += 1
            timeline.append("confirmation_error_before_return_to_production")
            raise sqlite3.OperationalError("Synthetic commit confirmation unavailable")

        def unavailable_readback(cursor, statement, parameters, context=None):
            nonlocal real_reconciliation_selects
            reconciliation_select = commit_unconfirmed and statement.lstrip().lower().startswith("select search_request.")
            if not absent and reconciliation_select and faults["read_failures"] == 0:
                faults["read_failures"] += 1
                timeline.append("production_reconciliation_select_unavailable")
                raise sqlite3.OperationalError("Synthetic committed readback unavailable")
            result = real_execute(cursor, statement, parameters, context)
            if absent and reconciliation_select:
                real_reconciliation_selects += 1
                timeline.append("real_reconciliation_select_returned")
            return result

        def observe_find(key):
            result = real_find(key)
            if commit_unconfirmed:
                reconciliation_results.append(result is not None)
                timeline.append("real_reconciliation_found" if result is not None else "real_reconciliation_absent")
            return result

        def observe_rollback(connection):
            nonlocal normal_driver_rollback_observed
            if commit_unconfirmed and connection.in_transaction:
                normal_driver_rollback_observed = True
                timeline.append("normal_driver_rollback_entered_with_transaction")
            return real_rollback(connection)

        try:
            with patch.object(dialect, "do_commit", lose_confirmation), patch.object(dialect, "do_execute", unavailable_readback), ExitStack() as observers:
                if absent:
                    observers.enter_context(patch.object(store, "find", observe_find))
                    observers.enter_context(patch.object(dialect, "do_rollback", observe_rollback))
                return real_save(prepared)
        finally:
            restored = dialect.do_commit == real_commit and dialect.do_execute == real_execute
            timeline.append("dialect_methods_restored")
            evidence = {
                "fault_counts": faults, "timeline": timeline,
                "independent_after_commit": observer_after_commit, "after_fault": _observe(database),
                "dialect_methods_restored": restored, "observer_rows_supplied_to_application": False,
                "raw_originating_proofs_recorded": False,
            }
            if absent:
                evidence.update(mode="absent", real_reconciliation_selects=real_reconciliation_selects,
                    reconciliation_results=reconciliation_results,
                    normal_driver_rollback_observed=normal_driver_rollback_observed)
            control_file.with_suffix(".evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    store.save = save

    def cleanup():
        if store.save is save:
            store.save = real_save
        control_file.unlink(missing_ok=True)

    return cleanup


class AbsentRecoveryComparison:
    def __init__(self, comparisons, control_file: Path, fallback=None):
        self.store = comparisons.store
        self._comparisons = comparisons
        self._fallback = fallback or comparisons
        self._control_file = control_file
        self._target_digest = None
        self._attempts = []
        self._enabled = True
        self._adapters = {name: getattr(comparisons, name)
            for name in ("interpreter", "knowledge", "renderer", "store", "clock")}

    def execute(self, submission):
        service = self._comparisons
        key_digest = digest(submission.key)
        if not self._enabled:
            return self._fallback.execute(submission)
        if self._target_digest is None:
            try:
                control = json.loads(self._control_file.read_text())
            except FileNotFoundError:
                return self._fallback.execute(submission)
            if (control.get("mode") != "absent" or control.get("submission_key_digest") != key_digest
                    or submission.text != EXAMPLE or submission.search_location != {"country_code": "CH"}):
                return self._fallback.execute(submission)
            self._target_digest = key_digest
        if key_digest != self._target_digest:
            return self._fallback.execute(submission)

        counts = dict.fromkeys(("interpret", "retrieve", "assess_clock", "prepare", "prepare_coverage", "save", "underlying_commits"), 0)
        attempt = {"counts": counts, "prepared": None, "returned_outcome": None,
            "raised_persistence_state": None, "lookup_results": [], "retrieved_count": 0,
            "qualified_rendered_count": 0, "coverage_limitation_codes": [], "real_request_selects": 0,
            "insert_attempts": dict.fromkeys(("search_request", "request_alternative", "request_alternative_evidence"), 0)}
        dialect = self.store.engine.dialect
        real_commit, real_execute = dialect.do_commit, dialect.do_execute

        def call(name, operation, *args):
            counts[name] += 1
            return operation(*args)

        def find(key):
            before = attempt["real_request_selects"]
            result = service.store.find(key)
            attempt["lookup_results"].append({"scope": "application_initial", "found": result is not None,
                "real_selects": attempt["real_request_selects"] - before})
            return result

        def retrieve(*args):
            result = call("retrieve", service.knowledge.retrieve, *args)
            attempt["retrieved_count"] = len(result)
            return result

        def prepare(interpretation, selected):
            attempt["qualified_rendered_count"] = len(selected)
            return call("prepare", service.renderer.prepare, interpretation, selected)

        def coverage(interpretation, limitations):
            attempt["coverage_limitation_codes"] = list(limitations)
            return call("prepare_coverage", service.renderer.prepare_coverage, interpretation, limitations)

        def save(prepared):
            body = prepared.projection
            attempt["prepared"] = {"request_id": body["persistence"]["request_id"],
                "option_ids": [option["option_id"] for option in body.get("comparison", {}).get("options", [])],
                "outcome": body["outcome"], "assessed_at": body["assessed_at"]}
            return call("save", service.store.save, prepared)

        def commit(connection):
            result = real_commit(connection)
            counts["underlying_commits"] += 1
            return result

        def execute(cursor, statement, parameters, context=None):
            normalized = statement.lstrip().lower()
            if normalized.startswith("select search_request."):
                attempt["real_request_selects"] += 1
            for table in attempt["insert_attempts"]:
                if normalized.startswith(f"insert into {table} "):
                    attempt["insert_attempts"][table] += 1
            return real_execute(cursor, statement, parameters, context)

        controlled = replace(service,
            interpreter=SimpleNamespace(interpret=lambda text: call("interpret", service.interpreter.interpret, text)),
            knowledge=SimpleNamespace(retrieve=retrieve),
            renderer=SimpleNamespace(prepare=prepare, prepare_coverage=coverage),
            store=SimpleNamespace(find=find, save=save), clock=lambda: call("assess_clock", service.clock))
        try:
            with patch.object(dialect, "do_commit", commit), patch.object(dialect, "do_execute", execute):
                result = controlled.execute(submission)
            attempt["returned_outcome"] = result["outcome"]
            return result
        except PersistenceFailure as error:
            attempt["raised_persistence_state"] = error.state
            raise
        finally:
            self._attempts.append(attempt)
            evidence = {"attempts": self._attempts,
                "total_counts": {name: sum(item["counts"][name] for item in self._attempts) for name in counts},
                "original_adapters_unchanged": all(getattr(service, name) is adapter for name, adapter in self._adapters.items()),
                "raw_originating_proofs_or_requests_recorded": False}
            destination = self._control_file.with_suffix(".processing.json")
            temporary = destination.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(evidence, indent=2) + "\n")
            temporary.replace(destination)

    def cleanup(self):
        self._enabled = False
        self._target_digest = None
        self._control_file.unlink(missing_ok=True)
