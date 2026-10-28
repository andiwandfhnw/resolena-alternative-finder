from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
import json
from typing import Any, Callable, Protocol
from uuid import uuid4

from app.domain.comparison import Candidate, Interpretation, PreparedOption, display_order
from app.domain.qualification import Qualification, qualify


class ConfigurationUnavailable(Exception):
    pass


class InputOutcome(Exception):
    def __init__(self, outcome: str, code: str):
        if outcome not in ("invalid_input", "clarification_required", "interpretation_unavailable"):
            raise ValueError("Not an input outcome")
        self.outcome, self.code = outcome, code
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
    def interpret(self, submission: Submission) -> Interpretation: ...


class Knowledge(Protocol):
    def retrieve(self, interpretation: Interpretation, submission: Submission) -> tuple[Candidate, ...]: ...


class Renderer(Protocol):
    def prepare(self, interpretation: Interpretation, candidates: tuple[Qualification, ...]) -> tuple[PreparedOption, ...]: ...


class ComparisonStore(Protocol):
    def find(self, key_digest: str) -> SavedSubmission | None: ...
    def save(self, prepared: PreparedSave) -> dict[str, Any]: ...


def digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class CompareRequest:
    interpreter: RequestInterpreter
    knowledge: Knowledge
    renderer: Renderer
    store: ComparisonStore
    clock: Callable[[], datetime]

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

        interpretation = self.interpreter.interpret(submission)
        if not interpretation.subject.strip():
            raise InputOutcome("invalid_input", "subject_unclear")
        if any(not item.quote or item.quote not in submission.text for item in interpretation.constraints):
            raise ValueError("Interpretation contains an ungrounded constraint")
        candidates = self.knowledge.retrieve(interpretation, submission)
        assessed = self.clock()
        assessments = [qualify(candidate, interpretation, submission.search_location, assessed) for candidate in candidates]
        qualified = {result.candidate.alternative_id: result for result in assessments if result.qualified}
        if len({c.alternative_id for c in candidates}) != len(candidates):
            raise ValueError("Duplicate alternative identity")
        # Select only after every retrieved candidate has been assessed.
        ordered = display_order(PreparedOption(c.alternative_id, c.display_name, {}, ()) for c in candidates if c.alternative_id in qualified)
        selected = tuple(qualified[item.alternative_id] for item in ordered[:3])
        rendered = self.renderer.prepare(interpretation, selected) if selected else ()
        if tuple(option.alternative_id for option in rendered) != tuple(c.candidate.alternative_id for c in selected):
            raise ValueError("Rendering changed the qualified display identities/order")
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
            "persistence": {"state": "saved", "request_id": request_id},
            "comparison": {
                "request_id": request_id, "assessed_at": assessed_at,
                "explanation_language": interpretation.explanation_language,
                "language_origin": interpretation.language_origin,
                "interpretation_version": interpretation.version,
                "options": displayed, "omitted_count": max(0, len(qualified) - 3),
            },
        }
        if not options:
            del projection["comparison"]
            projection["issues"] = [{"code": "no_qualifying_knowledge"}, {"code": "research_unavailable"}]
            projection["limitations"] = ["Existing knowledge cannot support this request under its constraints. Research is unavailable in this increment; alternatives may exist. Edit and resubmit explicitly."]
            reasons = {code for result in assessments for code in result.limitation_codes}
            if not assessments:
                reasons.add("no_retrieved_knowledge")
            explanations = {
                "essential_evidence_expired": "Required evidence has expired; its original review dates were retained.",
                "essential_freshness_unverified": "Required review timestamps or temporal applicability could not establish freshness.",
                "essential_support_unverified": "Required information has missing or disputed source support.",
                "requirement_contradicted": "Reviewed evidence contradicts a request requirement.",
                "geographic_applicability_unverified": "Existing evidence does not establish applicability in the requested location.",
                "useful_comparison_information_missing": "No qualifying candidate has useful supported financial or environmental/resource information.",
                "cost_requirement_not_established": "Comparable supported costs do not establish the requested budget or cheaper goal; unknown charges are not zero.",
                "no_retrieved_knowledge": "No relevant prepared knowledge was retrieved for assessment.",
            }
            projection["coverage"] = {"limitation_codes": sorted(reasons)}
            projection["limitations"].extend(explanations[code] for code in sorted(reasons))
        prepared = PreparedSave(submission, key_digest, binding, payload_digest, interpretation, projection, options)
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
