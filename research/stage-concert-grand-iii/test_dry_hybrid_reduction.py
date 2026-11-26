import unittest
import numpy as np
from dry_hybrid_reduction import grids,hybrid_basis,select_hybrid
from dry_snapshot_reduction import normalized,errors
from dry_structural_modal import mobility
class HybridTest(unittest.TestCase):
    def test_grids(self):
        a,b,c=grids()
        self.assertEqual((len(a),len(b),len(c)),(63,31,31))
        self.assertEqual(len(set(np.r_[a,b,c])),125)
    def test_hybrid(self):
        n=12;M=np.eye(n);w=(2*np.pi*np.linspace(30,400,n))**2;K=np.diag(w)
        D=4*np.eye(n)+np.ones((n,n));P=np.random.default_rng(3).normal(size=(n,4))
        m,k,d,p=normalized(M,K,D,P);a,b,c=grids()
        selected,rows,model=select_hybrid(m,k,d,p,a,b,mobility(w,D,P,a),mobility(w,D,P,b),lows=(4,8,12),extras=(0,4,8,12))
        self.assertLess(max(selected['trainingMaximum'],selected['innerMaximum']),.05)
        self.assertLess(errors(mobility(*model,c),mobility(w,D,P,c))['maximum'],.05)
if __name__=='__main__':unittest.main()
