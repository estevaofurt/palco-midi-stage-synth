"""Arithmetic fixtures only, never physical simulation evidence."""
import unittest
from energy_audit import audit_partition

class TestEnergyAudit(unittest.TestCase):
    def fixture(self):
        # E=0.5 J; impulse=1.8 Ns gives v=-0.8 m/s, capture=0.32 J.
        return dict(initial=.5,mass=1.,speed=1.,impulse=1.8,
                    stores=dict(mechanical=.07,cavity=.01,hammer_kinetic=0.,felt=.02),
                    target_losses=dict(mechanical=.03,cavity=.02,exterior_work=.01),
                    felt_loss=.02,capture_loss=.32,combined_loss=.06,combined_storage=.10)
    def test_partition(self):
        r=audit_partition(**self.fixture())
        self.assertAlmostEqual(r['inferred_capture_J'],.32)
        self.assertLess(max(r['relative_errors'].values()),1e-12)
    def test_capture_mismatch_even_with_balanced_total(self):
        x=self.fixture();x['capture_loss']-=.01;x['felt_loss']+=.01
        with self.assertRaises(AssertionError):audit_partition(**x)
    def test_signed_exterior(self):
        x=self.fixture();x['target_losses']['exterior_work']=-.01;x['target_losses']['mechanical']=.05
        r=audit_partition(**x)
        self.assertEqual(r['loss_J']['exterior_work'],-.01)
    def test_storage_partition_mismatch(self):
        x=self.fixture();x['combined_storage']+=.01
        with self.assertRaises(AssertionError):audit_partition(**x)
    def test_no_rebound(self):
        x=self.fixture();x['impulse']=.2
        with self.assertRaises(AssertionError):audit_partition(**x)
if __name__=='__main__':unittest.main(verbosity=2)
