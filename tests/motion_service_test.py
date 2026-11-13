import unittest
from detector.motion_server import analyze_motion
from motion_audit_test import sample

class MotionServiceTests(unittest.TestCase):
    def test_unknown_label_allowed_without_changing_it(self):
        s=sample();s['label']='unknown'
        r=analyze_motion(s,lambda value: {'status':'experimental','real_reference_score':.2})
        self.assertEqual(r['status'],'experimental')
        self.assertEqual(s['label'],'unknown')
        self.assertNotIn('label',r)

    def test_invalid_capture_never_enters_model(self):
        r=analyze_motion({},lambda value: self.fail('Must not run inference'))
        self.assertEqual(r['status'],'inconclusive')

    def test_static_abstention_preserved(self):
        r=analyze_motion(sample(),lambda value: {'status':'inconclusive','reason':'No temporal information'})
        self.assertEqual(r['status'],'inconclusive')
