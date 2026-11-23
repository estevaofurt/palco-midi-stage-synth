import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("audit_archive_metadata",HERE/"audit_archive_metadata.py")
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class SourceIndexTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((HERE/"steinway_d_felt_source_index.json").read_text(encoding="utf8"))

    def test_expected_three_sources_are_fixed(self):
        audit.validate_manifest(self.data)
        self.assertEqual(len(self.data["references"]),3)

    def test_noncormmercial_and_unknown_sources_rejected(self):
        self.data["references"][0]["license"]="CC-BY-NC-4.0"
        with self.assertRaisesRegex(ValueError,"license"):
            audit.validate_manifest(self.data)
        self.data["references"][0]["license"]="CC-BY-4.0"
        self.data["references"][0]["archiveIdentifier"]="unexpected"
        with self.assertRaisesRegex(ValueError,"untrusted"):
            audit.validate_manifest(self.data)

    def test_expected_member_filename_validated(self):
        self.data["references"][0]["expectedMembers"]=["../../password.wav"]
        with self.assertRaisesRegex(ValueError,"member"):
            audit.validate_manifest(self.data)

    def test_parse_valid_and_check_license_without_claiming_download(self):
        expected=self.data["references"][0]
        raw={"metadata":{"identifier":expected["archiveIdentifier"],"creator":"Dan Trueman","licenseurl":"https://creativecommons.org/licenses/by/4.0/"},
             "files":[{"name":expected["zipFile"],"size":"987654321","md5":"a"*32,"sha1":"b"*40}]}
        row=audit.extract_metadata(raw,expected)
        self.assertTrue(row["archiveExplicitCcBy4"])
        self.assertEqual(row["zipMd5"],"a"*32)
        self.assertIn("NOT downloaded",row["status"])
        self.assertEqual(len(row["expectedWavMembersNotVerified"]),len(expected["expectedMembers"]))

    def test_missing_zip_and_wrong_sha_block_promotion(self):
        expected=self.data["references"][0]
        raw={"metadata":{"identifier":expected["archiveIdentifier"]},"files":[]}
        with self.assertRaisesRegex(ValueError,"ZIP missing"):
            audit.extract_metadata(raw,expected)
        raw["files"]=[{"name":expected["zipFile"],"size":"987654321","md5":"nonsense"}]
        with self.assertRaisesRegex(ValueError,"MD5"):
            audit.extract_metadata(raw,expected)

if __name__=="__main__":unittest.main()
