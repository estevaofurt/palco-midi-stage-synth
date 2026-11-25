import unittest
import numpy as np
from high_mode_quadrature_audit import changes,self_metrics,adjacent,FREQ
from lid_exterior import Panel
class HighQuadratureAuditTest(unittest.TestCase):
    def test_frequency_independence(self):
        x=np.tile(np.eye(3),(len(FREQ),1,1));x[-1]*=1e6
        y=x.copy();y[0]*=1.1
        r=changes(x,y)
        self.assertAlmostEqual(r[0]['relative'],.1/1.1)
        self.assertEqual(max(v['relative'] for v in r[1:]),0.)
        self.assertEqual(max(v['rawAsymmetry'] for v in self_metrics(x)),0.)
        with self.assertRaises(ValueError):changes(x,y[1:])
    def test_adjacency(self):
        n=np.array([0.,0.,1.])
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
        p=[Panel(x,n,3),Panel(x+[1,0,0],n,3)]
        p.extend(Panel(x+[4*j,0,0],n,3) for j in range(1,5))
        self.assertEqual(adjacent(p,0),1)
if __name__=='__main__':unittest.main()
