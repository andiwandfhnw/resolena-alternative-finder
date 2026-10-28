"""Prepared synthetic coverage evidence; no factual locality or provider review."""
from dataclasses import replace

from app.domain.qualification import value_data
from tests.support.synthetic import candidates


def candidate(scope=None):
    scope = {"country_code": "CH", "country_wide": True} if scope is None else scope
    original = candidates()[0]
    identity = "00000000-0000-4000-8000-000000000540"
    version_id = "30000000-0000-4000-8000-000000000540"
    claims = tuple(replace(claim, scope=scope) for claim in original.claims)
    quote = (
        "Fictional test provider explicitly offers bicycle repair without replacement throughout CH, "
        "including all towns and postcodes, with no narrower locality condition. "
        "Labour CHF 45.00 per repair; parts excluded. This is not a real service, locality verification or availability guarantee."
        if scope == {"country_code": "CH", "country_wide": True} else
        f"Fictional test provider expressly supports bicycle repair without replacement under this independently prepared geographic scope: {scope}. "
        "Labour CHF 45.00 per repair; parts excluded. No real service or locality verification."
    )
    source = replace(original.evidence[0], alternative_id=identity, version_id=version_id,
        snapshot={**original.evidence[0].snapshot, "version_id": version_id,
            "publisher": "Fictional explicit-coverage repair provider",
            "source_reference": "synthetic:explicit-locality-coverage-v1", "scope": scope,
            "supporting_quote": quote,
            "competent_claims": [claim.key for claim in claims],
            "assertions": {claim.key: value_data(claim.value) for claim in claims}})
    return replace(original, alternative_id=identity, display_name="Explicit coverage repair (synthetic)",
        claims=claims, evidence=(source,))
