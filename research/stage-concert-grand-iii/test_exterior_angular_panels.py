import unittest
import numpy as np
from scipy.linalg import block_diag
from lid_exterior import Panel,angular
from exterior_angular_panels import angular_panels
from split_radiation import relative
class AngularTest(unittest.TestCase):
    def test_unequal_panels_and_blocks(self):
        p=Panel(np.array([[0.,0.,0.],[1.,0.,0.],[.5,.7,0.]]),np.array([0.,0.,1.]),10)
        q=Panel(np.array([[0.,0.,1.],[1.,0.,1.],[1.,.8,1.],[0.,1.,1.]]),np.array([0.,0.,1.]),55)
        parts=[]
        for v in (p,q):
            _,x,w,A=v.samples(14);parts.append((x,w[:,None]*A))
        xx=np.vstack([x for x,A in parts]);AA=block_diag(*[A for x,A in parts])
        for k in (.55,5.5):
            ref=angular(xx,AA,k,16)
            for block in (7,128,333):
                G,r=angular_panels(parts,k,16,block=block)
                self.assertLess(relative(G,ref),1e-12)
                self.assertLess(relative(G,G.T),1e-12)
                self.assertGreaterEqual(np.linalg.eigvalsh(G).min(),-1e-12*np.linalg.norm(G))
                self.assertLess(r['localBasisBytes'],r['denseBasisBytes'])
    def test_invalid(self):
        with self.assertRaises(ValueError):angular_panels([],1.,16)
        with self.assertRaises(ValueError):angular_panels([(np.zeros((2,3)),np.ones((3,1)))],1.,16)
if __name__=='__main__':unittest.main()
