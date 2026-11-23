#!/usr/bin/env python3
"""Acquire a few *compressed* acoustic references (never publish sound files).
Source is the public StaPiano audio repo. These AAC files are NOT suitable for
absolute physical B/T60 calibration; use for preliminary timbral comparisons.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

root = Path(os.environ["STAGE_AUDIO_WORKDIR"])
root.mkdir(parents=True,exist_ok=True)
base = "https://raw.githubusercontent.com/StanislavMakhnytskyi/stapiano-samples/main"
# For Yamaha the originally recorded minor-third keys are exact C2/C4/C6.
# The Knight upright is sampled on odd-number MIDI keys; compare C#2/4/6.
groups = [
    ("yamaha-c5","Yamaha C5 Salamander (AAC extract)",[36,60,84],[1,3,4],"japanese",
     "CC BY 3.0 – Alexander Holm / Salamander","Yamaha C5 close-mic source; mono AAC subset, 4 of 16 layers, cropped/faded","unknown"),
    ("upright","Knight Upright / VCSL (AAC extract)",[37,61,85],[1,2],"upright",
     "CC0 1.0 – VCSL / Simon Dalzell","Knight upright close source, mono AAC, cropped to <=10 s and faded; not Kawai KW","unknown"),
]
manifest={"notes":[]}
for folder,instrument,notes,layers,character,license,description,room in groups:
 for key in notes:
  for layer in layers:
   name=f"{key}_v{layer}.m4a"
   url=f"{base}/{folder}/{name}"
   request=urllib.request.Request(url,headers={"User-Agent":"StageSynthAcousticResearch/1.0"})
   with urllib.request.urlopen(request,timeout=25) as res:
    data=res.read(2_000_001)
   if len(data)>2_000_000 or len(data)<4096 or data[4:8]!=b"ftyp":
    raise RuntimeError(f"Unexpected or truncated AAC data for {url}: size={len(data)}")
   original=root/f"compact_{folder}_{name}"
   original.write_bytes(data)
   pcm=root/f"compact_{folder}_{key}_v{layer}.f32le"
   subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(original),
       "-map","0:a:0","-ar","48000","-ac","1","-f","f32le","-acodec","pcm_f32le",str(pcm)],check=True)
   manifest["notes"].append({
    "id":f"compact-{folder}-{key}-v{layer}",
    "instrument":instrument,
    "key":key,
    "dynamic":f"source-v{layer}",
    "stageCharacter":character,
    "pcmPath":str(pcm),
    "originalUrl":url,
    "sha256":hashlib.sha256(data).hexdigest(),
    "bytes":len(data),
    "originalRate":44100,
    "originalChannels":1,
    "originalFormat":"AAC LC in M4A",
    "captureNotes":description,
    "processing":"MONO AAC 96kbps, trimmed to max 10 s, 0.4 s fade; not original uncompressed takes",
    "license":license,
    "roomType":room,
    "compression":"lossy AAC"
   })
   print("Fetched compact",folder,key,layer,len(data),"bytes",flush=True)
(root/"compact-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("Compact source acquired:",len(manifest["notes"]),"recordings; no audio may be uploaded as artifact")
