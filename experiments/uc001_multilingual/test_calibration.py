import unittest
from prototype import interpret, extract_evidence, render

class Calibration(unittest.TestCase):
    def test_parallel_request_meaning(self):
        cases = {
            "de": "Ich möchte mein Fahrrad reparieren, ohne es zu ersetzen.",
            "fr": "Je veux réparer mon vélo sans le remplacer.",
            "it": "Vorrei riparare la mia bicicletta senza sostituirla.",
            "en": "I want to repair my bicycle without replacing it.",
        }
        for language, text in cases.items():
            with self.subTest(language=language):
                actual = interpret(text)
                self.assertEqual(actual["status"], "handled")
                self.assertEqual(actual["language"], language)
                self.assertEqual(actual["subject"], "bicycle")
                self.assertEqual(actual["action"], "repair")
                self.assertTrue(actual["no_replacement"])
                self.assertIsNone(actual["budget"])
                self.assertEqual(actual["original"], text)
                self.assertEqual(actual["country"], "CH")

    def test_budget_and_goal(self):
        actual = interpret("Repair my bicycle without replacing it; cheaper; budget 49,90 CHF.")
        self.assertEqual(actual["status"], "handled")
        self.assertEqual(actual["budget"], {"amount": "49.90", "currency": "CHF"})
        self.assertEqual(actual["goal"], "cheaper")

    def test_short_language_preference(self):
        actual = interpret("Velo", preferred="fr", browser="de")
        self.assertEqual(actual["status"], "handled")
        self.assertEqual(actual["language"], "fr")
        self.assertEqual(actual["language_origin"], "user_choice")
        self.assertEqual(actual["country"], "CH")

    def test_ambiguous_amount_and_unknown_clause(self):
        for text in ["Repair my bicycle; budget 1,200 CHF",
                     "Repair my bicycle but retain its waterproofing"]:
            self.assertEqual(interpret(text)["status"], "clarification")

    def test_evidence_rendering(self):
        sources = [
            "Labour 45 CHF per repair; parts excluded.",
            "Arbeit 45 CHF pro Reparatur; Teile ausgeschlossen.",
            "Main-d’œuvre 45 CHF par réparation; pièces exclues.",
            "Manodopera 45 CHF per riparazione; ricambi esclusi.",
        ]
        for source in sources:
            evidence = extract_evidence(source)
            self.assertEqual(evidence["status"], "handled")
            self.assertEqual(evidence["amount"], "45")
            self.assertEqual(evidence["currency"], "CHF")
            self.assertEqual(evidence["exclusions"], ["parts"])
            for language in ["de", "fr", "it", "en"]:
                result = render(evidence, language)
                self.assertEqual(result["status"], "handled")
                self.assertIn("45", result["text"])
                self.assertIn("CHF", result["text"])
                self.assertEqual(result["exclusions"], ["parts"])
                self.assertEqual(result["original_evidence"], source)
                self.assertEqual(result["derivation"], "template")

    def test_untemplated_condition_abstains(self):
        evidence = extract_evidence("Only non-electric bicycles; collection excluded.")
        self.assertEqual(evidence["status"], "unsupported")
        self.assertEqual(render(evidence, "fr")["status"], "unsupported")

if __name__ == "__main__":
    unittest.main()
