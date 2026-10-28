"""Isolated synthetic source/review substitutes; no real linguistic approval."""
from dataclasses import replace

from app.application.comparisons import CompareRequest, digest
from app.application.rendering import SourceBoundRenderer, rendering_material
from app.domain.qualification import Claim, Money, qualify, value_data
from app.infrastructure.sqlite_comparisons import SQLiteComparisonStore
from tests.support.synthetic import FIXTURE_TIME, SyntheticInterpreter, SyntheticRenderer, candidates


def candidate():
    original = candidates()[0]
    identity = "00000000-0000-4000-8000-000000000120"
    money = Money("120.00", "CHF", "workshop labour hour", "once", "hourly repair rate; not a complete repair quote")
    claims = tuple(Claim(c.key, money if c.key == "financial" else c.value, c.kind, c.scope, c.specific) for c in original.claims)
    source = replace(original.evidence[0], alternative_id=identity,
        version_id="30000000-0000-4000-8000-000000000120", snapshot={
            **original.evidence[0].snapshot, "version_id": "30000000-0000-4000-8000-000000000120",
            "publisher": "Synthetic hourly provider", "source_reference": "https://synthetic.example.invalid/hourly-repair-v1", "source_language": "de",
            "supporting_quote": "Synthetische Reparatur ohne Ersatz in CH; CHF 120.00 pro Arbeitsstunde. Kosten und Verfügbarkeit unklar.",
            "assertions": {c.key: value_data(c.value) for c in claims},
        })
    return replace(original, alternative_id=identity, display_name="Hourly repair (synthetic)", evidence=(source,), claims=claims)


TEXT = {
    "de": ("Synthetische Veloreparatur.", "Synthetische Anbieterangabe; nur die Testwerkstatt in CH. Umfang und Materialkosten mit dem Testbetrieb klären.",
        "Synthetische Anbieterangabe: CHF 120.00 pro Arbeitsstunde; kein Gesamtpreis.", "Unbekannt; Material, Steuern und weitere Kosten sind nicht null.",
        "Unbekannt; keine belegte Ersparnis.", "Nicht angegeben.", "Unbekannt; kein belegter Umweltvorteil.",
        "Unbekannt; kein garantierter Termin oder Reparaturerfolg.", "CH; nur die synthetische Testwerkstatt, kein Abholservice belegt.",
        "Synthetische Bedingungen: Umfang, Material und Abrechnung klären; keine Garantie für alle Velos."),
    "fr": ("Réparation de vélo synthétique.", "Déclaration du prestataire synthétique ; uniquement l’atelier de test en CH. Confirmer les travaux et le matériel avec l’atelier.",
        "Tarif déclaré par le prestataire synthétique : CHF 120.00 par heure de main-d’œuvre ; ce n’est pas un prix total.", "Inconnu ; matériel, taxes et autres frais ne valent pas zéro.",
        "Inconnue ; aucune économie établie.", "Non précisée.", "Inconnu ; aucun avantage environnemental établi.",
        "Inconnue ; aucun rendez-vous ni résultat garanti.", "CH ; uniquement l’atelier synthétique, aucun enlèvement établi.",
        "Conditions synthétiques : confirmer travaux, matériel et facturation ; aucune garantie pour tous les vélos."),
    "it": ("Riparazione sintetica di biciclette.", "Dichiarazione del fornitore sintetico; solo l’officina di prova in CH. Chiarire lavori e materiali con l’officina.",
        "Tariffa dichiarata dal fornitore sintetico: CHF 120.00 per ora di manodopera; non è un prezzo totale.", "Sconosciuto; materiali, imposte e altri costi non sono zero.",
        "Sconosciuta; nessun risparmio comprovato.", "Non specificata.", "Sconosciuto; nessun vantaggio ambientale comprovato.",
        "Sconosciuta; nessun appuntamento o risultato garantito.", "CH; solo l’officina sintetica, nessun ritiro comprovato.",
        "Condizioni sintetiche: chiarire lavori, materiali e fatturazione; nessuna garanzia per tutte le biciclette."),
    "en": ("Synthetic bicycle repair.", "Synthetic provider statement; only the CH test workshop. Check work and materials with the test branch.",
        "Synthetic provider-stated rate: CHF 120.00 per labour hour; not a total repair price.", "Unknown; materials, tax and other charges are not zero.",
        "Unknown; no supported savings.", "Unspecified.", "Unknown; no supported environmental advantage.",
        "Unknown; no guaranteed appointment or repair outcome.", "CH; synthetic workshop only, no collection service established.",
        "Synthetic conditions: confirm work, materials and billing; no all-bicycle guarantee."),
}
FIELDS = ("financial", "total_cost", "difference", "baseline", "environmental", "availability", "geographic_scope", "conditions")


