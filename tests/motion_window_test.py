import unittest
from unittest.mock import patch
from detector.motion_window import select_window
from motion_audit_test import sample

class WindowTests(unittest.TestCase):
    def longer(self):
        s=sample();s['schema']=3
        s['frames']=[{**s['frames'][i%16], 'time':i*.125} for i in range(32)]
        return s

    def test_legacy_capture_kept(self):
        window,audit,start=select_window(sample())
        self.assertTrue(audit['ready']);self.assertEqual(start,0)
        self.assertEqual(len(window['frames']),16)

    def test_earliest_good_window_without_model(self):
        s=self.longer()
        with patch('detector.motion_window.audit_sample',side_effect=lambda w,**kw: {'ready': w['frames'][0]['time']>=.375,'issues':['cut']}) as audit:
            window,_,start=select_window(s)
        self.assertEqual(start,3);self.assertEqual(audit.call_count,4)
        self.assertEqual(window['schema'],2);self.assertEqual(len(s['frames']),32)

    def test_no_good_section_abstains(self):
        with patch('detector.motion_window.audit_sample',return_value={'ready':False,'issues':['cut']}):
            window,audit,_=select_window(self.longer())
        self.assertIsNone(window);self.assertFalse(audit['ready'])

    def test_loop_rejected_before_window_selection(self):
        s=self.longer();s['frames'][-1]['time']=0
        with patch('detector.motion_window.audit_sample') as audit:
            self.assertIsNone(select_window(s)[0]);audit.assert_not_called()
