import unittest
import numpy as np
from mechanical_observer import render,convert,alias_probe,note_events
class ObserverTest(unittest.TestCase):
    def test_silence(self):
        x,r=render(2,4,48000,[],.01,31)
        np.testing.assert_array_equal(x,np.zeros((480,2)))
    def test_conversion(self):
        self.assertTrue(alias_probe()['gate'])
        self.assertEqual(convert(np.zeros((960,2)),96000).shape,(480,2))
    def test_partition(self):
        e=note_events(2,48000,80,True)[:3]
        a,_=render(2,4,48000,e,.01,17)
        b,_=render(2,4,48000,e,.01,64)
        np.testing.assert_array_equal(a,b)
if __name__=='__main__':unittest.main()
