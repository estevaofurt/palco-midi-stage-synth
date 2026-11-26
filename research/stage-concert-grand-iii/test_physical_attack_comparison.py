import unittest
import numpy as np
from physical_attack_comparison import compare,bands,RATE
class AttackCompareTest(unittest.TestCase):
    def test_identical(self):
        t=np.arange(2*RATE)/RATE;y=np.sin(2*np.pi*261.63*t)[:,None]*np.array([[1.,.6]])
        r=compare(y,y)
        self.assertEqual(r['waveformRelative2s'],0.)
        self.assertTrue(r['attackScreeningGate'])
        self.assertFalse(compare(2*y,y)['attackScreeningGate'])
        self.assertEqual(len(bands(y)),2)
if __name__=='__main__':unittest.main()
