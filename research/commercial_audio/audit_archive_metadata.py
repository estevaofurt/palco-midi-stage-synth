#!/usr/bin/env python3
"""Index Archive.org ZIP *metadata* for a commercially licensed Steinway D.

This tool NEVER downloads or opens ZIP WAV recordings. It verifies item identity,
metadata license claim, file names/sizes/checksums, then writes JSON only.
Expected inner member names remain UNVERIFIED until an actual bounded ZIP test.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

SCHEMA="stage-commercial-archive-source-index-v1"
ALLOWED={
 "bitKlavierGrand_PianoBar_44k16b",
 "bitKlavierGrand_Binaural_44k16b",
 "bitKlavierGrand_HarpOmni_44k16b"
}
HASH_MD5=re.compile(r"^[0-9a-f]{32}$",re.I)
HASH_SHA1=re.compile(r"^[0-9a-f]{40}$",re.I)
MAX_RESPONSE=5*1024*1024

def validate_manifest(data):
    if data.get("schema") != SCHEMA:raise ValueError("unknown manifest")
    r=data.get("references")
    if not isinstance(r,list) or len(r)!=3:raise ValueError("expected three mic-image records")
    found=set()
    for x in r:
        ident=x.get("archiveIdentifier","")
        if ident not in ALLOWED or ident in found:raise ValueError("untrusted/duplicate Archive item")
        found.add(ident)
        if x.get("zipFile")!=ident+".zip":raise ValueError("unexpected archive ZIP")
        if x.get("license")!="CC-BY-4.0":raise ValueError("unauthorized archive license")
        if not isinstance(x.get("expectedMembers"),list) or not 1<=len(x["expectedMembers"])<=16:
            raise ValueError("unbounded expected member list")
        if any(not re.fullmatch(r"[A-Za-z#0-9]+\.wav",s) for s in x["expectedMembers"]):
            raise ValueError("unexpected member label")

def extract_metadata(item, expect):
    if str(item.get("is_dark", "0")) in ("1","true","True"):
        raise ValueError("Archive item dark/unavailable")
    if item.get("metadata",{}).get("identifier")!=expect["archiveIdentifier"]:
        raise ValueError("Archive identifier mismatch")
    files=[f for f in item.get("files",[]) if f.get("name")==expect["zipFile"]]
    if len(files)!=1:raise ValueError("Archive audio ZIP missing/ambiguous")
    f=files[0]
    n=int(f.get("size","0"))
    if not 200_000_000<n<3_000_000_000:raise ValueError("archive size outside reviewed scope")
    md5=str(f.get("md5","")).lower()
    sha1=str(f.get("sha1","")).lower()
    if not HASH_MD5.fullmatch(md5):raise ValueError("missing source MD5")
    if sha1 and not HASH_SHA1.fullmatch(sha1):raise ValueError("malformed source SHA1")
    meta=item["metadata"]
    # Some Archive items state license in 'licenseurl', others only description.
    lic=str(meta.get("licenseurl") or meta.get("license") or "")
    license_confirmed=("creativecommons.org/licenses/by/4.0" in lic)
    return {
      "identifier":expect["archiveIdentifier"],
      "zipName":f["name"],"zipSizeBytes":n,
      "zipMd5":md5,"zipSha1":sha1 or None,
      "licenseClaimFromAuthor":"CC-BY-4.0",
      "licenseClaimFromArchive":lic or None,
      "archiveExplicitCcBy4":license_confirmed,
      "creator":meta.get("creator"),"title":meta.get("title"),
      "archiveItemURL":expect["source"],
      "source":f"https://archive.org/metadata/{expect['archiveIdentifier']}",
      "expectedWavMembersNotVerified":expect["expectedMembers"],
      "status":"SOURCE ZIP INDEXED FROM ARCHIVE METADATA; ZIP bytes and member WAVs NOT downloaded"
    }

def fetch_json(url: str):
    req=urllib.request.Request(url,headers={"User-Agent":"StageSynthProvenanceAudit/1.0"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        if not str(resp.url).startswith("https://archive.org/"):
            raise ValueError("untrusted Archive redirect")
        buf=resp.read(MAX_RESPONSE+1)
    if len(buf)>MAX_RESPONSE:raise ValueError("Archive metadata response too large")
    return json.loads(buf.decode("utf-8"))

def main(argv):
    if len(argv)!=3:raise SystemExit("usage: audit_archive_metadata.py manifest.json report.json")
    data=json.loads(Path(argv[1]).read_text(encoding="utf8"))
    validate_manifest(data)
    report={"schema":"stage-commercial-archive-metadata-audit-v1","sourceManifest":argv[1],
      "notice":"No source WAV or ZIP was fetched. Metadata checksums are not proof of downloaded bytes.",
      "items":[]}
    for x in data["references"]:
        obj=fetch_json("https://archive.org/metadata/"+x["archiveIdentifier"])
        row=extract_metadata(obj,x)
        report["items"].append(row)
        print(f"INDEXED {row['identifier']}: ZIP size={row['zipSizeBytes']} MD5={row['zipMd5']} "
              f"Archive CC-BY4 explicit={row['archiveExplicitCcBy4']}",flush=True)
    out=Path(argv[2]).resolve()
    root=os.environ.get("STAGE_ARCHIVE_REPORT_DIR")
    if not root or not out.is_relative_to(Path(root).resolve()):raise ValueError("report output directory restricted")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"INDEXED-{len(report['items'])}-ARCHIVES, no ZIP/WAV downloaded",flush=True)

if __name__=="__main__":main(sys.argv)
