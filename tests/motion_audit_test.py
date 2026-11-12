import base64
import io
import unittest
from PIL import Image
from detector.audit_motion import audit_sample


def sample(colors=None):
    frames = []
    for i in range(16):
        buf = io.BytesIO()
        Image.new('RGB', (8, 8), colors[i] if colors else (i * 15, 0, 0)).save(buf, format='JPEG')
        frames.append(dict(time=i / 8, method='Video pixels',
                           data='data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()))
    return dict(schema=2, mode='motion', label='real', frames=frames)


class MotionAuditTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(audit_sample(sample())['ready'])

    def test_frozen_pixels_despite_advancing_time(self):
        s = sample()
        s['frames'][1]['data'] = s['frames'][0]['data']
        self.assertFalse(audit_sample(s)['ready'])

    def test_missing_label(self):
        s = sample()
        del s['label']
        self.assertFalse(audit_sample(s)['ready'])

    def test_invalid_image(self):
        s = sample()
        s['frames'][0]['data'] = 'data:image/jpeg;base64,not-an-image'
        self.assertFalse(audit_sample(s)['ready'])

    def test_scene_cut_flagged(self):
        colors = [(40 + i * 2, 40 + i * 2, 40 + i * 2) for i in range(8)] + \
                 [(220 - i * 2, 220 - i * 2, 220 - i * 2) for i in range(8)]
        result = audit_sample(sample(colors))
        self.assertFalse(result['ready'])
        self.assertEqual(result['cut_after_frames'], [7])

    def test_gradual_change_not_a_cut(self):
        self.assertEqual(audit_sample(sample())['cut_after_frames'], [])

    def test_bad_cadence(self):
        s = sample()
        s['frames'][4]['time'] += .1
        self.assertFalse(audit_sample(s)['ready'])
