from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone

from app.application.comparisons import InputOutcome, digest
from app.domain.comparison import PreparedOption
from app.domain.interpretation import SUPPORTED_LANGUAGES
from app.domain.qualification import instant


PRESENTATION_FIELDS = {"financial", "total_cost", "difference", "baseline", "environmental", "availability", "geographic_scope", "conditions"}


def rendering_material(result):
    assessment = {**result.snapshot, "claims": [{k: v for k, v in claim.items() if k != "requirement"}
        for claim in result.snapshot["claims"]]}
    return {"candidate": asdict(result.candidate), "assessment": assessment,
        "evidence_version_ids": list(result.evidence_version_ids)}


def unavailable():
    raise InputOutcome("interpretation_unavailable", "rendering_unavailable", {
        "limitation": "Reviewed wording is unavailable in the selected explanation language. Your fields are preserved."})


class SourceBoundRenderer:
    def __init__(self, artifacts, *, allow_synthetic_reviews=False, coverage_renderer=None, clock=None):
        self.artifacts = deepcopy(artifacts)
        self.allow_synthetic_reviews = allow_synthetic_reviews
        self.coverage_renderer = coverage_renderer
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def prepare(self, interpretation, candidates):
        if interpretation.explanation_language not in SUPPORTED_LANGUAGES:
            unavailable()
        options = []
        for result in candidates:
            if not result.qualified:
                raise ValueError("Rendering requires a qualified candidate")
            matches = [a for a in self.artifacts if a.get("alternative_id") == result.candidate.alternative_id
                and a.get("language") == interpretation.explanation_language]
            if not matches:
                unavailable()
            if len(matches) != 1:
                raise ValueError("Ambiguous rendering version")
            artifact = matches[0]
            self._check(artifact, result)
            options.append(PreparedOption(result.candidate.alternative_id, result.candidate.display_name,
                {**deepcopy(artifact["content"]), "rendering": {"language": artifact["language"], "version": artifact["version"],
                    "derivation": "source-bound paraphrase", "material_sha256": artifact["material_sha256"],
                    "evidence_version_ids": list(result.evidence_version_ids), "review": deepcopy(artifact["review"])}}, result.evidence_version_ids))
        return tuple(options)

    def _check(self, artifact, result):
        review = artifact.get("review") or {}
        if artifact.get("runtime_use") is not True or review.get("status") != "approved":
            unavailable()
        source_languages = {v.snapshot["source_language"] for v in result.candidate.evidence if v.version_id in result.evidence_version_ids}
        source_flags = {v.snapshot.get("synthetic") is True for v in result.candidate.evidence if v.version_id in result.evidence_version_ids}
        synthetic = source_flags == {True}
        if len(source_flags) != 1 or review.get("synthetic") is not synthetic or (synthetic and not self.allow_synthetic_reviews):
            unavailable()
        now = self.clock()
        if now.tzinfo is None:
            raise ValueError("Rendering review requires an unambiguous clock")
        for role, languages in (("source", source_languages), ("target", {artifact["language"]})):
            record = review.get(role) or {}
            reviewed = instant(record.get("reviewed_at"))
            identified = all(isinstance(record.get(key), str) and record[key].strip() for key in ("reviewer", "basis"))
            if record.get("qualified") is not True or not identified or reviewed is None or reviewed > now:
                unavailable()
            if set(record.get("languages", ())) != languages:
                raise ValueError("Review language does not cover the source or target")
        if not isinstance(artifact.get("version"), str) or not artifact["version"].strip():
            raise ValueError("Rendering version is required")
        if artifact.get("material_sha256") != digest(rendering_material(result)) or artifact.get("evidence_version_ids") != list(result.evidence_version_ids):
            raise ValueError("Rendering source binding changed")
        if review.get("artifact_sha256") != digest({k: v for k, v in artifact.items() if k != "review"}):
            raise ValueError("Reviewed wording or version changed")
        content = artifact.get("content", {})
        if set(content) != {"description", "explanation", "presentation"} or set(content["presentation"]) != PRESENTATION_FIELDS:
            raise ValueError("Rendering omitted or replaced required content")
        if not all(isinstance(v, str) and v.strip() for v in (content["description"], content["explanation"], *content["presentation"].values())):
            raise ValueError("Rendering text is incomplete")
        money = result.snapshot["financial"]
        if money.get("amount") is not None and f"{money['currency']} {money['amount']}" not in content["presentation"]["financial"]:
            raise ValueError("Rendering changed protected money")

    def prepare_coverage(self, interpretation, limitation_codes):
        if self.coverage_renderer is None:
            unavailable()
        return self.coverage_renderer.prepare_coverage(interpretation, limitation_codes)
