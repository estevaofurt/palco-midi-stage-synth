import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("probe_original_felt_drive", HERE/"probe_original_felt_drive.py")
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class FeltOriginalSourceTests(unittest.TestCase):
    def test_source_url_file_id_and_copyright_claim(self):
        self.assertEqual(len(app.REQUEST_URLS),3)
        self.assertTrue(all(app.FILE_ID in x for x in app.REQUEST_URLS))
        self.assertEqual(app.FILENAME,"FuchsUndMoehrSamplesWAV16bit.zip")
        self.assertIn("polyphone.io",app.ORIGIN)

    def test_google_host_allowlist(self):
        for host in ("drive.google.com","drive.usercontent.google.com","doc-10-a.googleusercontent.com"):
            self.assertTrue(app.safe_host(host))
        for host in ("fakegoogleusercontent.com","example.org","drive.google.com.evil.net"):
            self.assertFalse(app.safe_host(host))

    def test_zip_header_is_only_access_evidence(self):
        r=app.classify_headers(206,"https://drive.usercontent.google.com/x",
          {"Content-Type":"application/zip","Content-Length":"512",
           "Content-Disposition":'attachment; filename="FuchsUndMoehrSamplesWAV16bit.zip"',
           "Content-Range":"bytes 0-511/734003200"},
          b"PK\x03\x04"+b"\x00"*16)
        self.assertTrue(r["firstBytesAreZip"])
        self.assertTrue(r["contentDispositionNamesExpectedZip"])
        self.assertFalse(r["sourceBytesFullyVerified"])
        self.assertEqual(r["status"],"ZIP HEADER REACHABLE, NOT DOWNLOADED")

    def test_html_login_not_claimed_as_zip(self):
        r=app.classify_headers(200,"https://drive.google.com/uc",
          {"Content-Type":"text/html","Content-Length":"74"},
          b"<!DOCTYPE html><html><body>Google Drive</body></html>")
        self.assertFalse(r["firstBytesAreZip"])
        self.assertTrue(r["looksLikeHtmlConfirmationOrLogin"])

    def test_rejects_other_host_and_oversize(self):
        with self.assertRaisesRegex(ValueError,"redirected"):
            app.classify_headers(200,"https://example.com/malicious.zip",{},b"PK\x03\x04")
        with self.assertRaisesRegex(ValueError,"length"):
            app.classify_headers(200,"https://drive.google.com/uc",
                                 {"Content-Length":"6000000000"},b"PK\x03\x04")
        with self.assertRaisesRegex(ValueError,"unbounded"):
            app.classify_headers(200,"https://drive.google.com/uc",
                                 {},b"PK\x03\x04"+b"\x00"*600)

if __name__=="__main__":unittest.main()
