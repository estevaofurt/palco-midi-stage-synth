"""F1: regression checks of an unchanged V10 sound-path decomposition.

All tests use the original synthetic V10; no recorded Yamaha C5/C3X PCM is needed.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from c4_v10_stem_ablation import reconstruct, partial_profile, estimate_onset, to_summary, original_body_transfer

HERE=Path(__file__).resolve().parent
DEFAULT_ROOT=HERE.parent/'Stage_Synth_C3X_Etapa_10'
V10_ROOT=Path(__import__('os').environ.get('C3X_V10_ROOT',str(DEFAULT_ROOT)))


class StemAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stems,cls.meta=reconstruct(V10_ROOT,75,48000,1.8,verify=True)
        cls.summary=to_summary(cls.stems,cls.meta)

    def test_reconstructs_original_v10_unmodified(self):
        self.assertLess(self.meta['baseline_max_abs_difference'],2e-6)
        self.assertTrue(self.meta['c5_sample_not_used'])
        self.assertTrue(self.meta['stems_no_normalization'])

    def test_audio_is_finite_and_stereo(self):
        for name,signal in self.stems.items():
            with self.subTest(name=name):
                self.assertEqual(signal.shape,(86400,2))
                self.assertTrue(np.isfinite(signal).all())

    def test_time_domain_stems_sum_to_mix(self):
        actual=self.stems['direct']+self.stems['body']+self.stems['board']
        self.assertLess(float(np.max(np.abs(actual-self.stems['mix']))),1e-12)

    def test_reference_C4_parameter_is_not_measured(self):
        from stage_synth_c3x.parameters import note_params
        p=note_params(60)
        self.assertEqual(p.midi,60)
        self.assertIn('NAO medida',p.origem)
        self.assertAlmostEqual(self.meta['base_B_estimated'],p.inarmonicidade_b)

    def test_five_is_at_physical_peak_not_1291_sideband(self):
        p=self.summary['windows']['attack_35_255ms'][4]
        self.assertEqual(p['partial'],5)
        self.assertGreater(p['peak_hz'],1310)
        self.assertLess(p['peak_hz'],1325)
        self.assertGreater(abs(p['peak_hz']-1291),19.)

    def test_cancellation_fifth_on_attack(self):
        p=self.summary['windows']['attack_35_255ms'][4]
        self.assertLess(p['phase_cancellation_db'],-10)
        self.assertGreater(p['component_vs_mix_db']['direct'],5)
        self.assertGreater(p['component_vs_mix_db']['body'],5)

    def test_cancellation_fifth_on_sustain(self):
        p=self.summary['windows']['body_260_700ms'][4]
        self.assertLess(p['phase_cancellation_db'],-5)

    def test_direct_and_body_nearly_opposed_for_fifth(self):
        p=self.summary['windows']['attack_35_255ms'][4]
        self.assertGreater(abs(p['direct_vs_body_phase_deg']),145)

    def test_body_dominates_fourth_at_output(self):
        p=self.summary['windows']['attack_35_255ms'][3]
        self.assertGreater(p['component_vs_mix_db']['body'],-2)
        self.assertLess(p['component_vs_mix_db']['direct'],-15)
        self.assertLess(p['component_vs_mix_db']['board'],-35)

    def test_fifth_direct_route_is_not_nearly_as_suppressed(self):
        p=self.summary['windows']['attack_35_255ms'][4]
        self.assertGreater(p['component_relative_to_its_fundamental_db']['direct'],
                           p['mix_relative_to_fundamental_db']+10)

    def test_all_complex_stems_are_aligned(self):
        for name,partials in self.summary['windows'].items():
            for p in partials:
                with self.subTest(name=name,partial=p['partial']):
                    self.assertLessEqual(p['phase_cancellation_db'],0.01)
                    self.assertGreater(p['mix_complex_amplitude'],0)

    def test_onset_and_impact_are_not_command_time(self):
        self.assertGreater(self.meta['onset_impact_s'],.025)
        self.assertGreater(self.summary['detected_onset_s'],.025)

    def test_independent_synthetic_IR_transfer_boosts_fourth_and_notches_fifth(self):
        ir=original_body_transfer(V10_ROOT)
        fourth=ir['4']['channels'];fifth=ir['5']['channels']
        for ch in (0,1):
            with self.subTest(channel=ch):
                boost=fourth[ch]['combined_body_plus_direct_vs_direct_only_db']
                attenuation=fifth[ch]['combined_body_plus_direct_vs_direct_only_db']
                self.assertGreater(boost,15)
                self.assertLess(attenuation,-3)
                self.assertGreater(boost-attenuation,23)

    def test_IR_frequency_selectivity_reproducible(self):
        a=original_body_transfer(V10_ROOT)
        b=original_body_transfer(V10_ROOT)
        self.assertEqual(a,b)
        self.assertGreater(a['5']['predicted_partial_hz'],1310)
        self.assertLess(a['5']['predicted_partial_hz'],1325)

    def test_two_sample_rates_optional(self):
        # Re-run short low-cost case: the integrator must also be stable at 44.1 kHz.
        stem,info=reconstruct(V10_ROOT,25,44100,.52,verify=True)
        self.assertEqual(stem['mix'].shape,(round(.52*44100),2))
        self.assertLess(info['baseline_max_abs_difference'],2e-6)


class NumericReferenceTests(unittest.TestCase):
    def test_c5_hashes_and_provenance_are_numeric_only(self):
        path=HERE/'F1_4_V10_STEM_RESULTS.json'
        if not path.exists():self.skipTest('No generated report in test directory')
        x=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(x['C3X_F1_status'],'PENDENTE')
        self.assertTrue(x['V10_default_unchanged'])
        self.assertTrue(x['c5_C4_original_sha_verified'])
        self.assertTrue(all(c['not_c3x_measurement'] and not c['c5_audio_used_as_input'] for c in x['cases'].values()))

    def test_old_algorithm_misread_sideband_in_attack(self):
        path=HERE/'F1_4_V10_STEM_RESULTS.json'
        if not path.exists():self.skipTest('No generated report in test directory')
        x=json.loads(path.read_text(encoding='utf-8'))
        for layer in ['v1','v8','v16']:
            p=x['previous_broad_peak_algorithm_issue'][layer]
            self.assertLess(p['old_frequency_hz'],1300)
            self.assertGreater(p['new_physically_anchored_h5_frequency_hz'],1310)
            self.assertGreater(p['old_minus_new_db'],5)


if __name__=='__main__':unittest.main(verbosity=2)
