import json
from pathlib import Path
from threading import get_ident
from time import monotonic, sleep
from unittest.mock import patch

from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from tests.support.uncertain_save import _observe


def _write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def install_delayed_save_gate(store: SQLiteComparisonStore, database: Path, control_file: Path, *, timeout=20):
    real_save = store.save
    release_file = control_file.with_suffix(".release.json")
    active_key = None
    save_calls = 0

    def cleanup():
        if active_key is not None:
            _write(release_file, {"submission_key_digest": active_key})
        if store.save is save:
            store.save = real_save

    def save(prepared):
        nonlocal active_key, save_calls
        try:
            control = json.loads(control_file.read_text())
        except FileNotFoundError:
            return real_save(prepared)
        if control.get("submission_key_digest") != prepared.key_digest:
            return real_save(prepared)
        control_file.unlink()
        active_key = prepared.key_digest
        save_calls += 1
        dialect = store.engine.dialect
        real_commit = dialect.do_commit
        owner_thread = get_ident()
        request_id = prepared.projection["persistence"]["request_id"]
        evidence = {"request_id": request_id, "save_calls": save_calls, "underlying_commit_calls": 0,
            "release_received": False, "independent_before": _observe(database),
            "observer_rows_supplied_to_application": False,
            "timeline": ["matching_control_consumed"]}

        def pause_before_commit(connection):
            if get_ident() != owner_thread:
                return real_commit(connection)
            cursor = connection.cursor()
            try:
                request_count = cursor.execute("SELECT count(*) FROM search_request WHERE id = ?", (request_id,)).fetchone()[0]
                if not request_count:
                    return real_commit(connection)
                transaction_rows = {"search_request": request_count,
                    "request_alternative": cursor.execute("SELECT count(*) FROM request_alternative WHERE request_id = ?", (request_id,)).fetchone()[0],
                    "request_alternative_evidence": cursor.execute("""SELECT count(*) FROM request_alternative_evidence link
                        JOIN request_alternative option ON option.id = link.option_id WHERE option.request_id = ?""", (request_id,)).fetchone()[0]}
            finally:
                cursor.close()
            if not connection.in_transaction:
                raise AssertionError("The designated SQLite save must still be uncommitted")
            evidence.update(stage="after_required_inserts_before_underlying_commit", transaction_active=True,
                transaction_rows=transaction_rows, independent_while_paused=_observe(database))
            evidence["timeline"].append("required_inserts_visible_in_active_writer_transaction")
            evidence["timeline"].append("pre_commit_reached_signal_published")
            _write(control_file.with_suffix(".reached.json"), evidence)
            deadline = monotonic() + timeout
            while True:
                try:
                    release = json.loads(release_file.read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    release = {}
                if release.get("submission_key_digest") == prepared.key_digest:
                    break
                if monotonic() >= deadline:
                    raise RuntimeError("The test-only save gate was not released within its bound")
                sleep(0.01)
            evidence["release_received"] = True
            evidence["timeline"].append("explicit_release_received")
            evidence["underlying_commit_calls"] += 1
            result = real_commit(connection)
            evidence["timeline"].append("underlying_commit_returned")
            return result

        try:
            with patch.object(dialect, "do_commit", pause_before_commit):
                return real_save(prepared)
        finally:
            active_key = None
            cleanup()
            evidence.update(dialect_method_restored=dialect.do_commit == real_commit,
                store_save_hook_restored=store.save == real_save, independent_after=_observe(database))
            evidence["timeline"].extend(["dialect_method_restored", "store_save_hook_restored"])
            _write(control_file.with_suffix(".evidence.json"), evidence)

    store.save = save
    return cleanup
