import json
import tempfile
import unittest
from pathlib import Path
from detector.evaluate_motion import evaluate, summarize
from motion_audit_test import sample

class EvaluationTests(unittest.TestCase):
    def run_samples(self, samples):
        with tempfile.TemporaryDirectory() as d:
            paths=[]
            for i,s in enumerate(samples):
                p=Path(d)/f'{i}.json';p.write_text(json.dumps(s));paths.append(p)
            return evaluate(paths,lambda s: {'status':'experimental','real_reference_score':.2})

    def test_labeled_copy_preferred_over_unknown(self):
        a=sample();a['label']='unknown'
        r=self.run_samples([a,sample()])
        self.assertEqual(r['summary']['status_counts'],{'duplicate':1,'scored':1})

    def test_conflicting_labels_not_scored(self):
        a=sample();a['label']='ai'
        r=self.run_samples([a,sample()])
        self.assertEqual(r['summary']['status_counts'],{'label_conflict':2})

    def test_single_class_has_no_ranking(self):
        self.assertIsNone(self.run_samples([sample()])['summary']['pairwise_ranking'])

    def test_ranking_counts_ties_and_reversed_pairs(self):
        rows=[dict(status='scored',label=l,score=s) for l,s in [('real',.1),('real',.5),('ai',.1),('ai',.3)]]
        r=summarize(rows)
        self.assertEqual(r['correctly_ordered_pairs'],2)
        self.assertEqual(r['tied_pairs'],1)
        self.assertEqual(r['pairwise_ranking'],.625)
