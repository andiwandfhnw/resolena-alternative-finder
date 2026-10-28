from datetime import datetime, timezone
from pathlib import Path

from app.application.comparisons import CompareRequest, ConfigurationUnavailable, InputOutcome
from app.domain.comparison import Candidate, EvidenceVersion, PreparedOption
from app.domain.qualification import Claim, Money, value_data
from app.domain.interpretation import Clause, InterpretationResult, MeaningItem, OriginalSpan, Recognition
from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from app.infrastructure.country_reference import LocalCountryCatalogue
from app.interfaces.api import create_app


EXAMPLE = "Repair my bicycle without replacing it"
FIXTURE_TIME = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)


def represented_locality():
    text = "repair bicycle in Genève"

    def span(quote):
        start = text.index(quote)
        return OriginalSpan(start, start + len(quote), quote)

    items = (MeaningItem("subject", "subject", "bicycle", span("bicycle")),
        MeaningItem("place", "place", "Genève", span("Genève")),
        MeaningItem("locality", "constraint", "locality:Genève", span("in Genève")))
    return InterpretationResult(text, Recognition("supported", "en", "synthetic"), "understood",
        (Clause(OriginalSpan(0, len(text), text), "understood", "synthetic intended scope", tuple(i.id for i in items)),),
        items, "synthetic")


def candidates():
    result = []
    for suffix, name in [(2, "Zeta repair (synthetic)"), (1, "Alpha repair (synthetic)")]:
        alternative_id = f"00000000-0000-4000-8000-{suffix:012d}"
        version_id = f"30000000-0000-4000-8000-{suffix:012d}"
        scope = {"country_code": "CH"}
        claims = (
            Claim("relevance", "bicycle", "specification", scope),
            Claim("action:repair", True, "specification", scope),
            Claim("no_replacement", True, "specification", scope),
            Claim("applicability", True, "service_coverage", scope),
            Claim("financial", Money("45.00", "CHF", "repair", "once", "per repair",
                charges_known=False, exclusions=("parts",)), "price", scope, specific=True),
        )
        version = EvidenceVersion(version_id, alternative_id, {
            "version_id": version_id, "publisher": "Synthetic fixture provider",
            "source_reference": f"synthetic:repair-{suffix}-v3", "source_language": "en",
            "supporting_quote": "Repairs existing bicycles without replacement in CH. Labour CHF 45.00 per repair; parts excluded.",
            "reviewed_at": FIXTURE_TIME.isoformat(), "review_basis": "synthetic test metadata, not factual review",
            "publication_date": None, "retrieved_at": None, "data_period": None,
            "scope": scope, "competent_claims": [claim.key for claim in claims],
            "assertions": {claim.key: value_data(claim.value) for claim in claims},
            "attribution": "provider-stated",
            "synthetic": True,
        })
        result.append(Candidate(alternative_id, name, (version,), claims))
    return tuple(result)


class SyntheticInterpreter:
    def interpret(self, original_text):
        if original_text == "Synthetic unsupported input":
            return InterpretationResult(original_text, Recognition("unsupported", None, "synthetic-only"),
                "unsupported", (), (), "synthetic-only", "Synthetic capability limitation. Rephrase in German, French, Italian or English.")
        if original_text == "Synthetic unclear clause":
            return InterpretationResult(original_text, Recognition("unknown", None, "synthetic-only"), "needs_clarification",
                (Clause(OriginalSpan(0, len(original_text), original_text), "needs_clarification", None, ()),),
                (), "synthetic-only", "Clarify the synthetic clause before continuing.")
        if original_text not in (EXAMPLE, "Velo"):
            raise ConfigurationUnavailable("Only the exact synthetic fixture is configured")
        def span(quote):
            start = original_text.index(quote)
            return OriginalSpan(start, start + len(quote), quote)
        items = (MeaningItem("subject", "subject", "bicycle", span("Velo" if original_text == "Velo" else "bicycle")),)
        if original_text == EXAMPLE:
            items += (MeaningItem("constraint", "constraint", "no_replacement", span("without replacing it"), negation=span("without")),
                MeaningItem("action", "action", "repair", span("Repair")))
        return InterpretationResult(original_text,
            Recognition("unknown", None, "synthetic-only") if original_text == "Velo" else Recognition("supported", "en", "synthetic-only"),
            "understood", (Clause(OriginalSpan(0, len(original_text), original_text), "understood",
                "synthetic bicycle scope" if original_text == "Velo" else "synthetic repair without replacement", tuple(item.id for item in items)),),
            items, "test-only-exact-fixture-v2")


class SyntheticKnowledge:
    def retrieve(self, interpretation, submission):
        return candidates()


class SyntheticRenderer:
    @staticmethod
    def _english(interpretation):
        if interpretation.explanation_language != "en":
            raise InputOutcome("interpretation_unavailable", "rendering_unavailable", {
                "limitation": "Only the English synthetic rendering is configured. No target-language translation was attempted."})

    def prepare(self, interpretation, retrieved):
        self._english(interpretation)
        return tuple(PreparedOption(result.candidate.alternative_id, result.candidate.display_name, {
            "description": "Synthetic bicycle repair service; not a real provider.",
            "explanation": "Repair the existing bicycle without replacement. Financial and environmental/resource details follow their individual evidence assessments below.",
            **result.snapshot,
            "rendering": {"language": "en", "version": "synthetic-reviewed-rendering-v1",
                "review_basis": "synthetic test fixture, not qualified linguistic review"},
            "limitations": ["Synthetic fixtures only; no verified provider, saving or environmental advantage.",
                "Fixture clock: 2026-10-15T10:00:00+00:00; not current factual validation."],
            "synthetic": True,
        }, result.evidence_version_ids) for result in retrieved)

    def prepare_coverage(self, interpretation, limitation_codes):
        self._english(interpretation)
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
        return {"limitations": ["Existing knowledge cannot support this request under its constraints. Research is unavailable in this increment; alternatives may exist. Edit and resubmit explicitly.",
                *(explanations[code] for code in limitation_codes)],
            "rendering": {"language": "en", "version": "synthetic-coverage-v1"}}


def create_service(path: Path):
    store = SQLiteComparisonStore(path)
    store.seed_test_knowledge(candidates())
    return CompareRequest(SyntheticInterpreter(), SyntheticKnowledge(), SyntheticRenderer(), store, lambda: FIXTURE_TIME,
        countries=LocalCountryCatalogue())


def create_test_app(path: Path):
    return create_app(create_service(path))
