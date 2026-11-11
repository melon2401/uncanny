import base64
import io
import unittest
from PIL import Image
from detector.audit_motion import audit_sample


def sample():
    frames = []
    for i in range(16):
        buf = io.BytesIO()
        Image.new('RGB', (8, 8), (i * 15, 0, 0)).save(buf, format='JPEG')
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

    def test_bad_cadence(self):
        s = sample()
        s['frames'][4]['time'] += .1
        self.assertFalse(audit_sample(s)['ready'])