def reviewed_artifacts():
    from tests.support.synthetic import EXAMPLE
    from app.domain.interpretation import apply_language_policy
    result = qualify(candidate(), apply_language_policy(SyntheticInterpreter().interpret(EXAMPLE), {}), {"country_code": "CH"}, FIXTURE_TIME)
    artifacts = []
    for language, (description, explanation, *values) in TEXT.items():
        artifact = {"alternative_id": candidate().alternative_id, "language": language, "version": f"synthetic-hourly-{language}-v1",
            "runtime_use": True, "evidence_version_ids": list(result.evidence_version_ids),
            "material_sha256": digest(rendering_material(result)),
            "content": {"description": description, "explanation": explanation, "presentation": dict(zip(FIELDS, values, strict=True))}}
        reviewer = {"reviewer": "synthetic reviewer", "qualified": True, "reviewed_at": FIXTURE_TIME.isoformat(),
            "basis": "synthetic test substitute; no qualified human review"}
        artifact["review"] = {"status": "approved", "synthetic": True, "artifact_sha256": digest(artifact),
            "source": {**reviewer, "languages": ["de"]}, "target": {**reviewer, "languages": [language]}}
        artifacts.append(artifact)
    return artifacts


def create_service(path, artifacts=None, store=None):
    store = store or SQLiteComparisonStore(path)
    store.seed_test_knowledge((candidate(),))

    class Knowledge:
        def retrieve(self, interpretation, submission):
            return (candidate(),)

    return CompareRequest(SyntheticInterpreter(), Knowledge(),
        SourceBoundRenderer(reviewed_artifacts() if artifacts is None else artifacts,
            allow_synthetic_reviews=True, coverage_renderer=SyntheticRenderer(), clock=lambda: FIXTURE_TIME),
        store, lambda: FIXTURE_TIME)


HOURLY_EXAMPLE = "Synthetic hourly bicycle repair"
PENDING_EXAMPLE = "Synthetic pending bicycle repair"


def create_demo_service(path):
    from app.domain.interpretation import Clause, InterpretationResult, MeaningItem, OriginalSpan, Recognition
    from tests.support.synthetic import create_service as legacy_service

    legacy = legacy_service(path)
    hourly = create_service(path, store=legacy.store)

    class FixedInterpreter:
        def interpret(self, text):
            if text not in (HOURLY_EXAMPLE, PENDING_EXAMPLE):
                raise AssertionError("Exact synthetic rendering fixtures only")
            items = tuple(MeaningItem(kind, kind, value, OriginalSpan(text.index(word), text.index(word) + len(word), word))
                for kind, value, word in (("subject", "bicycle", "bicycle"), ("action", "repair", "repair")))
            return InterpretationResult(text, Recognition("unknown", None, "synthetic-test-only"), "understood",
                (Clause(OriginalSpan(0, len(text), text), "understood", "synthetic bicycle repair", tuple(i.id for i in items)),),
                items, "synthetic-test-only")

    hourly = replace(hourly, interpreter=FixedInterpreter())
    drafts = reviewed_artifacts()
    for artifact in drafts:
        artifact["review"]["status"] = "pending"
    pending = replace(hourly, renderer=SourceBoundRenderer(drafts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME))

    class Demo:
        store = legacy.store

        def execute(self, submission):
            service = {HOURLY_EXAMPLE: hourly, PENDING_EXAMPLE: pending}.get(submission.text, legacy)
            return service.execute(submission)

    return Demo()
