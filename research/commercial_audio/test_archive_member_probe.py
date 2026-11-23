import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("archive_member_probe",HERE/"archive_member_probe.py")
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
spec2=importlib.util.spec_from_file_location("probe_archive_wav_access",HERE/"probe_archive_wav_access.py")
wavprobe=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(wavprobe)

class ArchiveMemberTests(unittest.TestCase):
 def test_immutable_archive_url(self):
  d={"archiveIdentifier":"bitKlavierGrand_PianoBar_44k16b","zipFile":"bitKlavierGrand_PianoBar_44k16b.zip"}
  self.assertEqual(app.listing_url(d),"https://archive.org/download/bitKlavierGrand_PianoBar_44k16b/bitKlavierGrand_PianoBar_44k16b.zip/")

 def test_malicious_archive_rejected(self):
  with self.assertRaisesRegex(ValueError,"unknown"):
   app.listing_url({"archiveIdentifier":"../../etc","zipFile":"../../etc.zip"})

 def test_viewer_names_do_not_count_as_audio_integrity(self):
  d={"archiveIdentifier":"bitKlavierGrand_PianoBar_44k16b","zipFile":"bitKlavierGrand_PianoBar_44k16b.zip",
    "expectedMembers":["C2v8.wav","C4v8.wav"]}
  got=app.evaluate_page('<a href="C2v8.wav">C2v8.wav</a><a href="C4v8.wav">C4v8.wav</a>',d)
  self.assertEqual(len(got["presentInViewerListing"]),2)
  self.assertIn("NOT VERIFIED",got["listingStatus"])
  short=app.evaluate_page("<a>C2v8.wav</a>",d)
  self.assertEqual(len(short["presentInViewerListing"]),1)
  self.assertIn("INCONCLUSIVE",short["listingStatus"])

 def test_folder_qualified_member_href_is_accepted(self):
  ident="bitKlavierGrand_PianoBar_44k16b"
  base=f"https://archive.org/download/{ident}/{ident}.zip/"
  content=f'<a href="//archive.org/download/{ident}/{ident}.zip/{ident}%2FC4v8.wav">{ident}/C4v8.wav</a>'
  link=wavprobe.find_member_link(content,"C4v8.wav",base)
  self.assertIsNotNone(link)
  self.assertIn("C4v8.wav",link)

if __name__=="__main__":unittest.main()
