import unittest
from detector.visual_decision import decision

class VisualDecisionTests(unittest.TestCase):
    def test_disagreement_abstains(self):
        self.assertEqual(decision([-1,2,1,-.1,.1,.1],6)['label'],'Inconclusive')
    def test_repeated_abstains(self):
        self.assertEqual(decision([8]*6,1)['label'],'Inconclusive')
    def test_positive_signal_not_probability(self):
        r=decision([2]*6,6)
        self.assertEqual(r['label'],'AI-like visual signal');self.assertNotIn('signal',r)
    def test_negative_not_authenticity_claim(self):
        self.assertIn('does not prove',decision([-2]*6,6)['summary'])
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):decision([float('nan')]*6,6)
