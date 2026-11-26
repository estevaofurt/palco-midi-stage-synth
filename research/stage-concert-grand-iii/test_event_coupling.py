import unittest
import numpy as np
from event_coupling import EventEngine,proof,schedule,arrays
class EventTest(unittest.TestCase):
    def test_dense(self):
        self.assertTrue(proof(2,4,48000)['gate'])
    def test_partition(self):
        a=EventEngine(2,4,48000);b=EventEngine(2,4,48000);e=schedule(2,48000);N=round(.04*48000)
        a.process(N,e)
        for i in range(0,N,127):
            end=min(N,i+127);b.process(end,[v for v in e if i<=v[0]<end])
        for x,y in zip(arrays(a),arrays(b)):np.testing.assert_array_equal(x,y)
        self.assertEqual(a.bank.injected,b.bank.injected);self.assertEqual(a.refreshes,b.refreshes)
    def test_bad_event_atomic(self):
        a=EventEngine(2,4,48000)
        with self.assertRaises(ValueError):a.process(10,[(0,0x90,60,90),(1,0xB0,7,90)])
        self.assertEqual(a.sample,0);self.assertEqual(a.messages,0)
if __name__=='__main__':unittest.main()
