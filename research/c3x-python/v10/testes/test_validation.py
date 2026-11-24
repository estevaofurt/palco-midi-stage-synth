import unittest
import numpy as np
from stage_synth_c3x.engine import _string_force
from stage_synth_c3x import note_params

class TestMechanicalValidation(unittest.TestCase):
    def test_octaves_contact_and_finite(self):
        for midi in [21,33,45,48,50,57,60,69,81,93,108]:
            with self.subTest(midi=midi):
                bridge,force=_string_force(midi,velocity=90,hold=.1,total=.12,return_force=True)
                self.assertTrue(np.isfinite(bridge).all())
                self.assertTrue(np.isfinite(force).all())
                ms=1000*np.count_nonzero(force>1e-6)/48000
                self.assertGreater(ms,.5)
                self.assertLess(ms,5.)
                self.assertGreater(np.max(force),1)
                self.assertLess(np.max(force),200)
    def test_frequency_reconstruction(self):
        for midi in range(21,109):
            p=note_params(midi)
            recovered=(p.tensao_por_corda_n/p.densidade_linear_kg_m)**.5/(2*p.comprimento_vibrante_m)
            self.assertAlmostEqual(recovered,p.frequencia_hz,delta=1e-5)

if __name__=='__main__':unittest.main()
