"""Explicit candidate + synthetic-knowledge composition, never imported by app.main."""

from dataclasses import replace
from pathlib import Path

from app.interfaces.api import create_app
from tests.support.synthetic import create_service


def create_development_app(database: Path, interpreter):
    root = Path(__file__).resolve().parents[2] / "build" / "test-only"
    database = database.resolve()
    if database.suffix != ".sqlite3" or not database.is_relative_to(root.resolve()) or database.exists():
        raise ValueError("Use a new isolated build/test-only/*.sqlite3 database")
    database.parent.mkdir(parents=True, exist_ok=True)
    service = replace(create_service(database), interpreter=interpreter, recognizer=None)
    return create_app(service)
