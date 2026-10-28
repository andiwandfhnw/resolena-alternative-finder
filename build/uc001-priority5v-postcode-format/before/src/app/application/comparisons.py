from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
import json
from unicodedata import normalize
from typing import Any, Callable, Protocol
from uuid import uuid4

from app.domain.comparison import Candidate, Interpretation, PreparedOption, display_order
from app.domain.qualification import Qualification, qualify
from app.domain.interpretation import ContractViolation, InterpretationResult, LanguageOutcome, Recognition, apply_language_policy
from app.application.countries import CountryReference, CountryReferenceUnavailable
from app.application.localities import LocalityCatalogue, LocalityReference


class ConfigurationUnavailable(Exception):
    pass


class InputOutcome(Exception):
    def __init__(self, outcome: str, code: str, detail: dict[str, Any] | None = None):
        if outcome not in ("invalid_input", "clarification_required", "interpretation_unavailable"):
            raise ValueError("Not an input outcome")
        self.outcome, self.code = outcome, code
        self.detail = detail or {}
        super().__init__(code)


class OwnershipDenied(Exception):
    pass


class PayloadConflict(Exception):
    pass


class DuplicateSubmission(Exception):
    pass


class PersistenceFailure(Exception):
    def __init__(self, state: str):
        self.state = state
        self.assessed_outcome = None
        super().__init__(state)


@dataclass(frozen=True)
class Submission:
    key: str
    proof: str
    text: str
    search_location: dict[str, Any]
    location_choice: str
    language_context: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        return {
            "text": self.text, "search_location": self.search_location,
            "location_choice": self.location_choice, "language_context": self.language_context,
        }


@dataclass(frozen=True)
class SavedSubmission:
    proof_binding: str
    payload_digest: str
    projection: dict[str, Any]


@dataclass(frozen=True)
class PreparedSave:
    submission: Submission
    key_digest: str
    proof_binding: str
    payload_digest: str
    interpretation: Interpretation
    projection: dict[str, Any]
    options: tuple[PreparedOption, ...]


class RequestInterpreter(Protocol):
    def interpret(self, original_text: str) -> InterpretationResult: ...


class InputRecognizer(Protocol):
    def recognize(self, original_text: str) -> Recognition | None: ...


class Knowledge(Protocol):
    def retrieve(self, interpretation: Interpretation, submission: Submission) -> tuple[Candidate, ...]: ...


class Renderer(Protocol):
    def prepare(self, interpretation: Interpretation, candidates: tuple[Qualification, ...]) -> tuple[PreparedOption, ...]: ...
    def prepare_coverage(self, interpretation: Interpretation, limitation_codes: tuple[str, ...]) -> dict[str, Any]: ...


class ComparisonStore(Protocol):
    def find(self, key_digest: str) -> SavedSubmission | None: ...
    def save(self, prepared: PreparedSave) -> dict[str, Any]: ...


def digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def effective_search_location(submission: Submission, catalogue: LocalityCatalogue | None = None) -> dict[str, Any]:
    if submission.location_choice == "country_only":
        return {"country_code": submission.search_location["country_code"]}
    intended = {key: submission.search_location[key] for key in ("town", "postcode") if submission.search_location.get(key)}
    normalized = {key: normalize("NFC", value.strip()).casefold() if key == "town" else value.strip()
        for key, value in intended.items()}
    if submission.location_choice == "confirmed_unverified" and any(submission.search_location.get(key) for key in ("town", "postcode")):
        return {"country_code": submission.search_location["country_code"], **intended,
            "locality": {"confirmation": "user_confirmed", "verification": "reference_unverified", "normalized": normalized}}
    if any(submission.search_location.get(field) for field in ("town", "postcode", "reference")):
        if catalogue is not None:
            country = submission.search_location["country_code"]
            matches = catalogue.matches(country, submission.search_location.get("town"), submission.search_location.get("postcode"))
            pointer = submission.search_location.get("reference")
            selected = catalogue.selected(pointer) if pointer is not None else None
            choices = [catalogue.association(row) for row in matches]
            if selected is not None and selected["country_code"] != country:
                raise InputOutcome("invalid_input", "locality_country_mismatch", {"clarification": {
                    "message": "The selected reference association belongs to a different search country. Correct the country or locality selection explicitly.",
                    "choices": [], "associations": []}})
            if pointer is not None and (selected is None or selected not in matches):
                raise InputOutcome("clarification_required", "locality_selection_inconsistent", {"clarification": {
                    "message": "The selected association does not match this pinned reference, country and entered fields. Correct the fields or select a supported association and continue explicitly.",
                    "choices": [], "associations": choices}})
            if not matches:
                raise InputOutcome("clarification_required", "locality_reference_unknown", {"clarification": {
                    "message": "No association matches all entered fields within this reference's CH/LI coverage. This is not proof that the entered locality is invalid. Correct the fields, explicitly continue country-only, or confirm the entered locality as intended scope. Confirmation establishes intended scope only; it does not establish delivery or service coverage.",
                    "choices": [], "associations": []}})
            if selected is None and len(matches) > 1:
                raise InputOutcome("clarification_required", "locality_reference_ambiguous", {"clarification": {
                    "message": "Multiple reference associations match the entered fields. These are postal/municipal associations, not a count of distinct physical localities. Select a supported association and continue explicitly, correct the fields or continue country-only.",
                    "choices": [], "associations": choices}})
            selected = selected or matches[0]
            return {"country_code": country, **intended, "locality": {
                "verification": "matched_in_reference", "selection": "explicit" if pointer is not None else "single_match",
                "normalized": normalized, "association": catalogue.association(selected)}}
        raise InputOutcome("clarification_required", "locality_reference_unavailable", {
            "clarification": {
                "message": "The locality cannot currently be verified because locality reference data is unavailable. Correct the fields, explicitly continue country-only, or confirm the entered locality as intended scope. Confirmation establishes intended scope only. It does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability.",
                "choices": [],
            }})
    return submission.search_location


