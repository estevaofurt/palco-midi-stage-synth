import unittest
import numpy as np
from attack_flutter import envelope_metrics,episodes,variants
class FlutterTest(unittest.TestCase):
    def test_envelope(self):
        r=48000;t=np.arange(2*r)/r;x=np.sin(2*np.pi*261.625565*t)
        a=envelope_metrics(x,r,60)['fundamental'][0]
        b=envelope_metrics(x*(1+.4*np.sin(2*np.pi*30*t)),r,60)['fundamental'][0]
        self.assertGreater(b['rippleRmsDb'],a['rippleRmsDb']+.5)
    def test_contacts(self):
        f=np.array([[0.],[2.],[1.],[0.],[3.],[0.]])
        a=episodes(f,1000)[0]
        self.assertEqual(len(a['contacts']),2)
        self.assertEqual(a['contacts'][1]['startMs'],4.)
        self.assertAlmostEqual(a['impulseNs'],.006)
    def test_variants(self):
        self.assertEqual(len(variants(60)),8);self.assertEqual(len(variants(45)),7)
if __name__=='__main__':unittest.main()
