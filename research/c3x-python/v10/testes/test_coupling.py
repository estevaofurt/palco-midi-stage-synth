import unittest
import numpy as np
from stage_synth_c3x.coupled import (CouplingConfig,string_bridge_coupled,
                                      render_note_coupled)
from stage_synth_c3x.engine import _string_force,SR

class CouplingTests(unittest.TestCase):
    def test_disabled_coupling_bit_exact_equals_v1(self):
        conf=CouplingConfig(gamma_rad_1khz=0,stiffness_fraction=0)
        for midi in [33,48,69,93]:
            with self.subTest(midi=midi):
                a=_string_force(midi,90,hold=.25,total=.25)
                b=string_bridge_coupled(midi,90,hold=.25,total=.25,config=conf,pedal_down=True)
                self.assertTrue(np.array_equal(a,b))

    def test_finite_all_88_notes(self):
        for midi in range(21,109):
            y=string_bridge_coupled(midi,70,hold=.05,total=.06,pedal_down=True)
            self.assertTrue(np.isfinite(y).all(),msg=f'nota {midi}')
            self.assertGreater(np.max(np.abs(y)),0,msg=f'nota {midi}')

    def test_hammer_collision_physically_bounded(self):
        for midi in [21,48,69,93,108]:
            _,f=string_bridge_coupled(midi,90,.15,.2,return_force=True)
            self.assertGreater(np.max(f),1)
            self.assertLess(np.max(f),200)
            ms=1000*np.count_nonzero(f>1e-6)/SR
            self.assertGreater(ms,.5)
            self.assertLess(ms,5)

    def test_pedal_separates_sustained_and_damped_strings(self):
        down=string_bridge_coupled(69,90,.35,1.,pedal_down=True)
        up=string_bridge_coupled(69,90,.35,1.,pedal_down=False)
        def rms(x):return float(np.sqrt(np.mean(x*x)))
        self.assertTrue(np.array_equal(down[:int(.3*SR)],up[:int(.3*SR)]))
        self.assertGreater(rms(down[int(.55*SR):int(.65*SR)]),
                           8*rms(up[int(.55*SR):int(.65*SR)]))

    def test_coupling_changes_tail_not_hammer_character(self):
        conf=CouplingConfig(gamma_rad_1khz=0,stiffness_fraction=0)
        orig,fo=string_bridge_coupled(69,90,1.5,1.8,config=conf,pedal_down=True,return_force=True)
        coupled,fc=string_bridge_coupled(69,90,1.5,1.8,pedal_down=True,return_force=True)
        self.assertLess(abs(fc.max()-fo.max())/fo.max(),.02)
        self.assertGreater(float(np.sqrt(np.mean((orig-coupled)**2))),0.01)

    def test_rejects_nonphysical_parameters(self):
        with self.assertRaises(ValueError):
            string_bridge_coupled(69,config=CouplingConfig(gamma_rad_1khz=-1))

if __name__=='__main__': unittest.main()