@dataclass(frozen=True)
class CompareRequest:
    interpreter: RequestInterpreter
    knowledge: Knowledge
    renderer: Renderer
    store: ComparisonStore
    clock: Callable[[], datetime]
    recognizer: InputRecognizer | None = None
    countries: CountryReference | None = None
    localities: LocalityReference | None = None

    def _acknowledge(self, saved: SavedSubmission, binding: str, payload_digest: str) -> dict[str, Any]:
        if not compare_digest(saved.proof_binding, binding):
            raise OwnershipDenied
        if not compare_digest(saved.payload_digest, payload_digest):
            raise PayloadConflict
        return {
            "outcome": "submission_recovered",
            "persistence": saved.projection["persistence"],
            "assessed_at": saved.projection.get("assessed_at", saved.projection.get("comparison", {}).get("assessed_at")),
            "saved_outcome": saved.projection["outcome"],
        }

    def execute(self, submission: Submission) -> dict[str, Any]:
        key_digest = digest(submission.key)
        binding = digest([submission.key, submission.proof])
        payload_digest = digest(submission.payload())
        saved = self.store.find(key_digest)
        if saved is not None:
            return self._acknowledge(saved, binding, payload_digest)

        if self.countries is None:
            raise CountryReferenceUnavailable
        catalogue = self.countries.load()
        country = submission.search_location.get("country_code")
        if not isinstance(country, str) or not catalogue.contains(country):
            raise InputOutcome("invalid_input", "country_not_in_catalogue")

        hypothesis = self.recognizer.recognize(submission.text) if self.recognizer else None
        result = self.interpreter.interpret(submission.text)
        if not isinstance(result, InterpretationResult) or result.original_text != submission.text:
            raise ContractViolation("Interpreter must retain the complete original input")
        try:
            interpretation = apply_language_policy(result, submission.language_context, hypothesis)
        except LanguageOutcome as action:
            raise InputOutcome(action.outcome, action.code, action.detail) from None
        interpretation = replace(interpretation, provenance={**interpretation.provenance,
            "reference_versions": {"country": catalogue.reference()}})
        language = {"recognition": asdict(result.recognition), "meaning_status": result.meaning_status,
            "explanation_language": interpretation.explanation_language, "origin": interpretation.language_origin,
            "correction_available": True}
        locality_catalogue = None
        if (submission.location_choice == "provided" and self.localities is not None
                and any(submission.search_location.get(key) for key in ("town", "postcode", "reference"))):
            locality_catalogue = self.localities.load()
        effective = replace(submission, search_location=effective_search_location(submission, locality_catalogue))
        association = effective.search_location.get("locality", {}).get("association")
        assessment_location = effective.search_location
        if association is not None:
            interpretation = replace(interpretation, provenance={**interpretation.provenance,
                "reference_versions": {**interpretation.provenance["reference_versions"], "locality": locality_catalogue.reference()}})
            assessment_location = {**effective.search_location,
                "town": association["locality_name"], "postcode": association["postcode"]}
        candidates = self.knowledge.retrieve(interpretation, effective)
        assessed = self.clock()
        assessments = [qualify(candidate, interpretation, assessment_location, assessed) for candidate in candidates]
        qualified = {result.candidate.alternative_id: result for result in assessments if result.qualified}
        if len({c.alternative_id for c in candidates}) != len(candidates):
            raise ValueError("Duplicate alternative identity")
        # Select only after every retrieved candidate has been assessed.
        ordered = display_order(PreparedOption(c.alternative_id, c.display_name, {}, ()) for c in candidates if c.alternative_id in qualified)
        selected = tuple(qualified[item.alternative_id] for item in ordered[:3])
        rendered = self.renderer.prepare(interpretation, selected) if selected else ()
        if tuple(option.alternative_id for option in rendered) != tuple(c.candidate.alternative_id for c in selected):
            raise ValueError("Rendering changed the qualified display identities/order")
        for option in rendered:
            self._check_rendering(option.snapshot, interpretation)
        options = tuple(PreparedOption(option.alternative_id, selected[index].candidate.display_name,
            {**option.snapshot, **qualified[option.alternative_id].snapshot},
            qualified[option.alternative_id].evidence_version_ids) for index, option in enumerate(rendered))
        request_id = str(uuid4())
        assessed_at = assessed.isoformat()
        displayed = [
            {**option.snapshot, "option_id": str(uuid4()), "alternative_id": option.alternative_id,
             "position": position, "display_name": option.display_name}
            for position, option in enumerate(options, 1)
        ]
        projection = {
            "outcome": "comparison" if options else "insufficient_coverage",
            "assessed_at": assessed_at,
            "language": language,
            "persistence": {"state": "saved", "request_id": request_id},
            "comparison": {
                "request_id": request_id, "assessed_at": assessed_at,
                "explanation_language": interpretation.explanation_language,
                "language_origin": interpretation.language_origin,
                "interpretation_version": interpretation.version,
                "options": displayed, "omitted_count": max(0, len(qualified) - 3),
            },
        }
        if "locality" in effective.search_location:
            projection["search_scope"] = effective.search_location
        if not options:
            del projection["comparison"]
            projection["issues"] = [{"code": "no_qualifying_knowledge"}, {"code": "research_unavailable"}]
            reasons = {code for result in assessments for code in result.limitation_codes}
            if not assessments:
                reasons.add("no_retrieved_knowledge")
            projection["coverage"] = {"limitation_codes": sorted(reasons)}
            coverage = self.renderer.prepare_coverage(interpretation, tuple(sorted(reasons)))
            self._check_rendering(coverage, interpretation)
            if not coverage.get("limitations"):
                raise ValueError("Coverage explanation is incomplete")
            projection.update({key: coverage[key] for key in ("limitations", "rendering")})
        prepared = PreparedSave(effective, key_digest, binding, payload_digest, interpretation, projection, options)
        try:
            return self.store.save(prepared)
        except PersistenceFailure as error:
            error.assessed_outcome = projection["outcome"]
            raise
        except DuplicateSubmission:
            winner = self.store.find(key_digest)
            if winner is None:
                raise PersistenceFailure("unknown") from None
            return self._acknowledge(winner, binding, payload_digest)

    @staticmethod
    def _check_rendering(snapshot: dict[str, Any], interpretation: Interpretation):
        rendering = snapshot.get("rendering", {})
        if rendering.get("language") != interpretation.explanation_language or not rendering.get("version"):
            raise ValueError("Renderer changed the selected language or omitted its version")
