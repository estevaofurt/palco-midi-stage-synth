#!/usr/bin/env python3
"""Can one ZIP member of the licensed Steinway D be reached without the ~1GB ZIP?

Bounded probe: reads <=256 bytes of ONE explicitly selected C4v8 WAV.
No WAV recording is saved, checksum/decoder test NOT performed.
"""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href=None
        self.items=[]
        self.label=""
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.href=dict(attrs).get("href")
            self.label=""
    def handle_data(self,txt):
        if self.href is not None:self.label+=txt
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.items.append((self.label.strip(),self.href))
            self.href=None

def find_member_link(html,filename,listing_url):
    parser=Links()
    parser.feed(html)
    candidates=[urllib.parse.urljoin(listing_url,href) for label,href in parser.items
                if label==filename and "zip" in href.lower()]
    # Never dynamically follow foreign URLs, questionable query strings or directories.
    for x in candidates:
        u=urllib.parse.urlsplit(x)
        if u.scheme=="https" and (u.hostname=="archive.org" or (u.hostname or "").endswith(".archive.org")) and ("bitKlavierGrand_PianoBar_44k16b" in (u.path+"?"+u.query)):
            return x
    return None

def main():
    ident="bitKlavierGrand_PianoBar_44k16b"
    listing=f"https://archive.org/download/{ident}/{ident}.zip/"
    request=urllib.request.Request(listing,headers={"User-Agent":"StageSynthCommercialPianoProvenanceProbe/1.0"})
    with urllib.request.urlopen(request,timeout=25) as r:
        html=r.read(2_000_001)
    if len(html)>2_000_000:raise ValueError("viewer unusually large")
    url=find_member_link(html.decode("utf8",errors="replace"),"C4v8.wav",listing)
    if not url:
        parser=Links()
        parser.feed(html.decode("utf8",errors="replace"))
        candidates=[(label[:70],href[:230]) for label,href in parser.items if "C4v8" in label or "C4v8" in href]
        print("WAV-C4V8 viewer anchor candidates (no audio fetched): "+json.dumps(candidates[:4]))
        print("WAV-C4V8: no individually addressable ZIP-member link verified")
        return
    print("WAV-C4V8: linked member URL found, attempting bounded RIFF-header check")
    try:
        q=urllib.request.Request(url,headers={"User-Agent":"StageSynthCommercialPianoProvenanceProbe/1.0","Range":"bytes=0-255"})
        with urllib.request.urlopen(q,timeout=25) as stream:
            host=urllib.parse.urlsplit(stream.url).hostname or ""
            if host!="archive.org" and not host.endswith(".archive.org"):
                raise ValueError("untrusted redirected audio URL")
            header=stream.read(256)
            code=stream.status
        if header[:4]==b"RIFF" and header[8:12]==b"WAVE":
            print(f"WAV-C4V8: VALID RIFF/WAVE HEADER, HTTP {code}, only {len(header)} bytes inspected; full source NOT verified")
        else:
            print(f"WAV-C4V8: INCONCLUSIVE content; HTTP {code}, only {len(header)} bytes inspected")
    except Exception as e:
        print(f"WAV-C4V8: retrieval INCONCLUSIVE ({type(e).__name__}: {str(e)[:160]})")

if __name__=="__main__":main()
