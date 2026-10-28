"""One owner-executed Windows dependency check; no model or live assessment."""

import argparse
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys
import traceback
from unittest.mock import patch
from uuid import UUID, uuid4


WORKTREE = Path(r"C:\Users\AndiWand\Downloads\granite-handoff-2026-10-25")
PYTHON = Path(r"C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe")
TABLES = ("search_request", "request_alternative", "request_alternative_evidence", "alternative", "evidence")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path, required=True)
    args = parser.parse_args()
    report = {"version": "uc001-granite-windows-compat-v1", "status": "failed",
        "observed_utc": datetime.now(timezone.utc).isoformat(), "stage": "paths",
        "python": sys.version, "executable": sys.executable, "api_posts": 0,
        "forbidden_attempts": [], "model_started": False, "live_assessment_invoked": False,
        "granite_suitability": "unverified", "semantic_or_qualified_review": "not performed"}
    output, engines = None, []
    try:
        root = args.worktree.resolve(strict=True)
        require(sys.platform == "win32" and struct.calcsize("P") == 8, "Windows x64 is required")
        require(sys.version_info[:3] == (3, 12, 11), "Exact Python 3.12.11 is required")
        require(root == WORKTREE.resolve(strict=True), "Use the recorded transferred worktree")
        require(Path(sys.executable).resolve() == PYTHON.resolve(strict=True), "Use the new Granite environment")
        require(not Path(__file__).resolve().is_relative_to(root / "scripts/uc001_granite_contract_v1"),
            "Keep this check outside the frozen package")
        output = root / "build/test-only" / ("granite-windows-compat-v1-" + str(uuid4()))
        output.mkdir(parents=True, exist_ok=False)
        database = output / "compatibility.sqlite3"
        report.update(output=str(output), database=str(database), check_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
        require(not any(name.split(".")[0] in ("app", "scripts", "tests") for name in sys.modules),
            "Project modules were already loaded before the explicit worktree binding")
        sys.path[:0] = [str(root / "src"), str(root)]
        report["stage"] = "imports"
        import httpx
        import sqlite3

        def forbidden(kind):
            def reject(*_args, **_kwargs):
                report["forbidden_attempts"].append(kind)
                raise RuntimeError("Forbidden operation: " + kind)
            return reject

        with ExitStack() as guards:
            guards.enter_context(patch.object(httpx.HTTPTransport, "handle_request", forbidden("network HTTP")))
            guards.enter_context(patch.object(httpx.AsyncHTTPTransport, "handle_async_request", forbidden("network HTTP")))
            granite = importlib.import_module("app.infrastructure.granite_interpreter")
            guards.enter_context(patch.object(granite.GraniteInterpreter, "__init__", forbidden("model transport")))
            assessment = importlib.import_module("scripts.uc001_granite_contract_v1.assess")
            composition = importlib.import_module("scripts.uc001_contract_check.development")
            synthetic = importlib.import_module("tests.support.synthetic")
            from fastapi.testclient import TestClient
            store_module = importlib.import_module("app.infrastructure.sqlite_comparisons")
            imported = {"adapter": (granite, "src/app/infrastructure/granite_interpreter.py"),
                "assessment": (assessment, "scripts/uc001_granite_contract_v1/assess.py"),
                "composition": (composition, "scripts/uc001_contract_check/development.py"),
                "synthetic": (synthetic, "tests/support/synthetic.py")}
            report["project_imports"] = {}
            for label, (module, relative) in imported.items():
                path = Path(module.__file__).resolve()
                require(path == (root / relative).resolve(), "Wrong imported module: " + label)
                report["project_imports"][label] = str(path)
            for name, module in tuple(sys.modules.items()):
                prefix = name.split(".")[0]
                if prefix in ("app", "scripts", "tests"):
                    parent = root / ("src/app" if prefix == "app" else prefix)
                    paths = [module.__file__] if getattr(module, "__file__", None) else list(getattr(module, "__path__", []))
                    require(bool(paths) and all(Path(path).resolve().is_relative_to(parent) for path in paths),
                        "Project import escaped the transferred files: " + name)
            require("app.main" not in sys.modules, "Normal app.main must remain inactive")
            assessment.check_dependencies(root)
            report["installed"] = {name: importlib.metadata.version(name) for name in
                ("fastapi", "pydantic", "starlette", "httpx", "sqlalchemy")}
            prepared = synthetic.SyntheticInterpreter().interpret(synthetic.EXAMPLE)
            calls = []

            class PreparedInterpreter:
                def interpret(self, text):
                    require(not calls and text == synthetic.EXAMPLE, "Only one synthetic interpretation is allowed")
                    calls.append(text)
                    return prepared

            original_engine = store_module.create_engine

            def tracked_engine(*arguments, **keywords):
                engine = original_engine(*arguments, **keywords)
                engines.append(engine)
                return engine

            guards.enter_context(patch.object(store_module, "create_engine", tracked_engine))
            report["stage"] = "composition"
            app = composition.create_development_app(database, PreparedInterpreter())
            require(len(engines) == 1, "Expected exactly one SQLite engine")

            def connect():
                return closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True))

            def counts(connection):
                return {table: connection.execute("SELECT count(*) FROM " + table).fetchone()[0] for table in TABLES}

            with connect() as connection:
                report["before_counts"] = counts(connection)
            require(report["before_counts"] == dict(zip(TABLES, (0, 0, 0, 2, 2))), "Unexpected initial fixture counts")
            report["stage"] = "api_post"
            client = TestClient(app, follow_redirects=False)
            try:
                with client:
                    report["api_posts"] += 1
                    response = client.post("/api/comparisons", json={"submission_key": str(uuid4()),
                        "text": synthetic.EXAMPLE, "search_location": {"country_code": "CH"},
                        "location_choice": "provided", "language_context": {"browser_language": "en"}},
                        headers={"X-Submission-Proof": "a" * 64})
                    report.update(http_status=response.status_code, response_text=response.text)
                    body = response.json()
                    report["response"] = body
            finally:
                client.close()
                report["client_closed"] = client.is_closed
            require(report["client_closed"], "In-process client did not close")
            require(response.status_code == 201 and body["outcome"] == "comparison", "Expected HTTP 201 / comparison")
            identity = body["persistence"]["request_id"]
            UUID(identity)
            require(body["persistence"]["state"] == "saved" and body["comparison"]["request_id"] == identity,
                "Saved request identity differs")
            require(body["assessed_at"] == body["comparison"]["assessed_at"] == synthetic.FIXTURE_TIME.isoformat(),
                "Synthetic assessment timestamp differs")
            options = body["comparison"]["options"]
            require([item["display_name"] for item in options] == ["Alpha repair (synthetic)", "Zeta repair (synthetic)"]
                and [item["position"] for item in options] == [1, 2], "Expected synthetic options/order differ")
            require(calls == [synthetic.EXAMPLE], "Expected one prepared synthetic interpretation")
            report["stage"] = "sqlite_projection"
            with connect() as connection:
                report["after_counts"] = counts(connection)
                require(report["after_counts"] == dict(zip(TABLES, (1, 2, 2, 2, 2))), "Saved row counts differ")
                row = connection.execute("SELECT id, original_text, interpretation, search_location, projection FROM search_request").fetchone()
                require(row[0] == identity and row[1] == synthetic.EXAMPLE and json.loads(row[3]) == {"country_code": "CH"}
                    and json.loads(row[4]) == body, "SQLite saved request/projection differs")
                require(json.loads(row[2])["constraints"] == [{"value": "no_replacement", "quote": "without replacing it"}],
                    "Prepared constraint was not retained")
                saved = connection.execute("SELECT id, request_id, alternative_id, position, snapshot FROM request_alternative ORDER BY position").fetchall()
                for option, (option_id, request_id, alternative, position, snapshot) in zip(options, saved, strict=True):
                    UUID(option_id)
                    require(request_id == identity and (option_id, alternative, position) == (option["option_id"], option["alternative_id"], option["position"])
                        and json.loads(snapshot) == option and option["financial"]["amount"] == "45.00"
                        and option["environmental"]["status"] == "unknown", "Saved option identity/snapshot differs")
                links = connection.execute("SELECT option_id, evidence_version_id FROM request_alternative_evidence ORDER BY option_id, evidence_version_id").fetchall()
                expected_links = sorted((option["option_id"], evidence["version_id"]) for option in options for evidence in option["evidence"])
                require(links == expected_links, "Saved evidence associations differ")
                evidence = {key: json.loads(snapshot) for key, snapshot in connection.execute("SELECT version_id, snapshot FROM evidence")}
                require(evidence == {version.version_id: version.snapshot for candidate in synthetic.candidates() for version in candidate.evidence},
                    "Seeded evidence snapshots differ")
                report.update(request_id=identity, evidence_links=links, projection_matches=True, option_snapshots_match=True)
            require(not report["forbidden_attempts"], "Unexpected network/model attempt")
            report["status"] = "passed"
    except BaseException as error:
        report["error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    finally:
        cleanup = []
        for engine in engines:
            try:
                engine.dispose()
            except BaseException as error:
                cleanup.append(str(error))
        report["engines_disposed"] = len(engines) if not cleanup else False
        if cleanup:
            report.update(status="failed", cleanup_errors=cleanup)
        report["windows_application_compatibility_passed"] = report["status"] == "passed"
        report["evidence_kind"] = "prepared synthetic Windows dependency check; not model generation or captured-model replay"
        if output is not None:
            result = output / "result.json"
            with result.open("x", encoding="utf-8", newline="\n") as file:
                json.dump(report, file, ensure_ascii=False, indent=2)
                file.write("\n")
            report["result_file"] = str(result)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
