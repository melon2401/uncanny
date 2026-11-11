import unittest
from detector.compare_hive import parse_score

def response(classes, code='0'):
    return {'status':[{'status':{'code':code},'response':{'output':[{'classes':classes}]}}]}

class HiveTests(unittest.TestCase):
    def test_correct_head(self):
        self.assertEqual(parse_score(response([{'class':'deepfake','score':.99},{'class':'ai_generated','score':.1}])),10)
    def test_failed_task(self):
        with self.assertRaises(ValueError): parse_score(response([],code='1'))
    def test_missing_class(self):
        with self.assertRaises(ValueError): parse_score(response([{'class':'deepfake','score':.9}]))
    def test_invalid_scores(self):
        for value in [-1,2,float('nan'),True,'0.9']:
            with self.assertRaises(ValueError): parse_score(response([{'class':'ai_generated','score':value}]))
    def test_malformed(self):
        for data in [{},{'status':[]}]:
            with self.assertRaises(ValueError): parse_score(data)
