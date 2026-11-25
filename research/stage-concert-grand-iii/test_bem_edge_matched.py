import unittest
import numpy as np
from test_exterior_bem import sphere
from exterior_bem import topology
from bem_edge_matched import matched
class MatchTest(unittest.TestCase):
    def test_common_size_and_geometry(self):
        t=sphere(.5,1);l=np.arange(len(t));S=np.arange(1.,3*len(t)+1).reshape(-1,3)
        a,b,r=matched(t,l,S,np.ones_like(S,bool),100)
        self.assertEqual(len(a[0]),len(b[0]));self.assertGreater(len(a[0]),len(t))
        self.assertLessEqual(len(a[0]),100);self.assertTrue(r['exactCountMatch'])
        for q,ll,_ in (a,b):
            self.assertTrue(topology(q)['gate']);self.assertAlmostEqual(topology(q)['volume'],topology(t)['volume'],places=12)
        with self.assertRaises(ValueError):matched(t,l,S,np.zeros_like(S,bool),100)
if __name__=='__main__':unittest.main()
