import importlib.util
import io
from pathlib import Path
import unittest
import zipfile

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("inspect_original_felt_zip_index",HERE/"inspect_original_felt_zip_index.py")
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

def fake_zip(names=("Piano/C4_v1.wav","Piano/C4_v2.wav")):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_STORED) as z:
        for name in names:z.writestr(name,b"RIFF"+b"\x00"*(64*1024))
    # Stretch file to >100 kB via two 64k entries
    return buf.getvalue()

class OriginalFeltZipDirectoryTests(unittest.TestCase):
    def test_exact_ranged_206_required(self):
        self.assertEqual(app.parse_content_range("bytes 0-511/900000",0,511),900000)
        with self.assertRaisesRegex(ValueError,"Range server"):
            app.parse_content_range("bytes 0-777/900000",0,511)
        with self.assertRaisesRegex(ValueError,"missing"):
            app.parse_content_range("",0,511)
        with self.assertRaisesRegex(ValueError,"Range server"):
            app.parse_content_range("bytes 0-511/5000",0,511)

    def test_reads_remote_zip_index_without_full_audio_transfer(self):
        data=fake_zip()
        total=len(data)
        def mock_fetch(start,end):return data[start:end+1],total
        source=app.RemoteZipReader(total,mock_fetch)
        entries=app.inspect_directory(source)
        self.assertEqual([x["name"] for x in entries],["Piano/C4_v1.wav","Piano/C4_v2.wav"])
        self.assertTrue(all(x["uncompressedBytes"]>64000 for x in entries))
        self.assertTrue(source.transferred<=app.BLOCK*2)
        self.assertLess(source.requests,5)

    def test_rejects_zip_traversal_path(self):
        data=fake_zip(["../outside.wav","safe.wav"])
        reader=app.RemoteZipReader(len(data),lambda s,e:(data[s:e+1],len(data)))
        with self.assertRaisesRegex(ValueError,"unsafe"):
            app.inspect_directory(reader)

    def test_rejects_changed_archive_and_transfer_budget(self):
        data=fake_zip()
        reader=app.RemoteZipReader(len(data),lambda s,e:(data[s:e+1],len(data)+1))
        with self.assertRaisesRegex(ValueError,"changed"):
            app.inspect_directory(reader)
        reader=app.RemoteZipReader(len(data),lambda s,e:(data[s:e+1],len(data)),max_transfer=8)
        with self.assertRaisesRegex(ValueError,"budget"):
            app.inspect_directory(reader)

    def test_reader_seek_boundaries(self):
        data=fake_zip()
        reader=app.RemoteZipReader(len(data),lambda s,e:(data[s:e+1],len(data)))
        with self.assertRaisesRegex(ValueError,"seek"):reader.seek(-1)
        with self.assertRaisesRegex(ValueError,"seek"):reader.seek(len(data)+1)
        with self.assertRaisesRegex(ValueError,"unbounded"):reader.read(3000000)

if __name__=="__main__":unittest.main()
