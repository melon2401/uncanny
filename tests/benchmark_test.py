import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from detector.benchmark import audit, run

class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.entries=[]
        for i,label in enumerate(['ai','real']):
            p=self.root/f'{i}.json'
            p.write_text(json.dumps(dict(schema=1,source=f'https://example.com/{i}',label=label,
                frames=[dict(data='data:image/jpeg;base64,'+base64.b64encode(str(i).encode()).decode())]*6)))
            self.entries.append(dict(file=p.name,group=str(i),label=label,split='development',evidence='fixture'))
    def manifest(self):
        p=self.root/'manifest.json';p.write_text(json.dumps(self.entries));return p
    def test_no_holdout_warns_and_cannot_evaluate(self):
        _,report=audit(self.manifest())
        self.assertEqual(report['independent_groups']['heldout'],dict(ai=0,real=0))
        with self.assertRaisesRegex(ValueError,'both'):run(self.manifest(),'heldout')
    def test_source_leakage(self):
        entry=dict(self.entries[0],file='copy.json',split='heldout',group='new-group')
        (self.root/'copy.json').write_bytes((self.root/'0.json').read_bytes())
        self.entries.append(entry)
        with self.assertRaisesRegex(ValueError,'crosses splits'):audit(self.manifest())
    def test_frame_leakage_different_sources(self):
        d=json.loads((self.root/'0.json').read_text());d['source']='different'
        (self.root/'copy.json').write_text(json.dumps(d))
        self.entries.append(dict(self.entries[0],file='copy.json',split='heldout',group='different'))
        with self.assertRaisesRegex(ValueError,'Identical frame'):audit(self.manifest())
    def test_related_sources_share_evaluation_group(self):
        d=json.loads((self.root/'0.json').read_text());d['source']='reupload'
        (self.root/'copy.json').write_text(json.dumps(d))
        self.entries.append(dict(self.entries[0],file='copy.json'))
        with patch('detector.benchmark.evaluate',return_value={}) as evaluate:
            report=run(self.manifest(),'development')
            self.assertEqual(report['independent_groups']['development']['ai'],1)
            mapping=evaluate.call_args.kwargs['source_groups']
            self.assertEqual(mapping[str(self.root/'copy.json')],mapping[str(self.root/'0.json')])
    def test_label_conflict(self):
        self.entries[0]['label']='real'
        with self.assertRaisesRegex(ValueError,'label'):audit(self.manifest())
