import unittest,math
from integrator_decay import poles,metrics
class DecayTest(unittest.TestCase):
    def test_roots(self):
        z=1j*2*math.pi*261.6256/48000
        a,b=poles(z*48000,48000)
        for g in (a,b):self.assertLess(abs((3-2*z)*g*g-4*g+1),1e-12)
        self.assertLess(abs(b),.4)
    def test_midpoint_undamped(self):
        for f in (110.,261.6256,8000.):
            self.assertLess(abs(metrics(f,48000,0.,'midpoint')['numericalDecayPerS']),1e-8)
    def test_bdf2_decay(self):
        a=metrics(261.6256,48000,0.,'bdf2')
        b=metrics(261.6256,96000,0.,'bdf2')
        self.assertGreater(a['numericalDecayPerS'],0.)
        self.assertTrue(7.9<a['numericalDecayPerS']/b['numericalDecayPerS']<8.1)
    def test_consistency(self):
        self.assertAlmostEqual(poles(0,48000)[0].real,1.)
        self.assertAlmostEqual(poles(0,48000)[1].real,1/3)
if __name__=='__main__':unittest.main()
