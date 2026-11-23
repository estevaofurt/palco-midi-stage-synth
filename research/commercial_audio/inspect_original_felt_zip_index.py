#!/usr/bin/env python3
"""Remote ZIP central-directory inspection for author-original Felt Piano.

Fetch ONLY RFC 7233 HTTP Range bytes from author's public Google Drive ZIP.
zipfile.ZipFile uses a strict bounded seek/read interface. The complete archive
is never downloaded; WAV audio is never requested in this indexing step.
"""
from __future__ import annotations
from collections import OrderedDict
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import zipfile

FILE_ID="1XbIZgTdKoR2KxIyKM-CkEweS3HI4ieHu"
URL=f"https://drive.usercontent.google.com/download?id={FILE_ID}&export=download&confirm=t"
SIZE_MIN=100_000
SIZE_MAX=3_000_000_000
BLOCK=256*1024
MAX_INDEX_TRANSFER=12*1024*1024
MAX_REQUESTS=64
MAX_MEMBERS=4000
CONTENT_RANGE=re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")
ALLOWED_HOSTS=("drive.google.com","drive.usercontent.google.com")

def parse_content_range(value: str, requested_start: int, requested_end: int):
    m=CONTENT_RANGE.fullmatch(value.strip())
    if not m:raise ValueError("missing or malformed Content-Range")
    start,end,total=map(int,m.groups())
    if start!=requested_start or end!=requested_end or not SIZE_MIN<=total<=SIZE_MAX:
        raise ValueError("Range server did not honor requested bytes/total")
    return total

def ranged_get(url,start,end):
    if url!=URL or start<0 or end<start or end-start>=BLOCK:
        raise ValueError("invalid bounded source range")
    request=urllib.request.Request(url,headers={
      "User-Agent":"StageSynthCommercialFeltZipSourceIndex/1.0",
      "Range":f"bytes={start}-{end}",
      "Accept":"application/octet-stream,application/zip,*/*;q=0.1"
    })
    with urllib.request.urlopen(request,timeout=25) as response:
        host=urllib.parse.urlsplit(response.url).hostname or ""
        if host not in ALLOWED_HOSTS and not host.endswith(".googleusercontent.com"):
            raise ValueError("untrusted source redirect")
        if response.status!=206:
            raise ValueError(f"source denied byte-range request: HTTP {response.status}")
        total=parse_content_range(response.headers.get("Content-Range",""),start,end)
        data=response.read(end-start+2)
    if len(data)!=end-start+1:raise ValueError("incorrect byte length")
    return data,total

def source_total():
    b,total=ranged_get(URL,0,511)
    if b[:4] not in (b"PK\x03\x04",b"PK\x05\x06"):
        raise ValueError("author source does not begin as ZIP")
    return total

