import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import uvicorn

from app.interfaces.api import create_app
from tests.support.source_bound_rendering import create_demo_service
from tests.support.uncertain_save import install_uncertain_save_fault
from tests.support.delayed_save import install_delayed_save_gate


def main():
    parser = argparse.ArgumentParser(description="Test-only synthetic comparison server; no real interpreter or knowledge")
    parser.add_argument("--db", default=os.environ.get("RESOLENA_TEST_DATABASE"), required=not os.environ.get("RESOLENA_TEST_DATABASE"))
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--clock-file", default=os.environ.get("RESOLENA_TEST_CLOCK_FILE") or None)
    parser.add_argument("--uncertain-save-file", default=os.environ.get("RESOLENA_TEST_UNCERTAIN_SAVE_FILE") or None)
    parser.add_argument("--delayed-save-file", default=os.environ.get("RESOLENA_TEST_DELAYED_SAVE_FILE") or None)
    parser.add_argument("--processing-error-file", default=os.environ.get("RESOLENA_TEST_PROCESSING_ERROR_FILE") or None)
    parser.add_argument("--without-locality-reference", action="store_true",
        default=os.environ.get("RESOLENA_TEST_LOCALITY_REFERENCE_UNAVAILABLE") == "1")
    parser.add_argument("--locality-reference-file", default=os.environ.get("RESOLENA_TEST_LOCALITY_REFERENCE_FILE") or None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2] / "build" / "test-only"
    database = Path(args.db).resolve()
    if database.suffix != ".sqlite3" or not database.is_relative_to(root.resolve()):
        parser.error("Use a separate .sqlite3 database beneath build/test-only/")
    database.parent.mkdir(parents=True, exist_ok=True)
    clock = None
    if args.clock_file:
        clock_file = Path(args.clock_file).resolve()
        if clock_file.suffix != ".json" or not clock_file.is_relative_to(root.resolve()):
            parser.error("Use a synthetic clock JSON file beneath build/test-only/")

        def clock():
            value = datetime.fromisoformat(json.loads(clock_file.read_text())["now"])
            if value.tzinfo is None:
                raise ValueError("Synthetic assessment clock requires an explicit timezone")
            return value.astimezone(timezone.utc)

    uncertain_save_file = None
    if args.uncertain_save_file:
        uncertain_save_file = Path(args.uncertain_save_file).resolve()
        if uncertain_save_file.suffix != ".json" or not uncertain_save_file.is_relative_to(root.resolve()):
            parser.error("Use a synthetic uncertain-save JSON file beneath build/test-only/")
    delayed_save_file = None
    if args.delayed_save_file:
        delayed_save_file = Path(args.delayed_save_file).resolve()
        if delayed_save_file.suffix != ".json" or not delayed_save_file.is_relative_to(root.resolve()):
            parser.error("Use a synthetic delayed-save JSON file beneath build/test-only/")
    processing_error_file = None
    if args.processing_error_file:
        processing_error_file = Path(args.processing_error_file).resolve()
        if processing_error_file.suffix != ".json" or not processing_error_file.is_relative_to(root.resolve()):
            parser.error("Use a synthetic processing-error JSON file beneath build/test-only/")
    locality_reference_file = None
    if args.locality_reference_file:
        locality_reference_file = Path(args.locality_reference_file).resolve()
        if locality_reference_file.suffix != ".json" or not locality_reference_file.is_relative_to(root.resolve()):
            parser.error("Use a test-only locality composition JSON file beneath build/test-only/")
    service = create_demo_service(database, clock=clock, processing_error_file=processing_error_file,
        uncertain_save_file=uncertain_save_file, locality_reference=not args.without_locality_reference,
        locality_reference_file=locality_reference_file)
    cleanup_uncertain = install_uncertain_save_fault(service.store, database, uncertain_save_file) if uncertain_save_file else None
    cleanup_gate = install_delayed_save_gate(service.store, database, delayed_save_file) if delayed_save_file else None
    app = create_app(service)
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
    finally:
        service.cleanup()
        if cleanup_gate is not None:
            cleanup_gate()
        if cleanup_uncertain is not None:
            cleanup_uncertain()
        app.state.comparisons.store.engine.dispose()


if __name__ == "__main__":
    main()
