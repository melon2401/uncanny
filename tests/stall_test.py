import unittest
import numpy as np
from detector.stall_score import score_embeddings,validate_motion

class StallTests(unittest.TestCase):
    def params(self):
        return dict(mu_spat=np.zeros(4),W_spat=np.eye(4),mu_temp=np.zeros(4),W_temp=np.eye(4),
                    calib_ll_spat=np.zeros((3,16)),calib_ll_temp=np.zeros((3,15)))
    def test_static_abstains(self):
        self.assertEqual(score_embeddings(np.zeros((16,4)),self.params())['status'],'inconclusive')
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):score_embeddings(np.full((16,4),np.nan),self.params())
    def test_direction_and_range(self):
        r=score_embeddings(np.random.default_rng(4).normal(size=(16,4)),self.params())
        self.assertTrue(0<=r['real_reference_score']<=1)
        self.assertIn('not an authenticity probability',r['direction'])
    def test_cadence(self):
        sample=dict(schema=2,mode='motion',frames=[dict(time=i*.125,method='Video pixels') for i in range(16)])
        validate_motion(sample)
        sample['frames'][8]['time']=0
        with self.assertRaises(ValueError):validate_motion(sample)
    def test_old_sample_rejected(self):
        with self.assertRaises(ValueError):validate_motion(dict(schema=1,frames=[{}]*6))
