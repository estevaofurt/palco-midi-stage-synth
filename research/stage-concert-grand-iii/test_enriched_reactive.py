import unittest
import numpy as np
from enriched_reactive_diagnostic import block_changes
from enriched_coupling_replay import require
class ReactiveTest(unittest.TestCase):
    def test_subblock(self):
        a=np.ones((6,61,63));b=a.copy();b[:,55:,55:]*=2
        d=block_changes(a,b)
        self.assertEqual(d['00'],0);self.assertEqual(d['11'],.5)
        self.assertLess(d['whole'],d['11'])
    def test_missing_evidence(self):
        with self.assertRaises(ValueError):require({},30,'a'*64,{})
if __name__=='__main__':unittest.main()
