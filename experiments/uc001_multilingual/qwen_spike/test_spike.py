import unittest
from evaluate_model import validate, semantic_score

class SpikeChecks(unittest.TestCase):
    def base(self):
        return {"status":"understood","language":"en",
                "subject":{"value":"bicycle","quote":"bicycle","start":10,"end":17},
                "action":{"value":"repair","quote":"Repair","start":0,"end":6},
                "goals":[],"constraints":[{"kind":"no_replacement","value":"true",
                "quote":"without replacement","start":18,"end":37}],"unresolved":[]}
    def test_valid_quote_is_only_structural(self):
        self.assertEqual(validate(self.base(),"Repair my bicycle without replacement"),[])
    def test_bad_offset_rejected(self):
        obj=self.base();obj["subject"]["start"]=0
        self.assertTrue(validate(obj,"Repair my bicycle without replacement"))
    def test_reversed_negation_is_semantic_error_even_with_valid_spans(self):
        obj=self.base();obj["constraints"][0]["value"]="false"
        self.assertEqual(validate(obj,"Repair my bicycle without replacement"),[])
        self.assertEqual(semantic_score(obj,{"subject":"bicycle","action":"repair","goals":[],
                         "constraints":{"no_replacement":"true"}})["category"],"incorrect")
    def test_missing_constraint_is_semantic_error(self):
        obj=self.base();obj["constraints"]=[]
        self.assertEqual(semantic_score(obj,{"subject":"bicycle","action":"repair","goals":[],
                         "constraints":{"no_replacement":"true"}})["category"],"incorrect")
    def test_rejected_partial_fields_cannot_be_accepted(self):
        obj=self.base();obj["status"]="clarification"
        self.assertEqual(semantic_score(obj,{"subject":"bicycle","action":"repair","goals":[],
                         "constraints":{"no_replacement":"true"}})["category"],"abstention")
    def test_explicit_unknown_goal_stays_missing(self):
        obj=self.base();obj["goals"]=[{"value":"cheaper","quote":"Repair","start":0,"end":6}]
        self.assertEqual(semantic_score(obj,{"subject":"bicycle","action":"repair","goals":[],
                         "constraints":{"no_replacement":"true"}})["category"],"incorrect")

if __name__=="__main__":
    unittest.main()
