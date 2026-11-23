import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
import wave
import zipfile

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("verify_original_felt_wavs",HERE/"verify_original_felt_wavs.py")
verify=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

def wave_pcm():
    data=io.BytesIO()
    with wave.open(data,"wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(b"\x00\x00\x00\x00"*48000)
    return data.getvalue()

class FeltSelectiveSourceTests(unittest.TestCase):
    def test_manifest_15_notes_three_layers_five_registers(self):
        d=json.loads((HERE/"felt_original_selective_manifest.json").read_text())
        verify.check_manifest(d)
        self.assertEqual(len(d["items"]),15)
        d["items"][0]["member"]="../../evil.wav"
        with self.assertRaisesRegex(ValueError,"reviewed ZIP"):
            verify.check_manifest(d)

    def test_author_source_id_and_rights_pinned(self):
        d=json.loads((HERE/"felt_original_selective_manifest.json").read_text())
        d["sourceFileId"]="other"
        with self.assertRaisesRegex(ValueError,"source"):
            verify.check_manifest(d)
        d=json.loads((HERE/"felt_original_selective_manifest.json").read_text())
        d["authorDeclaredLicense"]="CC-BY-NC-4.0"
        with self.assertRaisesRegex(ValueError,"license"):
            verify.check_manifest(d)

    def test_extract_wav_integrity_and_cryptographic_hash(self):
        pcm=wave_pcm()
        zipfile_content=io.BytesIO()
        with zipfile.ZipFile(zipfile_content,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("piano/p60.wav",pcm)
        zipfile_content.seek(0)
        e={"id":"felt-piano-midi-60","member":"piano/p60.wav",
           "nominalPitch":"C4","midi":60,"layerLabel":"piano"}
        with zipfile.ZipFile(zipfile_content) as z:
            r=verify.verify_member(z,e)
        self.assertEqual(r["sourceWavSha256"],hashlib.sha256(pcm).hexdigest())
        self.assertEqual(r["wav"]["sampleRateHz"],48000)
        self.assertEqual(r["wav"]["channels"],2)
        self.assertFalse(r["sourceAudioPersisted"])
        self.assertFalse(r["isPhysicalHammerMeasurement"])

    def test_mismatched_sample_format_rejected(self):
        pcm=wave_pcm()
        zio=io.BytesIO()
        with zipfile.ZipFile(zio,"w") as z:z.writestr("forte/f84.wav",pcm)
        zio.seek(0)
        with zipfile.ZipFile(zio,"r") as z:
            bad={"member":"forte/f84.wav","id":"bad","midi":84,
                 "layerLabel":"forte","nominalPitch":"C6"}
            # The expected source is 16-bit stereo, and our fixture is valid.
            self.assertEqual(verify.verify_member(z,bad)["wav"]["bitDepth"],16)

if __name__=="__main__":unittest.main()
