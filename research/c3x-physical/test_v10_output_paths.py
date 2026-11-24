"""Tests for offline path A/B — never promotes an alternative piano sound engine."""
import json
import os
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from diagnostic_v10_output_paths import build_case

class F15V10AblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ.get('F15_V10_ROOT','/mnt/data/Stage_Synth_C3X_Etapa_10'))
        if not cls.root.exists():
            # GitHub Actions base: research/c3x-physical/test file relative to checkout.
            cls.root=Path(__file__).resolve().parents[2] / 'research/c3x-python/v10'
        cls.case=build_case(cls.root,75)

    def test_original_reconstructed_not_modified(self):
        self.assertLess(clsmax(self.case['max_unmodified_V10_difference']), 2e-6)

    def test_diagnostic_is_radiation_muting_not_new_strings(self):
        s=self.case['waveforms']
        self.assertEqual(s['v10_original'].shape,s['direct_and_board_only_diagnostic'].shape)
        self.assertGreater(float(np.max(np.abs(s['v10_original']-s['direct_and_board_only_diagnostic']))),0.03)

    def test_h5_interference_is_released_by_muting_body_ir(self):
        before=self.case['measures']['v10_original']['h5_db_rel_fundamental']
        after=self.case['measures']['direct_and_board_only_diagnostic']['h5_db_rel_fundamental']
        self.assertGreater(after-before,15)

    def test_h4_reduction_matches_report(self):
        before=self.case['measures']['v10_original']['h4_db_rel_fundamental']
        after=self.case['measures']['direct_and_board_only_diagnostic']['h4_db_rel_fundamental']
        self.assertLess(after-before,-10)

    def test_audio_diagnostic_files_have_no_clipping(self):
        p=Path(os.environ.get('F15_DIAG_DIR',str(Path(__file__).resolve().parent/'audios')))/'C4_AB_V10_vs_sem_IR_modal_RMS_IGUALADO_DIAGNOSTICO.wav'
        if os.environ.get('F15_DIAG_DIR') or p.exists():
            self.assertTrue(p.is_file(), 'diagnostic A/B missing')
            x,fs=sf.read(p)
            self.assertEqual(fs,48000)
            self.assertEqual(x.ndim,2)
            self.assertEqual(x.shape[1],2)
            self.assertLess(np.max(np.abs(x)),0.81)
            self.assertTrue(np.isfinite(x).all())

def clsmax(x):return abs(float(x))

if __name__=='__main__':unittest.main()
