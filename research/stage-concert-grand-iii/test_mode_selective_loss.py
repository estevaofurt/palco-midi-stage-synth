import unittest
import numpy as np
from types import SimpleNamespace
from mode_selective_loss import extra_rates,mode_loss
class ModeLossTest(unittest.TestCase):
    def test_shape(self):
        w=np.square([1.,1.5,2.,3.,4.,8.])
        d=extra_rates(w,6.)
        self.assertEqual(d[0],0.);self.assertEqual(d[1],0.)
        self.assertEqual(d[-1],6.);self.assertTrue(np.all(np.diff(d)>=0.))
    def test_psd_and_coordinate_consistency(self):
        M=np.diag([2.,3.,4.,5.]);K=np.diag([10.,300.,1600.,4500.]);U=np.diag(1/np.sqrt(np.diag(M)[1:]))
        w=SimpleNamespace(M=M,K=K,U=U,w2=np.diag(K)[1:]/np.diag(M)[1:])
        a=mode_loss([w],4.,0.)[0];b=mode_loss([w],4.,6.)[0]
        self.assertEqual(a.gamma[0],b.gamma[0])
        np.testing.assert_allclose(a.d,b.d)
        np.testing.assert_allclose(U.T@b.D[1:,1:]@U,np.diag(b.gamma),rtol=1e-12,atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(b.D-a.D).min(),-1e-12)
if __name__=='__main__':unittest.main()