class RemoteZipReader:
    def __init__(self,total,fetcher=None,max_transfer=MAX_INDEX_TRANSFER,max_requests=MAX_REQUESTS):
        if not SIZE_MIN<=total<=SIZE_MAX:raise ValueError("source ZIP total outside budget")
        self.total=total
        self.pos=0
        self.fetcher=fetcher or (lambda s,e:ranged_get(URL,s,e))
        self.max_transfer=max_transfer
        self.max_requests=max_requests
        self.transferred=0
        self.requests=0
        self.cache=OrderedDict()
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=io.SEEK_SET):
        p=offset if whence==io.SEEK_SET else (self.pos+offset if whence==io.SEEK_CUR else self.total+offset if whence==io.SEEK_END else None)
        if p is None or not 0<=p<=self.total:raise ValueError("invalid ZIP seek")
        self.pos=p
        return p
    def _block(self,start):
        if start in self.cache:
            self.cache.move_to_end(start)
            return self.cache[start]
        end=min(start+BLOCK,self.total)-1
        if self.requests>=self.max_requests or self.transferred+end-start+1>self.max_transfer:
            raise ValueError("ZIP central directory exceeded network budget")
        data,source_size=self.fetcher(start,end)
        if source_size!=self.total:raise ValueError("source ZIP changed during inspection")
        self.requests+=1
        self.transferred+=len(data)
        self.cache[start]=data
        if len(self.cache)>5:self.cache.popitem(last=False)
        return data
    def read(self,n=-1):
        if n is None or n<0:n=self.total-self.pos
        if n>2*1024*1024:raise ValueError("unbounded ZIP reader request")
        n=min(n,self.total-self.pos)
        pieces=[]
        while n:
            block_start=(self.pos//BLOCK)*BLOCK
            block=self._block(block_start)
            off=self.pos-block_start
            take=min(n,len(block)-off)
            if take<=0:raise ValueError("invalid ZIP range buffer")
            pieces.append(block[off:off+take])
            self.pos+=take
            n-=take
        return b"".join(pieces)
    def close(self):self.cache.clear()

def inspect_directory(reader):
    with zipfile.ZipFile(reader,"r",allowZip64=True) as archive:
        infos=archive.infolist()
        if len(infos)>MAX_MEMBERS:raise ValueError("unreasonably many WAV members")
        result=[]
        for z in infos:
            if z.is_dir():continue
            name=z.filename
            if name.startswith("/") or ".." in name.replace("\\","/").split("/") or "\x00" in name:
                raise ValueError("unsafe file path in ZIP")
            if not name.lower().endswith(".wav"):
                # Ancillary metadata can exist; don't assume every file is audio.
                continue
            if z.file_size>50_000_000 or z.compress_size>35_000_000:
                raise ValueError("individual WAV exceeds planned extraction budget")
            result.append({
             "name":name,"compressedBytes":z.compress_size,
             "uncompressedBytes":z.file_size,"crc32FromZipDirectory":f"{z.CRC:08x}",
             "compressionMethod":z.compress_type,
             "filenameUtf8":bool(z.flag_bits & 0x800)
            })
        if not result:raise ValueError("ZIP has no WAV members")
        return result

def main(argv):
    if len(argv)!=2:raise SystemExit("usage: inspect_original_felt_zip_index.py metadata-only.json")
    root=os.environ.get("STAGE_FELT_REPORT_DIR")
    out=Path(argv[1]).resolve()
    if not root or out.parent!=Path(root).resolve() or not out.is_relative_to(Path("/tmp").resolve()):
        raise ValueError("restricted /tmp metadata output")
    total=source_total()
    reader=RemoteZipReader(total)
    items=inspect_directory(reader)
    report={"schema":"stage-felt-author-original-zip-directory-v1",
      "sourceAuthor":"Tom Guder",
      "sourceFileName":"FuchsUndMoehrSamplesWAV16bit.zip",
      "sourceFileId":FILE_ID,
      "authorLicenseStatement":"Public Domain on original Polyphone forum",
      "zipTotalBytesFromHttpRange":total,
      "wavMemberCount":len(items),
      "totalWavUncompressedBytes":sum(x["uncompressedBytes"] for x in items),
      "indexedNetworkTransferBytes":reader.transferred,
      "indexedHttpRequests":reader.requests,
      "originalZipOrWavsFullyDownloaded":False,
      "sourceWholeZipSha256Known":False,
      "sourceWavSha256Known":False,
      "scope":"original ZIP central directory only, WAV bytes not downloaded",
      "members":items
    }
    # Filename discovery only, no PCM/WAV access. Print a short source evidence list.
    import os as _os
    from collections import Counter
    print("FELT-ORIGINAL-LAYERS:",json.dumps(Counter(x["name"].split("/")[0] for x in items)),flush=True)
    target_list=[f"{folder}/{prefix}{n}.wav" for folder,prefix in (("forte","f"),("mezzo","m"),("piano","p")) for n in (36,48,60,72,84)]
    present={x["name"] for x in items}
    print("FELT-ORIGINAL-TARGETS:",json.dumps([{"name":n,"found":n in present} for n in target_list]),flush=True)
    print("FELT-ORIGINAL-ZIP-FIRST:",json.dumps([x["name"] for x in items[:15]],ensure_ascii=False),flush=True)
    target=[x for x in items if re.search(r"C[246](?![0-9])",_os.path.basename(x["name"]),re.I)]
    print("FELT-ORIGINAL-ZIP-KEYS:",json.dumps([x["name"] for x in target[:35]],ensure_ascii=False),flush=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"FELT-REMOTE-DIRECTORY: totalZip={total} WAVmembers={len(items)} "
          f"transfer={reader.transferred} requests={reader.requests}, "
          "NO WAV PAYLOAD DOWNLOADED",flush=True)

if __name__=="__main__":main(sys.argv)
