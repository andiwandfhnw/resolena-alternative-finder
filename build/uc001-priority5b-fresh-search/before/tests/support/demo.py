import argparse
import os
from pathlib import Path

import uvicorn

from app.interfaces.api import create_app
from tests.support.source_bound_rendering import create_demo_service


def main():
    parser = argparse.ArgumentParser(description="Test-only synthetic comparison server; no real interpreter or knowledge")
    parser.add_argument("--db", default=os.environ.get("RESOLENA_TEST_DATABASE"), required=not os.environ.get("RESOLENA_TEST_DATABASE"))
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2] / "build" / "test-only"
    database = Path(args.db).resolve()
    if database.suffix != ".sqlite3" or not database.is_relative_to(root.resolve()):
        parser.error("Use a separate .sqlite3 database beneath build/test-only/")
    database.parent.mkdir(parents=True, exist_ok=True)
    app = create_app(create_demo_service(database))
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
    finally:
        app.state.comparisons.store.engine.dispose()


if __name__ == "__main__":
    main()
