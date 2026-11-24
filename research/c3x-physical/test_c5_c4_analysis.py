import unittest
import numpy as np
from c5_c4_analysis import measure, compare,window_partials,estimate_B,sha256_file,SOURCES

class TestC5Analysis(unittest.TestCase):
    FS=48000
    def synthetic(self,b=.0005,seconds=1.7):
        t=np.arange(round(self.FS*seconds))/self.FS
        y=np.zeros(len(t))
        for k in range(1,10):
            f=261.6255653*k*((1+b*k*k)/(1+b))**.5
            y+=.2/(k**1.35)*np.sin(2*np.pi*f*t)*np.exp(-t*(1.5+.24*k))
        return np.column_stack([y,y])
    def test_B_estimator_control(self):
        s=self.synthetic();r=measure(s,self.FS,'synthetic only')
        b=r['inharmonicity_estimate']['B_fit'];self.assertAlmostEqual(b,.0005,delta=.00012)
    def test_window_usable(self):
        x=self.synthetic();p=window_partials(x[:,0],self.FS,.1,.30)
        self.assertGreaterEqual(len(p),9)
        self.assertEqual(p[0]['n'],1)
    def test_mono_rejected(self):
        with self.assertRaises(ValueError):measure(self.synthetic()[:,0],self.FS,'x')
    def test_rate_rejected(self):
        with self.assertRaises(ValueError):measure(self.synthetic(),44100,'x')
    def test_comparison_zero(self):
        r=measure(self.synthetic(),self.FS,'x')
        z=compare(r,r)
        self.assertEqual(z['attack_35_255ms']['mean_absolute_difference_db'],0)
    def test_declared_sources(self):
        self.assertEqual(set(SOURCES),{'v1','v8','v16'})
        self.assertTrue(all(len(x['sha256'])==64 for x in SOURCES.values()))

if __name__=='__main__': unittest.main()
