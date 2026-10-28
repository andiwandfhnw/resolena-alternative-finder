from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
import json
from typing import Any
import unicodedata

from app.domain.comparison import Candidate, EvidenceVersion, Interpretation


WINDOWS = {"price": 1, "availability": 1, "service_coverage": 90,
    "specification": 365, "environmental": 365}


@dataclass(frozen=True)
class Money:
    amount: str
    currency: str
    unit: str
    period: str
    basis: str
    charges_known: bool = False
    exclusions: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    price_basis: str = "quoted"

    def __post_init__(self):
        try:
            valid = isinstance(self.amount, str) and Decimal(self.amount).is_finite() and Decimal(self.amount) >= 0
        except InvalidOperation:
            valid = False
        if not valid or not all((self.currency, self.unit, self.period, self.basis)):
            raise ValueError("Exact nonnegative amount, source currency, unit, period and basis required")


def cost_difference(alternative: Money | None, baseline: Money | None) -> str | None:
    if alternative is None or baseline is None:
        return None
    if not alternative.charges_known or not baseline.charges_known:
        return None
    if any(getattr(alternative, key) != getattr(baseline, key) for key in ("currency", "unit", "period", "basis", "exclusions")):
        return None
    with localcontext() as context:
        context.prec = max(len(alternative.amount), len(baseline.amount)) * 2 + 10
        return format(Decimal(baseline.amount) - Decimal(alternative.amount), "f")


@dataclass(frozen=True)
class Claim:
    key: str
    value: Any
    kind: str
    scope: dict[str, Any]
    specific: bool = False
    comparative: bool = False
    inputs: tuple["Claim", ...] = ()


@dataclass(frozen=True)
class Qualification:
    candidate: Candidate
    qualified: bool
    snapshot: dict[str, Any]
    evidence_version_ids: tuple[str, ...]
    limitation_codes: tuple[str, ...] = ()


def instant(value: Any) -> datetime | None:
    if not isinstance(value, str) or "T" not in value or len(value.split("T")[1].split("+")[0]) < 8:
        return None
    try:
        result = datetime.fromisoformat(value)
        return result if result.tzinfo is not None else None
    except ValueError:
        return None


def value_data(value):
    return json.loads(json.dumps(asdict(value))) if isinstance(value, Money) else value


def assess_claim(claim: Claim, evidence: tuple[EvidenceVersion, ...], now: datetime) -> dict[str, Any]:
    if now.tzinfo is None:
        raise ValueError("Assessment requires an unambiguous clock")
    sources = []
    inputs = [assess_claim(item, evidence, now) for item in claim.inputs]
    for version in evidence:
        source = version.snapshot
        if not all(source.get(key) for key in ("publisher", "source_reference", "supporting_quote", "review_basis", "attribution")):
            continue
        if claim.key not in source.get("competent_claims", ()) or claim.key not in source.get("assertions", {}):
            continue
        if source.get("scope") != claim.scope:
            continue
        if claim.comparative:
            if not all(source.get(key) for key in ("method", "baseline", "assumptions")):
                continue
        if claim.comparative and (not inputs or any(item["support"] != "supported" for item in inputs)):
            continue
        sources.append(version)
    matching = [v for v in sources if v.snapshot["assertions"][claim.key] == value_data(claim.value)]
    support = "missing" if not matching else "disputed" if len(matching) != len(sources) else "supported"
    fresh_states = []
    for version in sources:
        source = version.snapshot
        reviewed = instant(source.get("reviewed_at"))
        days = WINDOWS.get(claim.kind)
        if reviewed is None or days is None or reviewed > now:
            fresh_states.append("unverified")
            continue
        expiry = reviewed + timedelta(days=days)
        uncertain = False
        for key in ("expires_at", "invalidated_at"):
            if source.get(key) is not None:
                bound = instant(source[key])
                if bound is None:
                    uncertain = True
                else:
                    expiry = min(expiry, bound)
        period_not_applicable = source.get("data_period_required") is False and bool(source.get("data_period_not_applicable_reason"))
        temporal = (claim.kind == "environmental" and not period_not_applicable) or source.get("data_period_required", False)
        if temporal and not (source.get("data_period") and source.get("temporal_applicability_reviewed") is True):
            uncertain = True
        fresh_states.append("expired" if now >= expiry else "unverified" if uncertain else "fresh")
    freshness = "fresh" if fresh_states and all(s == "fresh" for s in fresh_states) else "expired" if "expired" in fresh_states else "unverified"
    if inputs and any(item["freshness"] != "fresh" for item in inputs):
        freshness = "expired" if any(item["freshness"] == "expired" for item in inputs) else "unverified"
    return {"claim": claim.key, "support": support, "freshness": freshness,
        "requirement": "not_applicable", "attribution": sorted({v.snapshot["attribution"] for v in sources}),
        "checked_at": [v.snapshot.get("reviewed_at") for v in sources],
        "independent_verification": bool(sources) and all(v.snapshot.get("attribution") == "independently reviewed" for v in sources),
        "evidence_version_ids": sorted({v.version_id for v in sources} | {identity for item in inputs for identity in item["evidence_version_ids"]})}


