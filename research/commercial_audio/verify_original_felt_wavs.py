#!/usr/bin/env python3
"""Verify 15 author-original Felt WAV members without downloading entire 649MB ZIP.

Source is the public-domain ZIP explicitly linked by creator Tom Guder.
Use bounded HTTP range to read ONLY selected compressed ZIP member spans;
ZipFile checks CRC32 on decompression. Compute SHA256 of each original WAV.
Never publish or retain audio/ZIP data after each check. Does not calibrate
martlet physics, dynamic velocity, or before/after felt treatment.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import wave
import zipfile
import zlib

from inspect_original_felt_zip_index import RemoteZipReader, source_total

MAX_TRANSFER_BYTES=140*1024*1024
MAX_HTTP_REQUESTS=700
MAX_SAMPLE_BYTES=30*1024*1024

def check_manifest(m):
    if m.get("schema")!="stage-commercial-felt-author-original-selective-v1":
        raise ValueError("wrong source schema")
    if m.get("sourceFileId")!="1XbIZgTdKoR2KxIyKM-CkEweS3HI4ieHu":
        raise ValueError("source not author's ZIP")
    if m.get("authorDeclaredLicense")!="Public Domain":
        raise ValueError("source commercial license not author-declared")
    if m.get("sourceByteLengthByHTTPRange")!=648995046:
        raise ValueError("ZIP source size not pinned to last inspected source")
    items=m.get("items")
    if not isinstance(items,list) or len(items)!=15:
        raise ValueError("expected 15 note/layer sample entries")
    expected={f"{layer}/{p}{midi}.wav" for layer,p in (("piano","p"),("mezzo","m"),("forte","f"))
              for midi in (36,48,60,72,84)}
    got={x.get("member","") for x in items}
    if got!=expected:raise ValueError("sample names or count differ from reviewed ZIP")
    for x in items:
        if x.get("midi") not in (36,48,60,72,84):
            raise ValueError("unapproved pitch")
        if x.get("layerLabel") not in ("piano","mezzo","forte"):
            raise ValueError("unapproved layer")

def verify_member(archive,entry):
    member=entry["member"]
    info=archive.getinfo(member)
    if info.is_dir() or info.file_size<30000 or info.file_size>MAX_SAMPLE_BYTES:
        raise ValueError("unsupported WAV size")
    if info.compress_size>MAX_SAMPLE_BYTES:
        raise ValueError("unsupported ZIP member compressed size")
    name=info.filename
    if name!=member or name.startswith("/") or ".." in name.replace("\\","/").split("/"):
        raise ValueError("unsafe ZIP file")
    sha=hashlib.sha256()
    crc=0
    actual=0
    with tempfile.TemporaryFile(mode="w+b") as out,archive.open(info,"r") as stream:
        while piece:=stream.read(128*1024):
            actual+=len(piece)
            if actual>info.file_size or actual>MAX_SAMPLE_BYTES:
                raise ValueError("decompressed bytes exceed ZIP metadata")
            sha.update(piece)
            crc=zlib.crc32(piece,crc)
            out.write(piece)
        if actual!=info.file_size or crc&0xffffffff!=info.CRC:
            raise ValueError("ZIP member CRC/length mismatch")
        out.seek(0)
        with wave.open(out,"rb") as reader:
            wav={
             "sampleRateHz":reader.getframerate(),
             "bitDepth":reader.getsampwidth()*8,
             "channels":reader.getnchannels(),
             "frames":reader.getnframes(),
             "durationSeconds":round(reader.getnframes()/reader.getframerate(),5),
             "compression":reader.getcomptype()
            }
    if (wav["sampleRateHz"] not in (44100,48000,96000)
        or wav["bitDepth"]!=16
        or wav["channels"]!=2
        or wav["compression"]!="NONE"
        or wav["durationSeconds"]<0.2):
        raise ValueError("WAV source format not matching author's claims")
    return {
       "id":entry["id"],"member":member,
       "nominalPitch":entry["nominalPitch"],"midi":entry["midi"],
       "layerLabel":entry["layerLabel"],"wav":wav,
       "sourceUncompressedBytes":actual,
       "sourceCompressedBytes":info.compress_size,
       "zipMemberCrc32":f"{info.CRC:08x}",
       "sourceWavSha256":sha.hexdigest(),
       "sourceAudioPersisted":False,
       "isPhysicalHammerMeasurement":False,
       "wasFeltAblationPaired":False
    }

def main(args):
    if len(args)!=3:raise SystemExit("usage: verify_original_felt_wavs.py manifest.json report.json")
    manifest=json.loads(Path(args[1]).read_text(encoding="utf8"))
    check_manifest(manifest)
    total=source_total()
    if total!=manifest["sourceByteLengthByHTTPRange"]:
        raise ValueError("author ZIP changed since source index")
    root=os.environ.get("STAGE_FELT_REPORT_DIR")
    out=Path(args[2]).resolve()
    if not root or not out.parent==Path(root).resolve() or not out.is_relative_to(Path("/tmp").resolve()):
        raise ValueError("report must remain in metadata-only /tmp folder")
    reader=RemoteZipReader(total,max_transfer=MAX_TRANSFER_BYTES,max_requests=MAX_HTTP_REQUESTS)
    report={
      "schema":"stage-commercial-original-felt-verified-wav-sha256-v1",
      "sourceFileId":manifest["sourceFileId"],
      "sourceAuthor":manifest["author"],
      "sourceDeclaredLicense":manifest["authorDeclaredLicense"],
      "sourceZipTotalBytesFromRange":total,
      "sourceAudioUploaded":False,"sourceWholeZipSHA256Verified":False,
      "limits":manifest["limits"],"files":[]
    }
    with zipfile.ZipFile(reader,"r") as archive:
        for entry in manifest["items"]:
            row=verify_member(archive,entry)
            report["files"].append(row)
            print(f"FELT-ORIGINAL-VERIFIED {row['member']}: {row['sourceUncompressedBytes']} bytes, "
                  f"{row['wav']['sampleRateHz']}Hz/{row['wav']['bitDepth']}bit/"
                  f"{row['wav']['channels']}ch, SHA256={row['sourceWavSha256']}",flush=True)
    report["sourceRangeTransferBytes"]=reader.transferred
    report["sourceHttpRequests"]=reader.requests
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"FELT-ORIGINAL-{len(report['files'])}-VERIFIED "
          f"transfer={reader.transferred} bytes requests={reader.requests}; "
          "originals NOT retained",flush=True)

if __name__=="__main__":main(sys.argv)
