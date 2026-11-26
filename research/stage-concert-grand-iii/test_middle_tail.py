import unittest
import numpy as np
from middle_tail import analyze
class MiddleTest(unittest.TestCase):
    def test_medium_warning(self):
        rate=8000;t=np.arange(rate*12)/rate
        x=np.sin(2*np.pi*110*t)*np.exp(-t)+.06*np.sin(2*np.pi*669*t)*np.exp(-t/10)
        a=analyze(np.stack([x,x],axis=1),rate,45)[0]
        self.assertGreater(a['middleWarningWindows'],0)
        self.assertGreater(a['windows'][8]['targets']['669']['fraction'],.9)
        self.assertEqual(a['windows'][8]['middlePeaks'][0]['hz'],669.)
if __name__=='__main__':unittest.main()
