"""Two exact fictional examples; no general interpreter or factual review."""
from app.application.comparisons import CompareRequest, ConfigurationUnavailable
from app.domain.comparison import Candidate, EvidenceVersion, PreparedOption
from app.domain.interpretation import Clause, InterpretationResult, MeaningItem, OriginalSpan, Recognition
from app.domain.qualification import Claim, Money, value_data
from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from app.infrastructure.country_reference import LocalCountryCatalogue
from tests.support.synthetic import FIXTURE_TIME, SyntheticRenderer


PRODUCT_EXAMPLE = "Find a secondhand laptop"
HABIT_EXAMPLE = "Refill my existing bottle with potable tap water instead of buying bottled water"
PRODUCT_ID = "00000000-0000-4000-8000-000000000510"
HABIT_ID = "00000000-0000-4000-8000-000000000520"


class ExactInterpreter:
    def interpret(self, text):
        meanings = {
            PRODUCT_EXAMPLE: (("subject", "laptop", "laptop", None),
                ("constraint", "secondhand", "secondhand", None)),
            HABIT_EXAMPLE: (("subject", "drinking_water", "potable tap water", None),
                ("action", "refill", "Refill", None),
                ("constraint", "existing_bottle", "my existing bottle", None),
                ("constraint", "potable_tap_water", "potable tap water", None),
                ("constraint", "avoid_bottled_water", "instead of buying bottled water", "instead of")),
        }
        if text not in meanings:
            raise ConfigurationUnavailable("Only the two exact product/habit examples are configured")

        def span(quote):
            start = text.index(quote)
            return OriginalSpan(start, start + len(quote), quote)

        items = tuple(MeaningItem(f"{kind}:{value}", kind, value, span(quote),
            negation=span(negation) if negation else None) for kind, value, quote, negation in meanings[text])
        return InterpretationResult(text, Recognition("supported", "en", "synthetic-exact-product-habit-v1"),
            "understood", (Clause(OriginalSpan(0, len(text), text), "understood",
                "exact fictional product/habit scope", tuple(item.id for item in items)),),
            items, "synthetic-exact-product-habit-v1")


def _candidate(identity, name, scope, requirements, money, publisher, reference, quote, attribution):
    claims = tuple(Claim(key, value, kind, scope) for key, value, kind in requirements)
    claims += (Claim("financial", money, "price", scope, specific=True),)
    version_id = "30000000" + identity[8:]
    source = EvidenceVersion(version_id, identity, {
        "version_id": version_id, "publisher": publisher, "source_reference": reference, "source_language": "en",
        "supporting_quote": quote, "reviewed_at": FIXTURE_TIME.isoformat(),
        "review_basis": "synthetic test metadata, not factual review",
        "publication_date": None, "retrieved_at": None, "data_period": None,
        "scope": scope, "competent_claims": [claim.key for claim in claims],
        "assertions": {claim.key: value_data(claim.value) for claim in claims},
        "attribution": attribution, "synthetic": True,
    })
    return Candidate(identity, name, (source,), claims)


def candidates():
    return (
        _candidate(PRODUCT_ID, "Reused laptop (synthetic product)", {"country_code": "CH"},
            (("relevance", "laptop", "specification"), ("applicability", True, "availability"),
                ("secondhand", True, "specification")),
            Money("240.00", "CHF", "secondhand laptop", "once", "fictional item price",
                charges_known=False, exclusions=("delivery", "accessories")),
            "Fictional laptop retailer", "synthetic:secondhand-laptop-v1",
            "Fictional test listing: a secondhand laptop for delivery to CH, CHF 240.00 per secondhand laptop. "
            "Delivery and accessories excluded; no real offer or stock claim.", "retailer-stated"),
        _candidate(HABIT_ID, "Refill an existing bottle (synthetic habit)",
            {"country_code": "CH", "conditions": ["existing_bottle", "potable_tap_water"]},
            (("relevance", "drinking_water", "specification"), ("applicability", True, "specification"),
                ("action:refill", True, "specification"), ("existing_bottle", True, "specification"),
                ("potable_tap_water", True, "specification"), ("avoid_bottled_water", True, "specification")),
            Money("0.10", "CHF", "refill", "once", "hypothetical flat charge per refill",
                charges_known=False, exclusions=("bottle purchase", "cleaning")),
            "Fictional refill guide", "synthetic:bottle-refill-habit-v1",
            "Fictional habit example in CH: refill an existing bottle with potable tap water instead of buying bottled water, "
            "conditional on an existing bottle and potable tap water. Hypothetical flat charge CHF 0.10 per refill; "
            "bottle purchase and cleaning excluded. No bottle capacity, local water quality, real tariff or environmental advantage is established.",
            "provider-stated"),
    )


class ExactKnowledge:
    def retrieve(self, interpretation, submission):
        identity = {"laptop": PRODUCT_ID, "drinking_water": HABIT_ID}[interpretation.subject]
        return tuple(candidate for candidate in candidates() if candidate.alternative_id == identity)


class ExactRenderer(SyntheticRenderer):
    def prepare(self, interpretation, retrieved):
        self._english(interpretation)
        wording = {
            PRODUCT_ID: ("Fictional secondhand laptop product listing for delivery to CH.",
                "This fictional used laptop has a CHF 240.00 item price; delivery and accessories are excluded. "
                "No real offer, stock, total cost, saving or environmental advantage is established."),
            HABIT_ID: ("Fictional bottle-refilling habit using an existing bottle and potable tap water.",
                "Conditional fictional example: CHF 0.10 is a hypothetical flat charge per refill; bottle purchase and cleaning are excluded. "
                "This does not confirm local tap-water quality or availability, a real tariff, savings or an environmental advantage."),
        }
        prepared = []
        for result in retrieved:
            identity = result.candidate.alternative_id
            description, explanation = wording[identity]
            snapshot = {**result.snapshot, "description": description, "explanation": explanation,
                "rendering": {"language": "en", "version": f"synthetic-{identity[-3:]}-en-v1",
                    "review_basis": "synthetic test fixture, not qualified linguistic review"},
                "limitations": ["Fictional fixture only; no factual or linguistic approval.",
                    "Fixture clock: 2026-10-15T10:00:00+00:00; not current factual validation."], "synthetic": True}
            if identity == HABIT_ID:
                snapshot["presentation"] = {
                    "financial": "Fictional quoted charge: CHF 0.10 per refill; period: once; basis: hypothetical flat charge per refill. Excludes bottle purchase and cleaning.",
                    "total_cost": "Unknown; bottle purchase, cleaning and other charges are not zero.",
                    "difference": "Unknown; no supported savings.", "baseline": "Unspecified.",
                    "environmental": "Unknown; no supported environmental advantage.",
                    "availability": "Unknown; no local water quality or availability established.",
                    "geographic_scope": "CH; conditional on an existing bottle and potable tap water.",
                    "conditions": "Requires an existing bottle and potable tap water, and replaces buying bottled water; no local tap-water quality or availability is confirmed.",
                }
            prepared.append(PreparedOption(identity, result.candidate.display_name, snapshot, result.evidence_version_ids))
        return tuple(prepared)


def create_service(path, store=None, clock=None):
    store = store or SQLiteComparisonStore(path)
    store.seed_test_knowledge(candidates())
    return CompareRequest(ExactInterpreter(), ExactKnowledge(), ExactRenderer(), store, clock or (lambda: FIXTURE_TIME),
        countries=LocalCountryCatalogue())
