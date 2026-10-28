"""Isolated stdlib feasibility probe; synthetic lexicon, not production NLP."""
import re
import unicodedata
from decimal import Decimal

LANGUAGES = ("de", "fr", "it", "en")
SUBJECTS = {"bicycle", "bike", "fahrrad", "velo", "vélo", "bicicletta", "bici"}
ACTIONS = {"repair", "reparieren", "repariere", "reparatur", "réparer", "riparare"}
GOALS = {"cheaper", "günstiger", "moins cher", "più economico"}
FILLER = set("i want to my it please make ich möchte mein bitte es zu je veux mon le la vorrei mia".split())
MARKERS = {
    "de": {"ich", "möchte", "fahrrad", "reparieren", "repariere", "reparatur", "ohne", "ersatz", "günstiger"},
    "fr": {"je", "veux", "mon", "vélo", "réparer", "sans", "remplacement", "remplacer"},
    "it": {"vorrei", "mia", "bicicletta", "bici", "riparare", "senza", "sostituirla", "sostituzione"},
    "en": {"i", "want", "my", "bicycle", "bike", "repair", "without", "replacing", "replacement", "cheaper"},
}
NEGATION = re.compile(
    r"\b(?:without (?:replacing it|replacement)|ohne (?:es zu ersetzen|ersatz)|"
    r"sans (?:le remplacer|remplacement)|senza (?:sostituirla|sostituzione))\b")
BUDGET = re.compile(
    r"\b(?:budget|maximum|maximal|max|massimo|bis zu|jusqu'à|fino a|up to)"
    r"\s+(\d+(?:[.,]\d+)?)\s+(chf|eur|usd)\b")
SOURCE_PATTERNS = {
    "en": r"labour (AMOUNT) (CURRENCY) per repair; parts excluded[.]?",
    "de": r"arbeit (AMOUNT) (CURRENCY) pro reparatur; teile ausgeschlossen[.]?",
    "fr": r"main-d[’']œuvre (AMOUNT) (CURRENCY) par réparation; pièces exclues[.]?",
    "it": r"manodopera (AMOUNT) (CURRENCY) per riparazione; ricambi esclusi[.]?",
}
TEMPLATES = {
    "de": "Angegebene Arbeit: {amount} {currency} pro Reparatur; Teile ausgeschlossen.",
    "fr": "Main-d’œuvre indiquée: {amount} {currency} par réparation; pièces exclues.",
    "it": "Manodopera dichiarata: {amount} {currency} per riparazione; ricambi esclusi.",
    "en": "Stated labour: {amount} {currency} per repair; parts excluded.",
}

def normalize(text):
    return unicodedata.normalize("NFC", text).casefold()

def words(text):
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", text, flags=re.UNICODE)

def amount(value):
    fraction = re.split(r"[.,]", value)
    if len(fraction) > 1 and len(fraction[1]) == 3:
        return None
    return str(Decimal(value.replace(",", ".")))

def interpret(text, country="CH", preferred=None, browser=None):
    raw = normalize(text)
    tokens = set(words(raw))
    result = {"original": text, "country": country, "subject": None, "action": None,
              "goal": None, "no_replacement": False, "budget": None,
              "language": None, "language_origin": None}
    if tokens & {"quiero", "bicicleta", "reemplazarla", "nöd", "sött"}:
        return dict(result, status="unsupported", reason="language_capability")
    detected = [lang for lang, markers in MARKERS.items() if tokens & markers]
    if len(detected) == 1:
        result.update(language=detected[0], language_origin="detected")
    else:
        selected = preferred if preferred in LANGUAGES else browser
        if selected in LANGUAGES:
            result.update(language=selected,
                          language_origin="user_choice" if selected == preferred else "browser_preference")
    found_budgets = list(BUDGET.finditer(raw))
    if len(found_budgets) > 1:
        return dict(result, status="clarification", reason="multiple_budget_scopes")
    if found_budgets:
        value = amount(found_budgets[0][1])
        if value is None:
            return dict(result, status="clarification", reason="ambiguous_amount")
        result["budget"] = {"amount": value, "currency": found_budgets[0][2].upper()}
        raw = BUDGET.sub(" ", raw)
    result["no_replacement"] = bool(NEGATION.search(raw))
    raw = NEGATION.sub(" ", raw)
    for phrase in sorted(GOALS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(phrase) + r"\b", raw):
            result["goal"] = "cheaper"
            raw = re.sub(r"\b" + re.escape(phrase) + r"\b", " ", raw)
    residual = set(words(raw))
    if residual & SUBJECTS:
        result["subject"] = "bicycle"
    if residual & ACTIONS:
        result["action"] = "repair"
    unknown = sorted(residual - SUBJECTS - ACTIONS - FILLER)
    if unknown:
        return dict(result, status="clarification", reason="unmapped_meaning", unresolved=unknown)
    if result["subject"] is None:
        return dict(result, status="clarification", reason="subject_not_interpreted")
    if result["language"] is None:
        return dict(result, status="clarification", reason="explanation_language")
    return dict(result, status="handled")

def extract_evidence(text):
    raw = normalize(text)
    for lang, pattern in SOURCE_PATTERNS.items():
        pattern = pattern.replace("AMOUNT", r"\d+(?:[.,]\d+)?").replace("CURRENCY", "chf|eur|usd")
        match = re.fullmatch(pattern, raw)
        if match:
            value = amount(match[1])
            if value is None:
                return {"status": "clarification", "reason": "ambiguous_amount", "original": text}
            return {"status": "handled", "amount": value, "currency": match[2].upper(),
                    "basis": "per_repair_labour", "exclusions": ["parts"], "original": text,
                    "source_language": lang}
    return {"status": "unsupported", "reason": "unprepared_condition", "original": text}

def render(evidence, language):
    if evidence["status"] != "handled" or language not in TEMPLATES:
        return {"status": "unsupported", "reason": "unprepared_rendering"}
    return {"status": "handled", "text": TEMPLATES[language].format(**evidence),
            "amount": evidence["amount"], "currency": evidence["currency"],
            "basis": evidence["basis"], "exclusions": list(evidence["exclusions"]),
            "original_evidence": evidence["original"], "derivation": "template",
            "language": language}
