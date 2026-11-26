import unittest
import numpy as np
from variable_damper import PedalControl,VariableDamper,probe
from string_board_schur import fixture
class DamperTest(unittest.TestCase):
    def test_control(self):
        a=PedalControl(3,1000,[True,True,False],5.)
        a.note(0,True);a.sustain(1.)
        for _ in range(6):v=a.advance()
        np.testing.assert_allclose(v,[0,0,0])
        a.note(0,False);a.sustain(.5)
        for _ in range(6):v=a.advance()
        np.testing.assert_allclose(v,[.5,.5,0])
        a.note(1,True);a.sustain(0.)
        for _ in range(6):v=a.advance()
        np.testing.assert_allclose(v,[1,0,0])
    def test_no_state_reset(self):
        a=fixture(2,2,8000,'schur',8);x=VariableDamper(a,[0,0,1,1],a.ms*160)
        a.q[:]=.001;a.v[:]=.03;E=a.energy()
        self.assertTrue(x.apply([1,0]));self.assertEqual(E,a.energy())
        self.assertFalse(x.apply([1,0]))
        with self.assertRaises(ValueError):x.apply([-1,0])
    def test_reference(self):
        self.assertTrue(probe(4,2,8000)['gate'])
if __name__=='__main__':unittest.main()
