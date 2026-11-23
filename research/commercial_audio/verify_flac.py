#!/usr/bin/env python3
"""Verify original lossless FLAC commercial references by immutable Git blobs.

No model DSP, no audio analysis, no third-party audio uploaded. Checks source
byte count, Git blob SHA1, SHA256, FLAC STREAMINFO, and full decode via 'flac -t'.
Audio is deleted immediately after each check; only metadata JSON survives.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ALLOWED = {
    "sfzinstruments/SalamanderGrandPiano": ("CC-BY-3.0", "Samples/"),
    "freepats/upright-piano-KW": ("CC0-1.0", "samples/")
}
GIT_SHA = re.compile(r"^[a-f0-9]{40}$")
ID = re.compile(r"^[a-z0-9-]{5,90}$")
MAX_FILE_BYTES = 8_000_000
MAX_TOTAL_BYTES = 50_000_000

def source_url(repo: str, commit: str, path: str, license_id: str) -> str:
    if repo not in ALLOWED or license_id != ALLOWED[repo][0]:
        raise ValueError("source or commercial license not allowed")
    if not GIT_SHA.fullmatch(commit):
        raise ValueError("source must use pinned commit")
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or "\\" in path or not path.endswith(".flac"):
        raise ValueError("unsafe audio path")
    if not path.startswith(ALLOWED[repo][1]):
        raise ValueError("audio folder mismatch")
    return "https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+urllib.parse.quote(path, safe="/")

def streaminfo(head: bytes) -> dict:
    if len(head)<42 or head[:4]!=b"fLaC" or (head[4] & 0x7f)!=0 or int.from_bytes(head[5:8],"big")!=34:
        raise ValueError("missing or corrupt FLAC STREAMINFO")
    block=head[8:42]
    fields=int.from_bytes(block[10:18],"big")
    rate=(fields>>44)&0xfffff
    channels=((fields>>41)&7)+1
    bits=((fields>>36)&31)+1
    samples=fields & ((1<<36)-1)
    if rate not in (44100,48000,88200,96000) or channels not in (1,2) or bits not in (16,24) or samples<rate//4:
        raise ValueError("unexpected FLAC format")
    return {"sampleRate":rate,"channels":channels,"bitsPerSample":bits,
            "pcmSamplesPerChannel":samples,"durationSeconds":round(samples/rate,6),
            "flacStreamMd5":block[18:34].hex()}

def check_manifest(data: dict) -> None:
    if data.get("schema")!="stage-commercial-lossless-flac-pilot-v1":
        raise ValueError("unexpected manifest version")
    items=data.get("items")
    if not isinstance(items,list) or not 1<=len(items)<=24:
        raise ValueError("invalid selection")
    if sum(i.get("bytes",0) for i in items)>MAX_TOTAL_BYTES:
        raise ValueError("download volume too large")
    seen=set()
    for i in items:
        if not ID.fullmatch(i.get("id","")) or i["id"] in seen:
            raise ValueError("bad/duplicate item ID")
        seen.add(i["id"])
        if not isinstance(i.get("bytes"),int) or not 100000<i["bytes"]<=MAX_FILE_BYTES:
            raise ValueError("invalid expected size")
        if not GIT_SHA.fullmatch(i.get("gitBlobSha","")):
            raise ValueError("source Git blob missing")
        source_url(i["repository"],i["commit"],i["path"],i["license"])

def verify_one(item: dict, root: Path) -> dict:
    url=source_url(item["repository"],item["commit"],item["path"],item["license"])
    dest=root/(item["id"]+".flac")
    sha=hashlib.sha256()
    gitblob=hashlib.sha1()
    gitblob.update(f"blob {item['bytes']}\0".encode())
    count=0
    req=urllib.request.Request(url,headers={"User-Agent":"StageSynthOriginalCommercialSampleAudit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=60) as reader,dest.open("wb") as out:
            while chunk:=reader.read(256*1024):
                count+=len(chunk)
                if count>item["bytes"] or count>MAX_FILE_BYTES:
                    raise ValueError("unreviewed source file length")
                out.write(chunk)
                sha.update(chunk)
                gitblob.update(chunk)
        if count!=item["bytes"] or gitblob.hexdigest()!=item["gitBlobSha"]:
            raise ValueError("source integrity error: Git blob/length mismatch")
        with dest.open("rb") as inp: info=streaminfo(inp.read(42))
        # Full bitstream decode test, no PCM output or stored derived audio.
        subprocess.run(["flac","--test","--silent",str(dest)],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=45)
        return {
            "id":item["id"],"instrument":item["instrument"],"recordedPitch":item["recordedPitch"],
            "velocityLayer":item["velocityLayer"],"sourceRepository":item["repository"],
            "sourceCommit":item["commit"],"sourcePath":item["path"],
            "sourceURL":url,"sourceGitBlobSHA1":item["gitBlobSha"],
            "fileSHA256":sha.hexdigest(),"bytes":count,
            "license":item["license"],"streamInfo":info,
            "fullFlacDecoderTest":"passed",
            "physicalHammerVelocityMeasured":False,"metrologicallyCalibrated":False,
            "status":"source bytes, lossless metadata and decodability verified; acoustic calibration NOT approved"
        }
    finally:
        dest.unlink(missing_ok=True)

def main(args: list[str]) -> None:
    if len(args)!=3:
        raise SystemExit("usage: verify_flac.py manifest.json output.json")
    d=json.loads(Path(args[1]).read_text(encoding="utf8"))
    check_manifest(d)
    env=os.environ.get("STAGE_COMMERCIAL_AUDIO_DIR")
    if not env or not Path(env).resolve().is_relative_to(Path("/tmp").resolve()):
        raise ValueError("source audio must be downloaded to /tmp only")
    root=Path(env).resolve()
    root.mkdir(parents=True,exist_ok=True)
    report={"schema":"stage-commercial-lossless-verification-v1",
            "sources":d["sourceCatalog"],"restrictions":d["restrictions"],"verified":[]}
    for i in d["items"]:
        v=verify_one(i,root)
        report["verified"].append(v)
        print(f"VERIFIED-ORIGINAL-FLAC {v['id']}: {v['bytes']} bytes "
              f"{v['streamInfo']['sampleRate']}Hz/{v['streamInfo']['bitsPerSample']}bit "
              f"SHA256={v['fileSHA256']}",flush=True)
    output=Path(args[2]).resolve()
    if output.parent!=root:raise ValueError("report must remain private /tmp")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"VERIFIED-{len(report['verified'])}-FLAC original files; metadata only, no sample retained",flush=True)

if __name__=="__main__":
    main(sys.argv)
