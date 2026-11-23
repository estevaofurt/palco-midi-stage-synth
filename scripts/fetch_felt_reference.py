#!/usr/bin/env python3
"""Fetch a verified subset of the public-domain Fuchs & Möhr Felt Piano WAV set.
The 3-layer original author sample set has been repackaged by CueHarbor;
this script validates key centers/velocity ranges in the SFZ before analysis.
Keep WAVs/PCM in the ephemeral runner filesystem; publish numeric JSON only.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

BASE = "https://huggingface.co/datasets/cueharbor/starter-instruments/resolve/main/felt-piano/"
NOTES = {"C2":36, "C4":60, "C6":84}
LAYERS = [1,2,3]
selection = os.environ.get("STAGE_FELT_SELECTION","C4:v2")
if selection == "matrix":
    jobs = [(key,layer) for key in NOTES.values() for layer in LAYERS]
else:
    jobs = []
    for spec in selection.split(","):
        note, layer = spec.strip().split(":")
        if note not in NOTES or layer not in ("v1","v2","v3"):
            raise ValueError("Felt selection must be C2/C4/C6:v1/v2/v3")
        jobs.append((NOTES[note],int(layer[1:])))

def read_limited(url,cap=20_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"StageSynthResearch/1.0"})
    with urllib.request.urlopen(req,timeout=40) as reader:
        buf=reader.read(cap+1)
    if len(buf)>cap:raise RuntimeError("Oversized file: "+url)
    return buf

root=Path(os.environ["STAGE_AUDIO_WORKDIR"]).resolve()
root.mkdir(parents=True,exist_ok=True)
sfz=read_limited(BASE+"instrument.sfz",300_000).decode("utf-8-sig")
regions=[]
for line in sfz.splitlines():
    if "<region>" not in line: continue
    d=dict(re.findall(r"([a-zA-Z_]+)\s*=\s*([^\s]+)",line))
    if "sample" not in d:continue
    regions.append(d)
manifest={"notes":[]}
for key,layer in jobs:
    matches=[r for r in regions if int(r.get("pitch_keycenter",-1))==key
             and int(r.get("lovel",0))<=[1,43,86][layer-1]
             and int(r.get("hivel",128))>=[42,85,127][layer-1]]
    matches=[r for r in matches if f"_v{layer}_rr1.wav" in r["sample"]]
    if len(matches)!=1:raise RuntimeError(f"Invalid SFZ note/layer mapping: {key} v{layer} matches {len(matches)}")
    region=matches[0]
    filepath=region["sample"]
    if ".." in filepath or not filepath.startswith("samples/"):raise RuntimeError("Unsafe SFZ path")
    url=BASE+filepath
    content=read_limited(url)
    if len(content)<100_000 or content[:4] not in (b"RIFF",b"RIFX") or content[8:12]!=b"WAVE":
        raise RuntimeError("Not a WAV file: "+url)
    wav=root/f"felt_{key}_v{layer}.wav"
    wav.write_bytes(content)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
         "-select_streams","a:0","-show_entries","stream=sample_rate,channels,codec_name",
         "-of","json",str(wav)]))["streams"][0]
    pcm=root/f"felt_{key}_v{layer}.f32le"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(wav),
         "-map","0:a:0","-ar","48000","-ac","1",
         "-f","f32le","-acodec","pcm_f32le",str(pcm)],check=True)
    manifest["notes"].append({
        "id":f"fuchs-mohr-felt-{key}-v{layer}",
        "instrument":"Fuchs & Möhr Felt Upright / Tom Guder",
        "key":key,
        "dynamic":f"source-v{layer} ({region.get('lovel')}-{region.get('hivel')})",
        "stageCharacter":"felt",
        "pcmPath":str(pcm),
        "originalUrl":url,
        "sha256":hashlib.sha256(content).hexdigest(),
        "bytes":len(content),
        "originalRate":int(probe["sample_rate"]),
        "originalChannels":int(probe["channels"]),
        "originalFormat":probe.get("codec_name","PCM WAV"),
        "captureNotes":"Fuchs & Möhr upright felt, 3 velocity layers; not a grand prepared with felt. Source author Tom Guder.",
        "processing":"CueHarbor source-resolution WAV; silence trimmed and tail possibly capped to 12s with 1s fade",
        "license":"Public Domain, author Tom Guder (source Polyphone forum)",
        "roomType":"uncharacterized acoustic room",
        "compression":"lossless PCM WAV (trimming/fade possible)"
    })
    print("Fetched Felt MIDI",key,"layer",layer,"bytes",len(content),"SHA256",hashlib.sha256(content).hexdigest()[:16],flush=True)
(root/"felt-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("Felt acquisitions:",len(manifest["notes"]),": public-domain samples measured in-runner only")
