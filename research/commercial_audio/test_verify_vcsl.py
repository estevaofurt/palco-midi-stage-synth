#!/usr/bin/env python3
"""No-network unit tests for source locking and original WAV provenance checks."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("verify_vcsl", HERE / "verify_vcsl.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture_pcm():
    data = io.BytesIO()
    with wave.open(data, "wb") as snd:
        snd.setnchannels(1)
        snd.setsampwidth(2)
        snd.setframerate(44100)
        snd.writeframes(b"\0\0" * 44100)
    return data.getvalue()


class CommercialSourceTests(unittest.TestCase):
    def test_immutable_url_escapes_piano_names(self):
        u = mod.source_url("sgossner/VCSL", "a" * 40,
          "Chordophones/Zithers/Upright Piano, Knight/Sustains/Player_vl1_rr1_C#4.wav")
        self.assertIn("Piano%2C%20Knight", u)
        self.assertIn("C%234.wav", u)
        self.assertTrue(u.startswith("https://raw.githubusercontent.com/"))

    def test_rejects_traversal_and_bad_repo(self):
        with self.assertRaises(ValueError):
            mod.source_url("other/repo", "a" * 40, "Chordophones/Zithers/piano.wav")
        with self.assertRaises(ValueError):
            mod.source_url("sgossner/VCSL", "a" * 40, "Chordophones/Zithers/../../LICENSE.wav")

    def test_manifest_has_correct_license_and_no_duplicate(self):
        m = json.loads((HERE / "vcsl_cc0_pilot_manifest.json").read_text())
        mod.check_manifest(m)
        m["origin"]["repoLicense"] = "CC-BY-NC-4.0"
        with self.assertRaisesRegex(ValueError, "CC0"):
            mod.check_manifest(m)

    def test_wav_provenance_sha_and_ephemeral_cleanup(self):
        data = fixture_pcm()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        item = {"id": "fixture-note", "path": "Chordophones/Zithers/test.wav",
                "bytes": len(data), "gitBlobSha": blob,
                "instrument": "Test fixture", "recordedPitch": "A4", "midi": 69,
                "velocityLayer": "fixture", "capture": "test only",
                "sourceProcessing": "synthetic fixture, not sample bank"}
        origin = {"repository": "sgossner/VCSL", "commit": "a" * 40}
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(mod.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                report = mod.fetch_and_verify(item, origin, Path(temp))
            self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(report["wav"]["sampleRate"], 44100)
            self.assertEqual(report["wav"]["frames"], 44100)
            self.assertFalse(list(Path(temp).glob("*.wav")))

    def test_tampered_wav_is_rejected_even_when_decodable(self):
        data = fixture_pcm()
        wrong_blob = hashlib.sha1(b"blob 1\0x").hexdigest()
        item = {"id": "fixture-note", "path": "Chordophones/Zithers/test.wav",
                "bytes": len(data), "gitBlobSha": wrong_blob}
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(mod.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                with self.assertRaisesRegex(ValueError, "blob SHA mismatch"):
                    mod.fetch_and_verify(item, {"repository": "sgossner/VCSL", "commit": "a" * 40}, Path(temp))
            self.assertFalse(list(Path(temp).glob("*.wav")))


if __name__ == "__main__":
    unittest.main()
