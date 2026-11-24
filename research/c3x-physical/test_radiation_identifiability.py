"""No external audio. All test geometry and signals are invented controlled inputs."""
import cmath
import math
import unittest
from radiation_identifiability import Patch,pressure_rayleigh_patches,pressure_only_factorization,synthetic_radiation_example,normalized_synthetic_summary

class RadiationTest(unittest.TestCase):
    def test_cancellation_at_center_is_due_to_spatial_odd_mode(self):
        p=synthetic_radiation_example()
        self.assertLess(abs(p['5']['center']),1e-12)
        self.assertGreater(abs(p['4']['center']),1e-6)
    def test_off_axis_odd_mode_does_not_cancel(self):
        p=synthetic_radiation_example()
        self.assertGreater(abs(p['5']['offset']),1e-5)
        self.assertGreater(abs(p['5']['far_offset']),1e-5)
    def test_microphone_changes_h4_h5_ratio(self):
        x=normalized_synthetic_summary()
        self.assertGreater(x['offset']['h5_relative_to_h4_db']-x['center']['h5_relative_to_h4_db'],65)
    def test_linearity_of_patch_velocities(self):
        a=Patch((-.24,0.,0.),.04,.001+0.0002j)
        b=Patch((.24,0.,0.),.04,.001)
        mic=(.5,0.,1.)
        x=pressure_rayleigh_patches([a,b],mic,1100.)
        y=pressure_rayleigh_patches([a],mic,1100.)+pressure_rayleigh_patches([b],mic,1100.)
        self.assertAlmostEqual(abs(x-y),0.,places=12)
    def test_single_patch_inverse_distance(self):
        a=Patch((0.,0.,0.),.04,.001)
        p1=pressure_rayleigh_patches([a],(0.,0.,1.),1000.)
        p2=pressure_rayleigh_patches([a],(0.,0.,2.),1000.)
        self.assertAlmostEqual(abs(p1)/abs(p2),2.,places=12)
    def test_single_patch_propagation_phase(self):
        a=Patch((0.,0.,0.),.04,.001)
        f=1000.;c=343.
        a1=pressure_rayleigh_patches([a],(0.,0.,1.),f)
        a2=pressure_rayleigh_patches([a],(0.,0.,2.),f)
        expected=cmath.exp(-1j*2*math.pi*f/c)/2.
        self.assertAlmostEqual(abs(a2/a1-expected),0.,places=12)
    def test_absolute_pressure_scales_with_calibrated_patch_velocity(self):
        a=Patch((0.,0.,0.),.04,.001)
        b=Patch((0.,0.,0.),.04,.002)
        p=pressure_rayleigh_patches([a],(0.,0.,1.),1000.)
        q=pressure_rayleigh_patches([b],(0.,0.,1.),1000.)
        self.assertAlmostEqual(abs(q/p),2.,places=12)
    def test_pressure_only_source_transfer_non_identifiable(self):
        a=pressure_only_factorization(2+1j,4-.5j,3+2j)
        self.assertAlmostEqual(abs(a['pressure_original']-a['pressure_alternate']),0,places=12)
        self.assertGreater(abs(a['source_original']-a['source_alternate']),1)
        self.assertGreater(abs(a['transfer_original']-a['transfer_alternate']),1)
    def test_invalid_geometry_and_missing_units(self):
        a=Patch((0.,0.,0.),.04,.001)
        for mic,freq in [((0.,0.,0.),1000.),((0.,0.,1.),0.),((0.,0.,1.),float('nan'))]:
            with self.assertRaises(ValueError):pressure_rayleigh_patches([a],mic,freq)
        with self.assertRaises(ValueError):pressure_rayleigh_patches([Patch((0.,0.,0.),-.2,.001)],(0.,0.,1.),1000.)
    def test_cannot_infer_transfer_from_pressure_only(self):
        with self.assertRaises(ValueError):pressure_only_factorization(1+2j,3+4j,0)

if __name__=='__main__': unittest.main()
