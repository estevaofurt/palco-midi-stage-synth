import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("verify_flac", HERE/"verify_flac.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class FlacSourceTests(unittest.TestCase):
    def test_cc0_and_ccby_are_explicitly_allowlisted(self):
        u=p.source_url("sfzinstruments/SalamanderGrandPiano","a"*40,"Samples/C4v8.flac","CC-BY-3.0")
        self.assertTrue(u.endswith("/Samples/C4v8.flac"))
        u2=p.source_url("freepats/upright-piano-KW","a"*40,"samples/C2vL.flac","CC0-1.0")
        self.assertTrue(u2.endswith("samples/C2vL.flac"))
        with self.assertRaisesRegex(ValueError,"not allowed"):
            p.source_url("sfzinstruments/SalamanderGrandPiano","a"*40,"Samples/C4v8.flac","CC-BY-NC-4.0")

    def test_rejects_source_path_escape(self):
        with self.assertRaisesRegex(ValueError,"unsafe"):
            p.source_url("freepats/upright-piano-KW","a"*40,"samples/../../../secret.flac","CC0-1.0")

    def test_parse_valid_streaminfo(self):
        info=bytearray(34)
        word=(48000<<44)|((2-1)<<41)|((24-1)<<36)|96000
        info[10:18]=word.to_bytes(8,"big")
        f=b"fLaC"+bytes([0x80])+(34).to_bytes(3,"big")+bytes(info)
        v=p.streaminfo(f)
        self.assertEqual(v["sampleRate"],48000)
        self.assertEqual(v["bitsPerSample"],24)
        self.assertEqual(v["channels"],2)
        self.assertEqual(v["pcmSamplesPerChannel"],96000)
        self.assertEqual(v["durationSeconds"],2)

    def test_rejects_header_bad_rate(self):
        info=bytearray(34)
        word=(12345<<44)|((2-1)<<41)|((24-1)<<36)|96000
        info[10:18]=word.to_bytes(8,"big")
        f=b"fLaC"+bytes([0x80])+(34).to_bytes(3,"big")+bytes(info)
        with self.assertRaisesRegex(ValueError,"unexpected"):
            p.streaminfo(f)

    def test_pinned_manifest_and_bytes_in_budget(self):
        m=json.loads((HERE/"cc_flac_pilot_manifest.json").read_text())
        p.check_manifest(m)
        self.assertEqual(len(m["items"]),20)
        m["items"][0]["gitBlobSha"]="uncertain"
        with self.assertRaisesRegex(ValueError,"blob"):
            p.check_manifest(m)

if __name__=="__main__":
    unittest.main()
