from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.comparison import Interpretation, QuotedConstraint
from app.domain.qualification import Money


SUPPORTED_LANGUAGES = ("de", "fr", "it", "en")
MEANING_STATES = ("understood", "needs_clarification", "unsupported")
ITEM_KINDS = ("subject", "action", "goal", "constraint", "name", "place", "budget", "baseline", "quantity", "context")


class ContractViolation(ValueError):
    pass


class LanguageOutcome(Exception):
    def __init__(self, outcome: str, code: str, detail: dict[str, Any]):
        self.outcome, self.code, self.detail = outcome, code, detail
        super().__init__(code)


@dataclass(frozen=True)
class OriginalSpan:
    start: int
    end: int
    quote: str

    def validate(self, original: str):
        if (type(self.start) is not int or type(self.end) is not int
                or not 0 <= self.start < self.end <= len(original)
                or original[self.start:self.end] != self.quote):
            raise ContractViolation("Original span changed or has invalid code-point offsets")

    def contains(self, other: "OriginalSpan") -> bool:
        return self.start <= other.start < other.end <= self.end


@dataclass(frozen=True)
class Recognition:
    status: str
    language: str | None
    version: str

    def validate(self):
        if self.status not in ("supported", "unsupported", "mixed", "unknown") or not self.version:
            raise ContractViolation("Invalid original-input language hypothesis")
        if self.status == "supported" and self.language not in SUPPORTED_LANGUAGES:
            raise ContractViolation("Supported hypothesis requires a supported original language")
        if self.status == "mixed" and self.language is not None and self.language not in SUPPORTED_LANGUAGES:
            raise ContractViolation("Mixed primary language must be supported or unknown")
        if self.status in ("unsupported", "unknown") and self.language is not None:
            raise ContractViolation("Unsupported/unknown hypotheses have no supported language")


@dataclass(frozen=True)
class GroundedValue:
    value: str
    span: OriginalSpan


@dataclass(frozen=True)
class Quantity:
    amount: str | None
    number: OriginalSpan
    decimal_separator: str | None = None
    grouping_separator: str | None = None
    currency: GroundedValue | None = None
    unit: GroundedValue | None = None
    period: GroundedValue | None = None
    basis: GroundedValue | None = None
    charges_known: bool = False

    def validate(self, original: str, owner: OriginalSpan):
        self.number.validate(original)
        if not owner.contains(self.number):
            raise ContractViolation("Quantity is outside its meaning item")
        for field in (self.currency, self.unit, self.period, self.basis):
            if field is not None:
                field.span.validate(original)
                if not field.value or not owner.contains(field.span):
                    raise ContractViolation("Quantity context is ungrounded")
        if self.currency is not None and self.currency.value != self.currency.span.quote:
            raise ContractViolation("Source currency was changed")
        if self.amount is None:
            return
        if self.decimal_separator not in (None, ".", ",") or self.grouping_separator not in (None, ".", ",", "'", " ", "\u202f"):
            raise ContractViolation("Invalid explicitly declared numeric reading")
        if self.grouping_separator is not None and self.grouping_separator == self.decimal_separator:
            raise ContractViolation("Ambiguous numeric reading")
        reading = self.number.quote
        if self.grouping_separator is not None:
            reading = reading.replace(self.grouping_separator, "")
        if self.decimal_separator is not None:
            reading = reading.replace(self.decimal_separator, ".")
        try:
            valid = isinstance(self.amount, str) and Decimal(self.amount).is_finite() and Decimal(self.amount) >= 0
        except InvalidOperation:
            valid = False
        if not valid or reading != self.amount:
            raise ContractViolation("Exact magnitude/precision differs from the declared source reading")


@dataclass(frozen=True)
class MeaningItem:
    id: str
    kind: str
    normalized: str | None
    span: OriginalSpan
    negation: OriginalSpan | None = None
    quantity: Quantity | None = None


@dataclass(frozen=True)
class Clause:
    span: OriginalSpan
    meaning_status: str
    normalized: str | None
    item_ids: tuple[str, ...]


@dataclass(frozen=True)
class InterpretationResult:
    original_text: str
    recognition: Recognition
    meaning_status: str
    clauses: tuple[Clause, ...]
    items: tuple[MeaningItem, ...]
    version: str
    message: str | None = None

    def validate(self):
        self.recognition.validate()
        if self.meaning_status not in MEANING_STATES or not self.version:
            raise ContractViolation("Missing meaning state/version")
        if not self.clauses and self.meaning_status == "understood":
            raise ContractViolation("Understood input requires clause coverage")
        items = {item.id: item for item in self.items}
        if len(items) != len(self.items) or any(not item.id for item in self.items):
            raise ContractViolation("Meaning item identities must be unique")
        referenced = []
        position = 0
        for clause in sorted(self.clauses, key=lambda clause: clause.span.start):
            clause.span.validate(self.original_text)
            if clause.meaning_status not in MEANING_STATES:
                raise ContractViolation("Invalid clause meaning state")
            if clause.span.start < position or self.original_text[position:clause.span.start].strip():
                raise ContractViolation("Overlapping or omitted original clause")
            if clause.meaning_status == "understood" and (not clause.normalized or not clause.item_ids):
                raise ContractViolation("Understood clause has no represented meaning")
            for identity in clause.item_ids:
                if identity not in items or not clause.span.contains(items[identity].span):
                    raise ContractViolation("Clause references missing/outside meaning")
            referenced.extend(clause.item_ids)
            position = clause.span.end
        if self.clauses and self.original_text[position:].strip():
            raise ContractViolation("Original trailing clause was omitted")
        if sorted(referenced) != sorted(items):
            raise ContractViolation("Meaning items must each belong to one original clause")
        for item in self.items:
            item.span.validate(self.original_text)
            if item.kind not in ITEM_KINDS:
                raise ContractViolation("Unknown meaning item kind")
            if item.negation is not None:
                item.negation.validate(self.original_text)
                if not item.span.contains(item.negation):
                    raise ContractViolation("Negation is outside its meaning item")
            if item.kind in ("name", "place") and item.normalized != item.span.quote:
                raise ContractViolation("Literal name/place was renamed")
            if item.kind in ("budget", "baseline", "quantity"):
                if item.quantity is None:
                    raise ContractViolation("Quantity meaning has no original number/context")
                item.quantity.validate(self.original_text, item.span)
            elif item.quantity is not None:
                raise ContractViolation("Unexpected quantity outside a typed quantity item")
        if self.meaning_status == "unsupported" and not self.message:
            raise ContractViolation("Capability limitation must explain rephrasing need")


