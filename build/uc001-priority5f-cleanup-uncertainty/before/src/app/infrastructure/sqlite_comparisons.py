from dataclasses import asdict
from pathlib import Path
from typing import Any

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, JSON, MetaData, String, Table, UniqueConstraint, create_engine, event, insert, select
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from app.application.comparisons import DuplicateSubmission, PersistenceFailure, PreparedSave, SavedSubmission
from app.domain.comparison import Candidate


metadata = MetaData()
alternatives = Table("alternative", metadata,
    Column("id", String, primary_key=True), Column("display_name", String, nullable=False))
evidence = Table("evidence", metadata,
    Column("version_id", String, primary_key=True),
    Column("alternative_id", ForeignKey("alternative.id"), nullable=False),
    Column("snapshot", JSON, nullable=False))
requests = Table("search_request", metadata,
    Column("id", String, primary_key=True),
    Column("submission_key_digest", String, unique=True, nullable=False),
    Column("proof_binding", String, nullable=False), Column("payload_digest", String, nullable=False),
    Column("original_text", String, nullable=False), Column("interpretation", JSON, nullable=False),
    Column("search_location", JSON, nullable=False), Column("location_choice", String, nullable=False),
    Column("language_context", JSON, nullable=False), Column("assessed_at", String, nullable=False),
    Column("outcome", String, nullable=False), Column("projection", JSON, nullable=False))
options = Table("request_alternative", metadata,
    Column("id", String, primary_key=True), Column("request_id", ForeignKey("search_request.id"), nullable=False),
    Column("alternative_id", ForeignKey("alternative.id"), nullable=False),
    Column("position", Integer, nullable=False), Column("snapshot", JSON, nullable=False),
    UniqueConstraint("request_id", "position"), UniqueConstraint("request_id", "alternative_id"),
    CheckConstraint("position BETWEEN 1 AND 3"))
links = Table("request_alternative_evidence", metadata,
    Column("option_id", ForeignKey("request_alternative.id"), primary_key=True),
    Column("evidence_version_id", ForeignKey("evidence.version_id"), primary_key=True))


class SQLiteComparisonStore:
    def __init__(self, path: Path):
        self.engine = create_engine(URL.create("sqlite", database=str(path)),
            connect_args={"check_same_thread": False, "timeout": 1})

        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            for operation in ("UPDATE", "DELETE"):
                connection.exec_driver_sql(f"""CREATE TRIGGER IF NOT EXISTS evidence_no_{operation.lower()}
                    BEFORE {operation} ON evidence BEGIN SELECT RAISE(ABORT, 'Evidence versions are immutable'); END""")

    def seed_test_knowledge(self, candidates: tuple[Candidate, ...]) -> None:
        with self.engine.begin() as connection:
            for candidate in candidates:
                existing = connection.execute(select(alternatives).where(alternatives.c.id == candidate.alternative_id)).mappings().first()
                if existing is None:
                    connection.execute(insert(alternatives).values(id=candidate.alternative_id, display_name=candidate.display_name))
                for version in candidate.evidence:
                    previous = connection.execute(select(evidence.c.snapshot).where(evidence.c.version_id == version.version_id)).first()
                    if previous is not None:
                        if previous[0] != version.snapshot:
                            raise ValueError("Existing evidence version differs; no overwrite permitted")
                    else:
                        connection.execute(insert(evidence).values(version_id=version.version_id,
                            alternative_id=version.alternative_id, snapshot=version.snapshot))

    def find(self, key_digest: str) -> SavedSubmission | None:
        with self.engine.connect() as connection:
            row = connection.execute(select(requests).where(requests.c.submission_key_digest == key_digest)).mappings().first()
            return SavedSubmission(row["proof_binding"], row["payload_digest"], row["projection"]) if row else None

    def save(self, prepared: PreparedSave) -> dict[str, Any]:
        body = prepared.projection
        commit_confirmed = False
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(insert(requests).values(
                    id=body["persistence"]["request_id"], submission_key_digest=prepared.key_digest,
                    proof_binding=prepared.proof_binding, payload_digest=prepared.payload_digest,
                    original_text=prepared.submission.text, interpretation=asdict(prepared.interpretation),
                    search_location=prepared.submission.search_location, location_choice=prepared.submission.location_choice,
                    language_context=prepared.submission.language_context, assessed_at=body["assessed_at"],
                    outcome=body["outcome"], projection=body))
                for option, snapshot in zip(prepared.options, body.get("comparison", {}).get("options", []), strict=True):
                    connection.execute(insert(options).values(id=snapshot["option_id"], request_id=body["persistence"]["request_id"],
                        alternative_id=option.alternative_id, position=snapshot["position"], snapshot=snapshot))
                    for version_id in option.evidence_version_ids:
                        connection.execute(insert(links).values(option_id=snapshot["option_id"], evidence_version_id=version_id))
            except SQLAlchemyError:
                transaction.rollback()
                if self.find(prepared.key_digest) is not None:
                    raise DuplicateSubmission from None
                raise PersistenceFailure("failed") from None
            try:
                transaction.commit()
            except SQLAlchemyError:
                transaction.rollback()
            else:
                commit_confirmed = True
        try:
            committed = self.find(prepared.key_digest)
        except SQLAlchemyError:
            raise PersistenceFailure("unknown") from None
        if committed is None:
            raise PersistenceFailure("unknown")
        if not commit_confirmed:
            raise DuplicateSubmission
        return committed.projection
