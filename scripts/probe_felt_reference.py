#!/usr/bin/env python3
"""Metadata-only availability probe for public-domain Fuchs & Möhr Felt Piano.
No audio download and no file content uploaded.
"""
import re,urllib.request
url="https://huggingface.co/datasets/cueharbor/starter-instruments/resolve/main/felt-piano/instrument.sfz"
req=urllib.request.Request(url,headers={"User-Agent":"StageSynthResearch/1.0"})
with urllib.request.urlopen(req,timeout=30) as res:
 raw=res.read(350_000)
if len(raw)>=350_000:raise RuntimeError("SFZ metadata larger than expected")
text=raw.decode("utf-8-sig",errors="replace")
print("FELT SFZ bytes",len(raw),"sample opcodes",len(re.findall(r"\bsample\s*=",text)))
print("First 14 directives, paths abbreviated:")
for line in text.splitlines()[:14]:
 print(line[:210])
print("Sample paths near C4 and nearest mapped root:")
for line in text.splitlines():
 if re.search(r"(?:key|keycenter|root|pitch_keycenter)\s*=\s*(?:60|36|84)(?:\s|$)",line):
  print(line[:250])
