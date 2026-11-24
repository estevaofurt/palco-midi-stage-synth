import unittest,math
from stage_synth_c3x.parameters import note_params
from stage_synth_c3x.tuning import tune_note,tuning_cents,note_partials,anchor_stretch_cents
class TestTuning(unittest.TestCase):
    def test_88_nominal_are_equal_and_laa_440(self):
        for midi in range(21,109):
            self.assertAlmostEqual(note_params(midi).frequencia_hz,440*2**((midi-69)/12),places=9)
        self.assertAlmostEqual(tune_note(69,'equal').target_hz,440,places=8)
    def test_corrected_physics_all_88(self):
        for midi in range(21,109):
            p=note_params(midi)
            for profile in ('equal','stretch_experimental'):
                v=tune_note(midi,profile)
                observed=math.sqrt(v.tension_newton/p.densidade_linear_kg_m)/(2*p.comprimento_vibrante_m)*math.sqrt(1+v.inharmonicity_b)
                self.assertAlmostEqual(observed/v.target_hz,1,places=11)
                self.assertGreater(v.tension_newton,0)
                self.assertGreater(v.inharmonicity_b,0)
    def test_stretch_pivots(self):
        a=anchor_stretch_cents()
        self.assertAlmostEqual(a[69],0.,places=10)
        self.assertLess(tuning_cents(21,'stretch_experimental'),0)
        self.assertGreater(tuning_cents(108,'stretch_experimental'),0)
        self.assertTrue(all(a[i]<a[i+12] for i in (21,33,45,57,69,81,93)))
    def test_inharmonic_partials_are_not_integer_multiples(self):
        f=note_partials(69,'equal',5)
        self.assertAlmostEqual(f[0],440,places=8)
        self.assertGreater(f[1],2*f[0])
    def test_invalid_modes(self):
        for name in ('c3x_real', 'railsback_Yamaha', ''):
            with self.assertRaises(ValueError): tune_note(69,name)