def clarification(code: str, message: str, span: OriginalSpan | None = None, choices: tuple[str, ...] = ()):
    detail = {"message": message, "choices": list(choices)}
    if span is not None:
        detail["span"] = asdict(span)
    raise LanguageOutcome("clarification_required", code, {"clarification": detail})


def _money(items: tuple[MeaningItem, ...], kind: str) -> Money | None:
    values = [item for item in items if item.kind == kind]
    if len(values) > 1:
        clarification("comparison_basis_uncertain", "Clarify the scope of these amounts before comparison.", values[0].span)
    if not values:
        return None
    item = values[0]
    quantity = item.quantity
    if any(getattr(quantity, field) is None for field in ("currency", "unit", "period", "basis")):
        clarification("comparison_basis_uncertain", "Clarify the currency, units, period and cost basis without guessing.", item.span)
    return Money(quantity.amount, quantity.currency.value, quantity.unit.value, quantity.period.value, quantity.basis.value,
        charges_known=kind == "budget" or quantity.charges_known)


def apply_language_policy(result: InterpretationResult, context: dict[str, Any], recognizer_hypothesis: Recognition | None = None) -> Interpretation:
    result.validate()
    if recognizer_hypothesis is not None:
        recognizer_hypothesis.validate()
    unresolved = next((clause for clause in result.clauses if clause.meaning_status != "understood"), None)
    if result.meaning_status == "unsupported" or any(c.meaning_status == "unsupported" for c in result.clauses):
        if not result.message:
            raise ContractViolation("Unsupported clause requires an explicit capability limitation")
        raise LanguageOutcome("interpretation_unavailable", "interpretation_capability_unavailable", {"limitation": result.message})
    if result.meaning_status == "needs_clarification" or unresolved is not None:
        clarification("meaning_uncertain", result.message or "Clarify the indicated meaning before continuing.", unresolved.span if unresolved else None)
    for item in result.items:
        if item.kind in ("action", "goal", "constraint", "quantity") and not item.normalized:
            raise LanguageOutcome("interpretation_unavailable", "requirement_normalization_unavailable", {"limitation": "An explicit requirement could not be preserved. Rephrase the request."})
        if item.quantity is not None and item.quantity.amount is None:
            clarification("amount_uncertain", "Clarify the exact amount; no language or country-based numeric reading was assumed.", item.quantity.number)
    subjects = tuple(item.normalized or item.span.quote for item in result.items if item.kind == "subject")
    if not subjects:
        raise LanguageOutcome("invalid_input", "subject_unclear", {})
    baseline, budget = _money(result.items, "baseline"), _money(result.items, "budget")
    primary = result.recognition.language if result.recognition.status in ("supported", "mixed") else None
    choice = context.get("explanation_language_choice")
    preferred = context.get("preferred_language")
    browser = context.get("browser_language")
    if choice in SUPPORTED_LANGUAGES:
        language, origin = choice, "user_choice"
    elif primary is not None:
        language, origin = primary, "detected"
    elif preferred in SUPPORTED_LANGUAGES:
        language, origin = preferred, "user_choice"
    elif browser in SUPPORTED_LANGUAGES:
        language, origin = browser, "browser_preference"
    else:
        clarification("explanation_language_required", "Sprache wählen / Choisir la langue / Scegli la lingua / Choose a language.", choices=SUPPORTED_LANGUAGES)

    provenance = asdict(result)
    del provenance["original_text"]
    provenance["recognizer_hypothesis"] = asdict(recognizer_hypothesis) if recognizer_hypothesis else None
    provenance["contract_version"] = "uc001-language-v1"
    return Interpretation("; ".join(subjects),
        tuple(QuotedConstraint(item.normalized, item.span.quote) for item in result.items if item.kind in ("constraint", "quantity")),
        primary, language, origin, result.version,
        goals=tuple(item.normalized for item in result.items if item.kind == "goal"), baseline=baseline, budget=budget,
        provenance=provenance, subjects=subjects,
        actions=tuple(item.normalized for item in result.items if item.kind == "action"))
