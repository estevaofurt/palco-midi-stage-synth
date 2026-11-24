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

# Additional validation: salience and reference integrity (not physical C3X proof).
class TestC5Salience(unittest.TestCase):
    def test_suppress_extremely_weak_comparison_bins(self):
        from c5_c4_analysis import compare
        def make(a,b):
            return {'spectral_windows':{'attack_35_255ms':[
                {'n':1,'relative_db':0},
                {'n':2,'relative_db':a},
                {'n':8,'relative_db':b}]}}
        x=make(-10,-75);y=make(-20,-90)
        d=compare(x,y)['attack_35_255ms']
        self.assertEqual(d['salient_partials_2_8'],[2])
        self.assertEqual(d['mean_absolute_difference_salient_db'],10)
    def test_data_never_named_c3x(self):
        from c5_c4_analysis import SAMPLE_LICENSE
        self.assertIn('Yamaha C5',SAMPLE_LICENSE)
        self.assertNotIn('Yamaha C3X',SAMPLE_LICENSE)
