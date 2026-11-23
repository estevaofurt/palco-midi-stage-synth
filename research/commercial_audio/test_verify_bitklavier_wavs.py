import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("verify_bitklavier_wavs",HERE/"verify_bitklavier_wavs.py")
target=importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)

class Response(io.BytesIO):
    url="https://archive.org/download/bitKlavierGrand_PianoBar_44k16b/bitKlavierGrand_PianoBar_44k16b.zip/bitKlavierGrand_PianoBar_44k16b%2FC4v8.wav"

def wav_bytes():
    buffer=io.BytesIO()
    with wave.open(buffer,"wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(44100)
        output.writeframes(b"\x00\x00\x00\x00"*10000)
    return buffer.getvalue()

class BitKlavierWavTests(unittest.TestCase):
    def sample(self):
        m=json.loads((HERE/"steinway_d_selective_pilot.json").read_text(encoding="utf8"))
        target.check_manifest(m)
        return m

    def test_pinned_archive_path(self):
        m=self.sample()
        x=next(z for z in m["items"] if z["id"]=="steinway-d-pianobar-c4v8")
        self.assertTrue(target.source_url(x).endswith(".zip/bitKlavierGrand_PianoBar_44k16b%2FC4v8.wav"))

    def test_reject_nc_and_untrusted_items(self):
        m=self.sample()
        m["items"][0]["license"]="CC-BY-NC-4.0"
        with self.assertRaisesRegex(ValueError,"unreviewed"):
            target.check_manifest(m)
        m["items"][0]["license"]="CC-BY-4.0"
        m["items"][0]["memberName"]="../../config.wav"
        with self.assertRaisesRegex(ValueError,"unreviewed"):
            target.check_manifest(m)

    def test_verify_exact_sha_wav_and_cleanup(self):
        m=self.sample()
        x=next(z for z in m["items"] if z["id"]=="steinway-d-pianobar-c4v8")
        payload=wav_bytes()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(target.urllib.request,"urlopen",return_value=Response(payload)):
                r=target.verify_wav(x,Path(folder))
            self.assertEqual(r["wav"]["rateHz"],44100)
            self.assertEqual(r["wav"]["bitsPerSample"],16)
            self.assertEqual(r["sha256"],hashlib.sha256(payload).hexdigest())
            self.assertEqual(list(Path(folder).glob("*.wav")),[])
            self.assertFalse(r["hammerVelocityKnown"])

if __name__=="__main__":
    unittest.main()
