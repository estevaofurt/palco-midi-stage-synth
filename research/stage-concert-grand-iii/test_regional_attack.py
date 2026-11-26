import unittest
import numpy as np
from regional_attack import regional_matrix,screening
class RegionTest(unittest.TestCase):
    def test_passive(self):
        G=np.stack([np.diag([1.,2.]),np.diag([3.,4.]),np.array([[1.,1.],[1.,1.]])])
        np.testing.assert_allclose(regional_matrix(G,[1.,1.,1.]),G.sum(axis=0))
        np.testing.assert_allclose(regional_matrix(G,[.25,1.,.25]),.25*G[0]+G[1]+.25*G[2])
        self.assertGreaterEqual(np.linalg.eigvalsh(regional_matrix(G,[.25,1.,.25])).min(),0.)
        with self.assertRaises(ValueError):regional_matrix(G,[-1.,1.,1.])
    def test_tradeoff(self):
        def row(r,t):return dict(comparison=[dict(fundamentalCommonT60S=t,fundamentalPeakRelative=1.,lateUpperEnergyPa2S=1.)],pressureEnvelope=dict(fundamental=[dict(rippleRmsDb=r)]),attackComparison=dict(gate=True))
        self.assertTrue(screening(row(.5,35),row(1.,36))['candidateGate'])
        self.assertFalse(screening(row(.5,20),row(1.,36))['candidateGate'])
if __name__=='__main__':unittest.main()
