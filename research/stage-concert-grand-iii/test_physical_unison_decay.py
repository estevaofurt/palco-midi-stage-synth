import unittest
import numpy as np
from physical_unison_decay import tension_multiplier,offsets,metrics
class UnisonTest(unittest.TestCase):
    def test_tension(self):
        f=lambda x:260*np.sqrt(.99*x+.01)
        for c in (-2.,-.25,0.,.5,2.):
            m=tension_multiplier(f,c)
            self.assertAlmostEqual(1200*np.log2(f(m)/f(1.)),c,places=7)
        np.testing.assert_allclose(offsets(3,1.),[-1.,0.,1.])
        np.testing.assert_allclose(offsets(1,1.),[0.])
    def test_observation_identity(self):
        t=np.linspace(0.,1.,800);x=np.column_stack([np.cos(t),np.sin(t),np.cos(2*t)])
        mean=x.mean(axis=1)
        rms=abs(np.column_stack([mean,np.ones(len(t)),x,x-mean[:,None]]))
        y=metrics(rms,3,[1.,1.,1.,1.])
        self.assertLess(y['observationIdentity'],1e-12)
        self.assertLessEqual(max(v['fraction'] for v in y['differentialEnergyProxyFraction']),1.)
if __name__=='__main__':unittest.main()
