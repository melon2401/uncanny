import base64
import io
import unittest
import numpy as np
from PIL import Image
from detector.server import analyze, preprocess, PIPELINE

class FakeSession:
    def __init__(self, scores): self.scores = iter(scores)
    def run(self, _, inputs):
        assert inputs['pixel_values'].shape == (1,3,384,384)
        value = next(self.scores)
        return [np.array([[np.log(value/(100-value))]])]

def frame(color):
    buffer = io.BytesIO()
    Image.new('RGB', (320, 640), color).save(buffer, 'JPEG')
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()

class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.frames = [frame((i*30, i*20, i*10)) for i in range(6)]
    def test_reference_normalization(self):
        arr, _ = preprocess(Image.new('RGB', (400,800), 'white'))
        np.testing.assert_allclose(arr[0,:,0,0], (1-np.array([.485,.456,.406]))/np.array([.229,.224,.225]), rtol=1e-6)
    def test_conflicting_known_ai_example_abstains(self):
        result = analyze(FakeSession([1,99,88,99,1,66]), self.frames)
        self.assertEqual(result['reason'], 'conflicting_frames')
        self.assertEqual(result['signal'], 77)
        self.assertEqual(result['pipeline'], PIPELINE)
    def test_repetition_abstains_even_with_high_scores(self):
        result = analyze(FakeSession([99]*6), [self.frames[0]]*6)
        self.assertEqual(result['label'], 'Inconclusive')
        self.assertEqual(result['reason'], 'repeated_frames')
    def test_consistent_signals(self):
        for scores, label in [([99]*6,'Strong synthetic signal'),([1]*6,'Weak synthetic signal')]:
            self.assertEqual(analyze(FakeSession(scores), self.frames)['label'], label)
    def test_invalid_inputs(self):
        for frames in [[], ['bad']*6, ['data:image/jpeg;base64,!!!']*6]:
            with self.assertRaises(ValueError):
                analyze(FakeSession([]), frames)


class EvaluationTests(unittest.TestCase):
    def test_unknown_samples_do_not_become_accuracy_evidence(self):
        import tempfile, json
        from pathlib import Path
        from unittest.mock import patch
        from detector.evaluate import evaluate
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'sample.json').write_text(json.dumps(dict(schema=1, source='https://example.com/1', label='unknown', frames=[dict(data='fixture')]*6)))
            with patch('detector.evaluate.load_model'), patch('detector.evaluate.analyze', return_value={'label':'Strong synthetic signal'}):
                r = evaluate(folder)['legacy']
                self.assertEqual(r['unknown_videos'], 1)
                self.assertEqual(len(r['details']), 1)
                self.assertIsNone(r['ai_detection_rate'])
                self.assertIsNone(r['false_positive_rate'])

    def test_repeated_sources_count_once_and_conflicting_labels_fail(self):
        import tempfile, json
        from pathlib import Path
        from unittest.mock import patch
        from detector.evaluate import evaluate
        with tempfile.TemporaryDirectory() as folder:
            a = dict(schema=1, source='https://example.com/video/1', label='ai', frames=[dict(data='fixture')]*6)
            for name in ('a', 'b'):
                Path(folder, name+'.json').write_text(json.dumps(a))
            with patch('detector.evaluate.load_model'), patch('detector.evaluate.analyze', return_value={'label':'Inconclusive'}):
                report = evaluate(folder)
                self.assertEqual(report['legacy']['counts']['ai']['videos'], 1)
                self.assertEqual(report['legacy']['ai_detection_rate'], 0)
                self.assertEqual(report['legacy']['ai_inconclusive_rate'], 1)
                self.assertIsNone(report['legacy']['false_positive_rate'])
                a['label'] = 'real'
                Path(folder, 'b.json').write_text(json.dumps(a))
                with self.assertRaisesRegex(ValueError, 'Conflicting'):
                    evaluate(folder)

if __name__ == '__main__': unittest.main()

