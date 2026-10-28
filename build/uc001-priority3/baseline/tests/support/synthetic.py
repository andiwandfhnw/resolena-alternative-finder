from datetime import datetime, timezone
from pathlib import Path

from app.application.comparisons import CompareRequest, ConfigurationUnavailable
from app.domain.comparison import Candidate, EvidenceVersion, Interpretation, PreparedOption, QuotedConstraint
from app.domain.qualification import Claim, Money, value_data
from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from app.interfaces.api import create_app


EXAMPLE = "Repair my bicycle without replacing it"
FIXTURE_TIME = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)


def candidates():
    result = []
    for suffix, name in [(2, "Zeta repair (synthetic)"), (1, "Alpha repair (synthetic)")]:
        alternative_id = f"00000000-0000-4000-8000-{suffix:012d}"
        version_id = f"20000000-0000-4000-8000-{suffix:012d}"
        scope = {"country_code": "CH"}
        claims = (
            Claim("relevance", "bicycle", "specification", scope),
            Claim("no_replacement", True, "specification", scope),
            Claim("applicability", True, "service_coverage", scope),
            Claim("financial", Money("45.00", "CHF", "repair", "once", "per repair",
                charges_known=False, exclusions=("parts",)), "price", scope, specific=True),
        )
        version = EvidenceVersion(version_id, alternative_id, {
            "version_id": version_id, "publisher": "Synthetic fixture provider",
            "source_reference": f"synthetic:repair-{suffix}-v2", "source_language": "en",
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
    def interpret(self, submission):
        if (submission.text != EXAMPLE or submission.search_location not in ({"country_code": "CH"}, {"country_code": "DE"})
                or submission.location_choice != "provided" or submission.language_context):
            raise ConfigurationUnavailable("Only the exact synthetic fixture is configured")
        return Interpretation("bicycle", (QuotedConstraint("no_replacement", "without replacing it"),),
            "en", "en", "detected", "test-only-exact-fixture-v1")


class SyntheticKnowledge:
    def retrieve(self, interpretation, submission):
        return candidates()


class SyntheticRenderer:
    def prepare(self, interpretation, retrieved):
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


def create_service(path: Path):
    store = SQLiteComparisonStore(path)
    store.seed_test_knowledge(candidates())
    return CompareRequest(SyntheticInterpreter(), SyntheticKnowledge(), SyntheticRenderer(), store, lambda: FIXTURE_TIME)


def create_test_app(path: Path):
    return create_app(create_service(path))
