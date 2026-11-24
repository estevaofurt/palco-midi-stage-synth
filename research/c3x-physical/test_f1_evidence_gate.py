from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import wave

sys.path.insert(0,str(Path(__file__).resolve().parent))
from f1_evidence_gate import evaluate, inspect_project_state, REQUIRED_MEASURES


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        def asset(n, wav=False):
            p=self.root/n
            if wav:
                with wave.open(str(p),"wb") as f:
                    f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(bytes([sum(map(ord,n))%254, 0])*48000)
            else:p.write_bytes((n*4).encode())
            return {"path":n,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        self.fixture={
            "schema":"stage-c3x-f1-evidence-v1",
            "instrument":{"manufacturer":"Yamaha","model":"C3X","exemplar_id":"C3X_AUDIT_001","recording_session":"2026-11-24","tuning_reference_hz":440,"microphone_geometry":"one calibrated rig","room_description":"studio A","lid_position":"fully open","test_fixture":False},
            "rights":{"commercial_analysis_authorized":True,"permission_checked_by_human":True,"permission_reference":"Consent record 0001"},
            "recordings":[{"dynamic":v,"midi_note":60,"instrument_id":"C3X_AUDIT_001","processed":False,"pedal":"off","held_key":True,"asset":asset(f"{v}.wav",True)} for v in ("pp","mf","ff")],
            "measurements":[{"parameter":key,"value":values[key],"unit":unit,"standard_uncertainty":.00001,"method":"calibrated gauge","provenance":"technician notebook","source_type":"real_measurement","instrument_id":"C3X_AUDIT_001","independent_of_target_frequency":True,"source_asset":asset(key+".txt")} for key,unit in REQUIRED_MEASURES.items()]
        }
    def run_gate(self,fn=None):
        p=copy.deepcopy(self.fixture)
        if fn:fn(p)
        return evaluate(p,self.root)
    def checkblocked(self,mut=None):
        r=self.run_gate(mut)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertFalse(r["C3X_F1_approved"])
        self.assertTrue(r["missing_or_invalid"])
        return r
    def test_valid_fixture_still_requires_human(self):
        r=self.run_gate()
        self.assertEqual(r["status"],"READY_FOR_MANUAL_REVIEW")
        self.assertFalse(r["automatic_approval"])
        self.assertFalse(r["C3X_F1_approved"])
    def test_reject_C5_instead_of_C3X(self):self.checkblocked(lambda p:p["instrument"].update(model="C5"))
    def test_reject_missing_exemplar(self):self.checkblocked(lambda p:p["instrument"].update(exemplar_id="unknown"))
    def test_reject_fixture_claiming_real(self):self.checkblocked(lambda p:p["instrument"].update(test_fixture=True))
    def test_reject_missing_commercial_rights(self):self.checkblocked(lambda p:p["rights"].update(commercial_analysis_authorized=False))
    def test_reject_no_human_license_review(self):self.checkblocked(lambda p:p["rights"].update(permission_checked_by_human=False))
    def test_reject_only_two_dynamics(self):self.checkblocked(lambda p:p.update(recordings=p["recordings"][:2]))
    def test_reject_wrong_midi_octave(self):self.checkblocked(lambda p:p["recordings"][0].update(midi_note=48))
    def test_reject_processed_audio(self):self.checkblocked(lambda p:p["recordings"][0].update(processed=True))
    def test_reject_wrong_instrument_in_audio(self):self.checkblocked(lambda p:p["recordings"][0].update(instrument_id="other"))
    def test_reject_modified_wav_bytes(self):
        (self.root/"mf.wav").write_bytes(b"changed")
        self.checkblocked()
    def test_reject_path_traversal(self):self.checkblocked(lambda p:p["recordings"][0]["asset"].update(path="../outside.wav"))
    def test_reject_fake_wav_extension(self):self.checkblocked(lambda p:p["recordings"][0].update(asset=p["measurements"][0]["source_asset"]))
    def test_reject_mismatched_wire_units(self):self.checkblocked(lambda p:p["measurements"][2].update(unit="mm"))
    def test_reject_missing_measurement(self):self.checkblocked(lambda p:p.update(measurements=p["measurements"][:-1]))
    def test_reject_negative_uncertainty(self):self.checkblocked(lambda p:p["measurements"][0].update(standard_uncertainty=-1))
    def test_reject_fractional_string_count(self):self.checkblocked(lambda p:p["measurements"][0].update(value=2.5))
    def test_reject_nan_value(self):self.checkblocked(lambda p:p["measurements"][0].update(value=float("nan")))
    def test_reject_circular_linear_mass_tension(self):
        def bad(p):
            for m in p["measurements"]:
                if m["parameter"] in ("C4_linear_density","C4_tension"):m["independent_of_target_frequency"]=False
        self.checkblocked(bad)
    def test_project_f1_actual_blocked(self):
        p=Path(__file__).resolve().parents[0]/"F1_ESTADO_E_GATES_V2.json"
        if not p.exists():self.skipTest("project-state file only present in repo runner")
        v=inspect_project_state(p)
        self.assertEqual(v["status"],"BLOCKED")
        self.assertEqual(v["physical_c4_measured_count"],0)

values={"C4_string_count":3,"C4_vibrating_length":.6,"C4_wire_diameter":.001,"C4_linear_density":.006,"C4_tension":700,"C4_inharmonicity_B":.0003,"C4_partial_decay":1.0,"C4_strike_position":.12}

if __name__=="__main__":unittest.main()
