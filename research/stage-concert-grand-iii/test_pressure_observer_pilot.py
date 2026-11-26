import unittest
import numpy as np
from pressure_observer_pilot import dictionary,fit,predict,select
class ObserverFitTest(unittest.TestCase):
    def test_exact_dictionary(self):
        freq=[30,80,150,200,250,300];cfg=(2,15.,1e-12)
        C=np.random.default_rng(1).normal(size=(4,2,4));Y=predict(freq,C,cfg)
        X=fit(freq,Y,cfg)
        np.testing.assert_allclose(predict(freq,X,cfg),Y,rtol=1e-8,atol=1e-9)
        self.assertFalse(np.iscomplexobj(X))
    def test_selection(self):
        freq=[30,80,150,200,250,300];C=np.ones((4,2,4));Y=predict(freq,C,(2,15.,1e-4))
        chosen,rows=select(freq,{'exterior':Y})
        self.assertEqual(len(rows),18);self.assertTrue(np.isfinite(chosen['maximumInner']))
if __name__=='__main__':unittest.main()
