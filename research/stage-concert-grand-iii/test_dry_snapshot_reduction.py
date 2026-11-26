import unittest
import numpy as np
from dry_snapshot_reduction import normalized,select,errors
from dry_structural_modal import mobility
class SnapshotTest(unittest.TestCase):
    def test_complete(self):
        n=8;M=np.eye(n);k=(2*np.pi*np.linspace(30,400,n))**2;K=np.diag(k);D=4*np.eye(n)+np.ones((n,n))
        P=np.random.default_rng(3).normal(size=(n,4));f=np.geomspace(30,500,12)
        ref=mobility(k,D,P,f);m,k0,d,p=normalized(M,K,D,P)
        selected,rows,model,s=select(m,k0,d,p,f,ref,[4,8])
        self.assertLess(rows[-1]['training']['maximum'],1e-9)
        self.assertLess(errors(mobility(*model,f),ref)['maximum'],.05)
if __name__=='__main__':unittest.main()
