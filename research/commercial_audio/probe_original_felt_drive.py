#!/usr/bin/env python3
"""Safely probe author-linked public Felt WAV ZIP for source access and size.

The author linked FuchsUndMoehrSamplesWAV16bit.zip on Polyphone and declared
the WAV samples 'Public Domain'. This probe does NOT download the archive.
Every response reads at most 512 bytes, does not store audio, and never logs
download-confirmation tokens. The file remains unverified until full byte/hash
and ZIP-member checks are successfully completed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

FILE_ID="1XbIZgTdKoR2KxIyKM-CkEweS3HI4ieHu"
ORIGIN="https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr"
FILENAME="FuchsUndMoehrSamplesWAV16bit.zip"
MAX_READ=512
ALLOWED_HOSTS={"drive.google.com","drive.usercontent.google.com","docs.google.com"}
ALLOWED_SUFFIXES=(".googleusercontent.com",)
REQUEST_URLS=[
 f"https://drive.google.com/uc?export=download&id={FILE_ID}",
 f"https://drive.google.com/uc?export=download&confirm=t&id={FILE_ID}",
 f"https://drive.usercontent.google.com/download?id={FILE_ID}&export=download&confirm=t",
]

def safe_host(value: str) -> bool:
    return value in ALLOWED_HOSTS or any(value.endswith(s) for s in ALLOWED_SUFFIXES)

def classify_headers(status: int, url: str, headers: dict, first: bytes) -> dict:
    hostname=urllib.parse.urlsplit(url).hostname or ""
    if not safe_host(hostname):
        raise ValueError("unexpected redirected host")
    ctype=headers.get("Content-Type","").split(";",1)[0].strip().lower()
    disp=headers.get("Content-Disposition","")
    length=headers.get("Content-Length")
    cr=headers.get("Content-Range","")
    if length and (not length.isdecimal() or int(length)>5_000_000_000):
        raise ValueError("unexpected content length")
    if len(first)>MAX_READ:raise ValueError("unbounded response read")
    zip_magic=first[:4] in (b"PK\x03\x04",b"PK\x05\x06",b"PK\x07\x08")
    filename_match=(FILENAME.lower() in disp.lower())
    html_likely=first.lstrip().lower().startswith((b"<!doctype",b"<html",b"<head"))
    return {
      "httpStatus":status, "redirectedHost":hostname,
      "contentType":ctype, "advertisedSizeBytes":int(length) if length else None,
      "contentRangePresent":bool(cr),
      "acceptRanges":headers.get("Accept-Ranges"),
      "contentDispositionNamesExpectedZip":filename_match,
      "firstBytesAreZip":zip_magic,
      "looksLikeHtmlConfirmationOrLogin":html_likely or ctype=="text/html",
      "probeBytesRead":len(first),
      "sourceBytesFullyVerified":False,
      "status":"ZIP HEADER REACHABLE, NOT DOWNLOADED" if zip_magic else "INCONCLUSIVE OR ACCESS GATED"
    }

def fetch_probe(url: str) -> dict:
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or not safe_host(u.hostname or "") or FILE_ID not in u.query:
        raise ValueError("unexpected source request")
    req=urllib.request.Request(url,headers={
      "User-Agent":"Mozilla/5.0 StageSynthCommercialFeltSourceAudit/1.0",
      "Range":"bytes=0-511",
      "Accept":"application/zip,application/octet-stream,text/html;q=0.5,*/*;q=0.1"
    })
    try:
        with urllib.request.urlopen(req,timeout=22) as response:
            return classify_headers(response.status,response.url,dict(response.headers),response.read(MAX_READ))
    except urllib.error.HTTPError as ex:
        # Status itself is evidence; do not log quota/auth tokens or body.
        return {"httpStatus":ex.code,"status":"HTTP FAILURE / ACCESS NOT VERIFIED",
                "firstBytesAreZip":False,"sourceBytesFullyVerified":False}
    except (urllib.error.URLError,TimeoutError) as ex:
        return {"httpStatus":None,"status":"NETWORK INCONCLUSIVE",
                "errorType":type(ex).__name__,"firstBytesAreZip":False,
                "sourceBytesFullyVerified":False}

def main(args: list[str]) -> None:
    if len(args)!=2:raise SystemExit("usage: probe_original_felt_drive.py report.json")
    root=os.environ.get("STAGE_FELT_REPORT_DIR")
    if not root or not Path(root).resolve().is_relative_to(Path("/tmp").resolve()):
        raise ValueError("metadata output must be under private /tmp")
    out=Path(args[1]).resolve()
    if out.parent!=Path(root).resolve():raise ValueError("unexpected output path")
    report={"schema":"stage-commercial-author-felt-access-probe-v1","author":"Tom Guder",
      "instrument":"Fuchs & Möhr Felt Upright","authorPublication":ORIGIN,
      "declaredLicense":"Public Domain (author's own statement; final commercial due diligence pending)",
      "authorZipFilename":FILENAME,"sourceProvider":"Google Drive","sourceFileId":FILE_ID,
      "notice":"512 bytes maximum per request, no ZIP/WAV archive stored, no original file SHA256 or internal WAV validation",
      "probes":[]}
    for idx,url in enumerate(REQUEST_URLS,1):
        result=fetch_probe(url)
        report["probes"].append({"methodIndex":idx,**result})
        print(f"FELT-PROBE-{idx}: {result['status']}; HTTP={result.get('httpStatus')}; "
              f"ZIP magic={result.get('firstBytesAreZip')}; "
              f"advertised size={result.get('advertisedSizeBytes')}",flush=True)
    report["zipHeaderAccessible"]=any(p.get("firstBytesAreZip") for p in report["probes"])
    report["fullZipValidated"]=False
    report["licenseConfirmedFromAuthorForum"]=True
    report["commercialAudioCorpusGatePassed"]=False
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"FELT-ORIGIN: header accessible={report['zipHeaderAccessible']}; "
          "no audio stored; source ZIP UNVERIFIED",flush=True)

if __name__=="__main__":main(sys.argv)
