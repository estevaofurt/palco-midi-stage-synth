#!/usr/bin/env python3
"""Probe archive ZIP *member names* without transferring the ~1GB ZIP or WAV.

Archive.org provides a /zipfile.zip/ directory viewer on some items. It is not
guaranteed; if inaccessible, record inconclusive, never claim WAV integrity.
"""
from __future__ import annotations
import html
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

LIMIT=2_000_000

def listing_url(item:dict)->str:
    ident=item["archiveIdentifier"]
    if not re.fullmatch(r"bitKlavierGrand_(PianoBar|Binaural|HarpOmni)_44k16b",ident):
        raise ValueError("unknown Archive item")
    if item["zipFile"]!=ident+".zip":
        raise ValueError("unexpected ZIP name")
    return "https://archive.org/download/"+ident+"/"+ident+".zip/"

def evaluate_page(body:str,item:dict)->dict:
    body=html.unescape(urllib.parse.unquote(body))
    matches=[x for x in item["expectedMembers"]
             if re.search(r"(?<![a-zA-Z0-9#])"+re.escape(x)+r"(?![a-zA-Z0-9])",body)]
    return {"identifier":item["archiveIdentifier"],"archiveViewerURL":listing_url(item),
            "expectedMembers":item["expectedMembers"],
            "presentInViewerListing":matches,
            "missingOrUnverified":[x for x in item["expectedMembers"] if x not in matches],
            "listingStatus":"expected labels visible, actual ZIP/WAV bytes NOT VERIFIED" if len(matches)==len(item["expectedMembers"]) else "INCONCLUSIVE: not all labels in viewer; no WAV downloaded"}

def probe(item):
    url=listing_url(item)
    req=urllib.request.Request(url,headers={"User-Agent":"StageSynthResearchMetadataProbe/1.0","Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        netloc=urllib.parse.urlsplit(resp.url).hostname or ""
        if not (netloc=="archive.org" or netloc.endswith(".archive.org")):
            raise ValueError("untrusted redirect")
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("no HTML viewer")
        data=resp.read(LIMIT+1)
    if len(data)>LIMIT:raise ValueError("viewer response too large")
    return evaluate_page(data.decode("utf-8",errors="replace"),item)

def main(argv):
    if len(argv)!=3:raise SystemExit("usage: archive_member_probe.py index.json report.json")
    d=json.loads(Path(argv[1]).read_text(encoding="utf8"))
    report={"schema":"stage-steinway-d-archive-member-listing-v1",
            "disclaimer":"A viewer index is NOT audio or ZIP validation; no source audio downloaded",
            "items":[]}
    for item in d["references"]:
        try:
            result=probe(item)
        except Exception as ex:
            result={"identifier":item["archiveIdentifier"],"listingStatus":"UNAVAILABLE", "reason":f"{type(ex).__name__}: {str(ex)[:200]}", "expectedMembers":item["expectedMembers"],"presentInViewerListing":[]}
        report["items"].append(result)
        print(f"VIEWER {item['archiveIdentifier']}: {result['listingStatus']};"
              f" matched={len(result.get('presentInViewerListing',[]))}",flush=True)
    root=Path(os.environ.get("STAGE_ARCHIVE_REPORT_DIR","/none")).resolve()
    path=Path(argv[2]).resolve()
    if root==Path("/none") or not path.is_relative_to(root):raise ValueError("restricted report location")
    path.write_text(json.dumps(report,indent=2)+"\n")
    print("NO AUDIO BYTES TRANSFERRED",flush=True)

if __name__=="__main__":main(sys.argv)
