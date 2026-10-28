import re
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.application.comparisons import CompareRequest, ConfigurationUnavailable, InputOutcome, OwnershipDenied, PayloadConflict, PersistenceFailure, Submission


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    town: str | None = None
    postcode: str | None = None
    reference: dict | None = None


class LanguageContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preferred_language: Literal["de", "fr", "it", "en"] | None = None
    browser_language: Literal["de", "fr", "it", "en"] | None = None
    explanation_language_choice: Literal["de", "fr", "it", "en"] | None = None


class ComparisonInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submission_key: UUID
    text: str = Field(min_length=1)
    search_location: Location
    location_choice: Literal["provided", "country_only", "confirmed_unverified"] = "provided"
    language_context: LanguageContext = Field(default_factory=LanguageContext)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("A subject is required")
        return value


def failure(status: int, outcome: str, state: str, code: str):
    return JSONResponse(status_code=status, content={
        "outcome": outcome, "persistence": {"state": state}, "issues": [{"code": code}],
    })


def create_app(comparisons: CompareRequest | None = None) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None)
    app.state.comparisons = comparisons

    @app.get("/health")
    def health():
        return {"status": "ok", "interpreter_configured": comparisons is not None}

    @app.exception_handler(RequestValidationError)
    async def invalid_input(_request, _error):
        return failure(422, "invalid_input", "not_attempted", "request_fields_invalid")

    @app.post("/api/comparisons")
    def compare(payload: ComparisonInput, x_submission_proof: str | None = Header(default=None)):
        if x_submission_proof is None or re.fullmatch(r"[0-9a-f]{64}", x_submission_proof) is None:
            return failure(403, "recovery_not_authorized", "not_attempted", "originating_proof_required")
        if comparisons is None:
            return failure(503, "configuration_unavailable", "not_attempted", "runtime_adapters_not_configured")
        command = Submission(str(payload.submission_key), x_submission_proof, payload.text,
            payload.search_location.model_dump(exclude_none=True), payload.location_choice,
            payload.language_context.model_dump(exclude_none=True))
        try:
            body = comparisons.execute(command)
        except InputOutcome as error:
            return failure(422 if error.outcome == "invalid_input" else 200, error.outcome, "not_attempted", error.code)
        except ConfigurationUnavailable:
            return failure(503, "configuration_unavailable", "not_attempted", "test_fixture_only")
        except OwnershipDenied:
            return failure(403, "recovery_not_authorized", "not_attempted", "originating_proof_required")
        except PayloadConflict:
            return failure(409, "submission_key_conflict", "not_attempted", "payload_changed")
        except PersistenceFailure as error:
            response = {"outcome": "persistence_error", "persistence": {"state": error.state},
                "issues": [{"code": "comparison_save_failed"}], "assessed_outcome": error.assessed_outcome}
            return JSONResponse(status_code=503, content=response)
        except Exception:
            return failure(500, "processing_error", "not_attempted", "comparison_processing_failed")
        return JSONResponse(status_code=201 if body["outcome"] in ("comparison", "insufficient_coverage") else 200, content=body)

    return app