def qualify(candidate: Candidate, interpretation: Interpretation, location: dict[str, Any], now: datetime) -> Qualification:
    claims = {claim.key: claim for claim in candidate.claims}
    if len(claims) != len(candidate.claims):
        raise ValueError("Duplicate claim identity")
    evidence = tuple(v for v in candidate.evidence if v.alternative_id == candidate.alternative_id)
    labels = {key: assess_claim(claim, evidence, now) for key, claim in claims.items()}

    def applicable(scope, *, geographic_coverage=False):
        if scope.get("country_code") != location["country_code"] and scope.get("global") is not True:
            return False
        conditions = scope.get("conditions", ())
        if isinstance(conditions, str):
            conditions = (conditions,)
        if any(condition not in {c.value for c in interpretation.constraints} for condition in conditions):
            return False
        if scope.get("town") or scope.get("postcode"):
            if not scope.get("locality_identity_unambiguous"):
                return False
            for key in ("town", "postcode"):
                if not location.get(key):
                    continue
                intended = location[key].strip()
                supported = scope.get(key)
                if not isinstance(supported, str):
                    return False
                supported = supported.strip()
                if key == "town":
                    intended = unicodedata.normalize("NFC", intended).casefold()
                    supported = unicodedata.normalize("NFC", supported).casefold()
                if intended != supported:
                    return False
        elif geographic_coverage and any(location.get(key) for key in ("town", "postcode")):
            if scope.get("country_wide") is not True:
                return False
        return True

    def usable(key):
        if key not in claims:
            return False
        label = labels.get(key, {})
        claim = claims[key]
        return (label.get("support") == "supported" and label.get("freshness") == "fresh"
            and applicable(claim.scope, geographic_coverage=key == "applicability")
            and all(applicable(item.scope, geographic_coverage=key == "applicability") for item in claim.inputs))

    required = {"relevance": interpretation.subject, "applicability": True,
        **{f"action:{action}": True for action in interpretation.actions},
        **{c.value: True for c in interpretation.constraints},
        **{goal: True for goal in interpretation.goals if goal != "cheaper"}}
    passed = True
    for key, expected in required.items():
        claim = claims.get(key)
        satisfaction = "unverified"
        if usable(key):
            satisfaction = "satisfied" if type(claim.value) is type(expected) and claim.value == expected else "contradicted"
        labels.setdefault(key, {"claim": key, "support": "missing", "freshness": "unverified", "evidence_version_ids": []})["requirement"] = satisfaction
        passed &= satisfaction == "satisfied"

    price = claims.get("financial")
    money = price.value if price and isinstance(price.value, Money) and usable("financial") and price.specific else None
    difference = cost_difference(money, interpretation.baseline)
    calculations = []
    def cost_label(key, difference, strict):
        satisfied = difference is not None and (Decimal(difference) > 0 if strict else Decimal(difference) >= 0)
        calculations.append({"claim": key, "support": "supported" if difference is not None else "missing",
            "freshness": labels.get("financial", {}).get("freshness", "unverified"),
            "requirement": "satisfied" if satisfied else "contradicted" if difference is not None else "unverified",
            "evidence_version_ids": labels.get("financial", {}).get("evidence_version_ids", []),
            "method": "baseline minus alternative using exact decimals on identical currency/unit/period/basis/exclusions",
            "difference": difference, "baseline_provenance": "user-reported"})
        return satisfied
    if "cheaper" in interpretation.goals:
        passed &= cost_label("cheaper", difference, True)
    if interpretation.budget is not None:
        budget_difference = cost_difference(money, interpretation.budget)
        passed &= cost_label("budget", budget_difference, False)
    environment = claims.get("environmental")
    useful_environment = environment is not None and environment.specific and usable("environmental")
    passed &= money is not None or useful_environment
    used = set()
    public_claims = []
    for key, label in labels.items():
        if key in required or usable(key):
            public_claims.append({**label, **({"value": value_data(claims[key].value)} if usable(key) else {})})
            if usable(key):
                used.update(label["evidence_version_ids"])
    snapshot = {
        "claims": public_claims + calculations,
        "financial": {**asdict(money), "status": "supported", "total_cost": money.amount if money.charges_known and money.basis == "total" and not money.exclusions else None,
            "difference": difference, "baseline": asdict(interpretation.baseline) if interpretation.baseline else None,
            "baseline_provenance": "user-reported" if interpretation.baseline else None} if money else {
                "status": "unknown", "amount": None, "difference": None, "total_cost": None,
                "baseline": asdict(interpretation.baseline) if interpretation.baseline else None,
                "baseline_provenance": "user-reported" if interpretation.baseline else None},
        "environmental": {"status": "supported", "explanation": environment.value} if useful_environment else {"status": "unknown", "explanation": "No supported environmental/resource information."},
        "availability": {"status": "provider-stated" if usable("availability") else "unknown", "value": claims["availability"].value if usable("availability") else None},
        "evidence": [v.snapshot for v in evidence if v.version_id in used],
        "geographic_scope": claims["applicability"].scope if "applicability" in claims else None,
    }
    limitations = set()
    for key in required:
        label = labels[key]
        if label["requirement"] != "satisfied":
            if label["freshness"] == "expired":
                limitations.add("essential_evidence_expired")
            if label["freshness"] == "unverified":
                limitations.add("essential_freshness_unverified")
            if label["support"] in ("missing", "disputed"):
                limitations.add("essential_support_unverified")
            if label["requirement"] == "contradicted":
                limitations.add("requirement_contradicted")
            if key == "applicability":
                limitations.add("geographic_applicability_unverified")
    if money is None and not useful_environment:
        limitations.add("useful_comparison_information_missing")
    if any(label["requirement"] != "satisfied" for label in calculations):
        limitations.add("cost_requirement_not_established")
    return Qualification(candidate, bool(passed), snapshot, tuple(sorted(used)), tuple(sorted(limitations)))
