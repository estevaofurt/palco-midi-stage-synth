import unittest
import numpy as np
from sustain_brightness import attack_bands,attack_compare,fixed_thresholds
class BrightnessTest(unittest.TestCase):
    def test_attack(self):
        r=48000;t=np.arange(round(.2*r))/r
        y=np.stack([np.sin(2*np.pi*260*t)+.3*np.sin(2*np.pi*1000*t)+.1*np.sin(2*np.pi*3000*t)]*2,axis=1)
        a=attack_bands(y,r);b=attack_bands(.5*y,r)
        self.assertTrue(attack_compare(a,a)['gate'])
        v=attack_compare(b,a);self.assertFalse(v['gate'])
        self.assertAlmostEqual(v['maximumSignificantBandChangeDb'],6.020599913,places=7)
    def test_threshold(self):
        s=dict(channels=[dict(channel=1,windows=[dict(timeS=0,fundamentalRmsPa=1.,spectralRmsPa=1.),dict(timeS=1,fundamentalRmsPa=.001,spectralRmsPa=.01)])])
        r=dict(channels=[dict(peakFundamentalRmsPa=10.,peakSpectralRmsPa=10.)])
        a=fixed_thresholds(s,r)[0]
        self.assertEqual(a['fundamental']['-60']['lastWindowEndS'],1)
        self.assertTrue(a['total']['-60']['rightCensored'])
if __name__=='__main__':unittest.main()
