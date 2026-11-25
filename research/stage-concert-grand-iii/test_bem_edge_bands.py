import unittest,math
import numpy as np
from bem_edge_bands import band_samples,samples,LIMITS
from bem_edge_localization import localize
from bem_p1_static_moments import fit,operators
from bem_power_partition import integrate
from test_exterior_bem import sphere
class BandTest(unittest.TestCase):
    def test_exact_area_and_radial_moments(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        for order in (4,8):
            x,w,s,b=band_samples(t,order)
            self.assertTrue(np.all(w>0));self.assertAlmostEqual(w.sum(),.5,places=13)
            for j in range(3):
                d=3*np.stack([1-x[0,:,0]-x[0,:,1],x[0,:,0],x[0,:,1]],axis=1)[:,(j+2)%3]
                for k,(lo,hi) in enumerate(zip(LIMITS[:-1],LIMITS[1:])):
                    m=(s==j)&(b==k)
                    self.assertTrue(np.all((d[m]>lo)&(d[m]<hi)))
                    for p in range(3):
                        expected=(hi**(p+1)-lo**(p+1))/(p+1)-(hi**(p+2)-lo**(p+2))/(p+2)
                        self.assertAlmostEqual(float(np.sum(w[0,m]*d[m]**p)),expected/3,places=13)
            for i in range(4):
                for j in range(4-i):
                    exact=math.factorial(i)*math.factorial(j)/math.factorial(i+j+2)
                    # Order four integrates lower moments exactly; order eight all.
                    if order==8 or i+j<=2:self.assertAlmostEqual(float(np.sum(w*x[:,:,0]**i*x[:,:,1]**j)),exact,places=13)
        with self.assertRaises(ValueError):band_samples(t,4,[0,.4,.1,1])
    def test_acoustic_integral_and_closure(self):
        t=sphere(.5,0);labels=np.zeros(len(t),int);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        q,_=fit(t,k,4,5,v)
        r=localize(t,labels,['port'],q,v,k,4,5,exact_bands=True)
        _,_,a=integrate(t,q,v,k,4,5,operator=operators,sample_rule=samples)
        self.assertTrue(r['exactBandIntegration'])
        self.assertAlmostEqual(r['heldoutResidual'],a['heldoutResidual'],places=12)
        self.assertAlmostEqual(r['heldoutWorstColumn'],a['heldoutWorstColumn'],places=12)
        fractions=np.sum([x['bandAreaFractions'] for x in r['categories']],axis=0)
        np.testing.assert_allclose(fractions,[.19,.45,.36],atol=1e-13)
        self.assertLess(r['energyClosure'],1e-12)
        np.testing.assert_allclose(np.asarray(r['sectorIndicator']).sum(1),r['elementIndicator'],atol=1e-13)
if __name__=='__main__':unittest.main()
