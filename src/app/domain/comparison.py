from dataclasses import dataclass
from typing import Any, Iterable
from unicodedata import normalize
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.qualification import Claim, Money


@dataclass(frozen=True)
class QuotedConstraint:
    value: str
    quote: str


@dataclass(frozen=True)
class Interpretation:
    subject: str
    constraints: tuple[QuotedConstraint, ...]
    request_language: str | None
    explanation_language: str
    language_origin: str
    version: str
    goals: tuple[str, ...] = ()
    baseline: "Money | None" = None
    budget: "Money | None" = None
    provenance: dict[str, Any] | None = None
    subjects: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceVersion:
    version_id: str
    alternative_id: str
    snapshot: dict[str, Any]


@dataclass(frozen=True)
class Candidate:
    alternative_id: str
    display_name: str
    evidence: tuple[EvidenceVersion, ...]
    claims: tuple["Claim", ...] = ()


@dataclass(frozen=True)
class PreparedOption:
    alternative_id: str
    display_name: str
    snapshot: dict[str, Any]
    evidence_version_ids: tuple[str, ...]


def display_order(options: Iterable[PreparedOption]) -> tuple[PreparedOption, ...]:
    return tuple(sorted(options, key=lambda item: (
        normalize("NFKC", item.display_name).casefold(), item.alternative_id,
    )))
