import unittest
import importlib.util
from pathlib import Path
import numpy as np

s=importlib.util.spec_from_file_location('rob',Path(__file__).with_name('c5_stereo_robustness.py'))
r=importlib.util.module_from_spec(s)
s.loader.exec_module(r)

class F1Robustness(unittest.TestCase):
    fs=48000
    def synth(self, B=.00028, a4=.2, a5=.1, flipped=False, noise=0., duration=2.8):
        t=np.arange(round(self.fs*duration))/self.fs
        f4=r.harmonic_frequency(261.54,B,4);f5=r.harmonic_frequency(261.54,B,5)
        x4=a4*np.sin(2*np.pi*f4*t);x5=a5*np.sin(2*np.pi*f5*t)
        left=x4+x5;right=x4+(-x5 if flipped else x5)
        if noise:
            rng=np.random.default_rng(123);left+=rng.normal(0,noise,len(t));right+=rng.normal(0,noise,len(t))
        return np.stack([left,right],axis=1)
    def test_01_peak_within_physical_guard_not_sideband(self):
        x=self.synth()
        t=np.arange(len(x))/self.fs
        x[:,0] += .8*np.sin(2*np.pi*1291*t)
        p=r.partial_measure(x[:,0],self.fs,.04,.22,r.harmonic_frequency(261.54,.00028,5))
        self.assertLess(abs(p['peak_hz']-r.harmonic_frequency(261.54,.00028,5)),2)
    def test_02_stereo_equal_phase_near_minus_six_db(self):
        d=r.analyze_stereo(self.synth(),self.fs,261.54,.00028,0)
        for stage in ('attack','body','tail'):
            for ch in ('L','R','mono'):
                self.assertLess(abs(d['stages'][stage][ch]['summary']['median_db']-(-6.02)),.3)
    def test_03_stereo_antiphase_monochannel_can_cancel(self):
        d=r.analyze_stereo(self.synth(flipped=True),self.fs,261.54,.00028,0)
        self.assertLess(abs(d['stages']['body']['L']['summary']['median_db']+6.02),.3)
        self.assertLess(abs(d['stages']['body']['R']['summary']['median_db']+6.02),.3)
        self.assertTrue(d['stages']['body']['mono']['summary']['valid']==0 or d['stages']['body']['mono']['summary']['median_db'] < -20)
    def test_04_peak_rejects_narrowband_noise_floor(self):
        d=r.analyze_stereo(self.synth(noise=.0001),self.fs,261.54,.00028,0)
        self.assertGreater(d['stages']['attack']['L']['summary']['valid'],0)
    def test_05_estimation_fails_lost_source_channel(self):
        x=self.synth();x[:,1]=0
        d=r.analyze_stereo(x,self.fs,261.54,.00028,0)
        self.assertEqual(d['stages']['body']['R']['summary']['valid'],0)
    def test_06_nonfinite_rejected(self):
        x=self.synth();x[10,1]=float('nan')
        with self.assertRaises(ValueError):r.analyze_stereo(x,self.fs,261.54,.00028,0)
    def test_07_invalid_rate_rejected(self):
        with self.assertRaises(ValueError):r.analyze_stereo(self.synth(),44100,261.54,.00028,0)
    def test_08_invalid_note_parameters_rejected(self):
        with self.assertRaises(ValueError):r.harmonic_frequency(0,.001,4)
    def test_09_statistical_window_percentiles_not_ci(self):
        a=r.summarize([-3.,-1.,2.,4.])
        self.assertEqual(a['median_db'],.5)
        self.assertEqual(a['valid'],4)
        self.assertLessEqual(a['p10_db'],a['median_db'])
        self.assertGreaterEqual(a['p90_db'],a['median_db'])
    def test_10_window_protection(self):
        with self.assertRaises(ValueError):r.partial_measure(np.zeros(10000),48000,0,.22,1050)
    def test_11_signal_is_not_physical_c3x_measurement(self):
        d=r.analyze_stereo(self.synth(),self.fs,261.54,.00028,0)
        self.assertEqual(d['note'],'C5 Dó4; NOT Yamaha C3X')
        self.assertIn('not statistical confidence interval',d['temporal_windows'])

if __name__=='__main__':unittest.main()
