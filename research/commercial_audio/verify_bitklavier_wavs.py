#!/usr/bin/env python3
"""Download only seven INDIVIDUAL original Steinway D WAVs from Archive ZIP view.

No full 1GB ZIP downloads, no audio files in Git or Actions artifacts.
Computes SHA256 of actual bytes and verifies WAV PCM/format, deleting source
data immediately after each file. Does NOT measure or infer physical parameters.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import wave

IDENT=re.compile(r"^bitKlavierGrand_(PianoBar|Binaural|HarpOmni)_44k16b$")
NAME=re.compile(r"^(C2v8|C4v1|C4v8|C4v16|C6v8)\.wav$")
MAX_ONE=30_000_000
MAX_TOTAL=100_000_000

def source_url(item):
    ident=item.get("archiveIdentifier","")
    member=item.get("memberName","")
    if not IDENT.fullmatch(ident):
        raise ValueError("archive identifier not in reviewed allowlist")
    if not NAME.fullmatch(member):
        raise ValueError("unreviewed piano WAV note/layer")
    if item.get("zipFile")!=ident+".zip" or item.get("license")!="CC-BY-4.0":
        raise ValueError("unreviewed archive/license")
    if item.get("expectedWavRate")!=44100 or item.get("expectedBits")!=16:
        raise ValueError("unreviewed audio format")
    encoded=urllib.parse.quote(ident+"/"+member,safe="")
    return f"https://archive.org/download/{ident}/{ident}.zip/{encoded}"

def check_manifest(manifest):
    if manifest.get("schema")!="stage-steinway-d-selective-wav-pilot-v1":
        raise ValueError("bad manifest")
    items=manifest.get("items")
    if not isinstance(items,list) or len(items)!=7:
        raise ValueError("unexpected pilot file count")
    ids=set()
    for x in items:
        if not re.fullmatch(r"steinway-d-[a-z0-9-]{4,60}",x.get("id","")):
            raise ValueError("unsafe id")
        if x["id"] in ids:raise ValueError("duplicate id")
        ids.add(x["id"])
        source_url(x)

def verify_wav(item,dir_path):
    url=source_url(item)
    file=dir_path/(item["id"]+".wav")
    size=0
    digest=hashlib.sha256()
    req=urllib.request.Request(url,headers={
       "User-Agent":"StageSynthCommercialSteinwaySourceCheck/1.0",
       "Accept":"audio/wav,application/octet-stream,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=90) as res, file.open("wb") as dst:
            hostname=urllib.parse.urlsplit(res.url).hostname or ""
            if hostname!="archive.org" and not hostname.endswith(".archive.org"):
                raise ValueError("untrusted redirected source")
            while chunk:=res.read(128*1024):
                size+=len(chunk)
                if size>MAX_ONE:raise ValueError("source WAV exceeds reviewed 30MB limit")
                dst.write(chunk)
                digest.update(chunk)
        if size<64:raise ValueError("source WAV too short")
        with wave.open(str(file),"rb") as reader:
            info={
             "channels":reader.getnchannels(),
             "rateHz":reader.getframerate(),
             "bitsPerSample":reader.getsampwidth()*8,
             "frames":reader.getnframes(),
             "durationSeconds":round(reader.getnframes()/reader.getframerate(),6),
             "compression":reader.getcomptype()
            }
        if (info["channels"]!=item["expectedChannels"] or
            info["rateHz"]!=item["expectedWavRate"] or
            info["bitsPerSample"]!=item["expectedBits"] or
            info["compression"]!="NONE" or info["durationSeconds"]<.1):
            raise ValueError("unexpected WAV source header/format")
        return {
          "id":item["id"],"instrument":item["instrument"],"mic":item["mic"],
          "sourceURL":url,"archiveIdentifier":item["archiveIdentifier"],
          "memberName":item["memberName"],"license":item["license"],
          "bytes":size,"sha256":digest.hexdigest(),"wav":info,
          "status":"original ZIP-member WAV fully downloaded, RIFF parsed, hashed, immediately deleted",
          "hammerVelocityKnown":False,"bodyTransferCalibrated":False
        }
    finally:
        file.unlink(missing_ok=True)

def main(args):
    if len(args)!=3:raise SystemExit("usage: verify_bitklavier_wavs.py manifest.json report.json")
    data=json.loads(Path(args[1]).read_text(encoding="utf8"))
    check_manifest(data)
    env=os.environ.get("STAGE_ARCHIVE_REPORT_DIR")
    if not env or not Path(env).resolve().is_relative_to(Path("/tmp").resolve()):
        raise ValueError("temporary source directory must be inside /tmp")
    root=Path(env).resolve()
    root.mkdir(parents=True,exist_ok=True)
    report={"schema":"stage-commercial-steinway-d-wav-provenance-v1",
            "sourceLicense":"CC-BY-4.0",
            "sourceAuthor":"Dan Trueman/Princeton bitKlavier Grand",
            "caveats":data["caveats"],
            "sourceAudioIncluded":False,"items":[]}
    tot=0
    for item in data["items"]:
        row=verify_wav(item,root)
        tot+=row["bytes"]
        if tot>MAX_TOTAL:raise ValueError("combined download exceeds 100MB budget")
        report["items"].append(row)
        print(f"VERIFIED-STEINWAY-D {row['id']}: {row['bytes']} bytes "
              f"{row['wav']['rateHz']}Hz/{row['wav']['bitsPerSample']}bit, "
              f"SHA256={row['sha256']}",flush=True)
    out=Path(args[2]).resolve()
    if out.parent!=root:raise ValueError("report must remain in controlled temp folder")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"VERIFIED-{len(report['items'])}-STEINWAY-D-WAV, {tot} source bytes, no audio retained",flush=True)

if __name__=="__main__":
    main(sys.argv)
