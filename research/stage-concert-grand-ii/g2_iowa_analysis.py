"""G2.02b: Iowa piano, pinned mirror checksums; same windows as C5."""
import argparse, hashlib, io, json, math, time, tomllib, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_c5_analysis import measure

PIN="3127691df600da0c20a44f8e59db514e11df7197"
BASE=f"https://huggingface.co/datasets/sondalex/university-iowa-piano-samples/resolve/{PIN}/"
ORIGINAL="https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/piano/"
NOTES=range(3,8)
LEVELS=("pp","mf","ff")

def fetch(url,limit):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StageSynth-G2-research"})
            with urllib.request.urlopen(req,timeout=45) as r:
                data=r.read(limit+1)
            if len(data)>limit:raise ValueError("oversize source")
            return data
        except (OSError,ValueError) as e:
            last=e
            if attempt<2:time.sleep(2**attempt)
    raise RuntimeError(f"download failed: {url}") from last

def adapt(y,fs):
    if y.ndim!=2 or y.shape[1] not in (1,2) or fs not in (44100,48000) or not np.isfinite(y).all():raise ValueError("source format")
    if fs!=48000:
        d=math.gcd(48000,fs)
        y=resample_poly(y,48000//d,fs//d,axis=0)
    # Identical mono channels only for compatibility with power averaging.
    if y.shape[1]==1:y=np.repeat(y,2,axis=1)
    return y

def one(note,level,checksums):
    name=f"Piano.{level}.C{note}.aiff"
    rel="university_iowa/"+name
    expected=checksums[rel]
    url=BASE+rel
    data=fetch(url,20_000_000)
    sha=hashlib.sha256(data).hexdigest()
    if sha!=expected or data[:4]!=b"FORM":raise ValueError("source checksum or AIFF mismatch: "+name)
    y,fs=sf.read(io.BytesIO(data),always_2d=True,dtype="float64")
    row=measure(adapt(y,fs),48000,12*(note+1))
    row.update(note=f"C{note}",dynamic=level,source_rate=fs,source_channels=y.shape[1],source_duration_s=len(y)/fs,source_peak_dbfs=20*math.log10(max(float(np.max(np.abs(y))),1e-30)),sha256=sha,bytes=len(data),url=url,original_url=ORIGINAL+name)
    return row

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    raw=fetch(BASE+"checksums.toml",100_000)
    checksums=tomllib.loads(raw.decode("utf-8"))["sha256"]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(one,n,v,checksums) for n in NOTES for v in LEVELS]
        rows=[f.result() for f in futures]
    assert len(rows)==15
    result={"source":{"instrument":"University of Iowa Steinway grand (Model B per prior project records)","author":"Lawrence Fritts / University of Iowa Electronic Music Studios","permission":"University states unrestricted use for projects; not a named CC license","permission_url":"https://theremin.music.uiowa.edu/mis.html","mirror_commit":PIN,"mirror_checksums_sha256":hashlib.sha256(raw).hexdigest()},"limitations":["checksum against pinned mirror; not independent original-server verification","recording and editing conditions differ from C5","mono duplicate is not stereo capture","resampling cannot restore content above source Nyquist","pp/mf/ff not equivalent to C5 v1/v8/v16","late windows can contain release or noise; no direct sustain or hammer force inference"],"cases":rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    for row in rows:
        w=row["windows"]
        print("G2_IOWA_CASE "+json.dumps({"note":row["note"],"dynamic":row["dynamic"],"source_rate":row["source_rate"],"channels":row["source_channels"],"duration":row["source_duration_s"],"h2":w.get("0.25-0.75",{}).get("partial_band_relative_db",[None,None])[1],"early_low":w.get("0-0.02",{}).get("below_0_7_f0_pct"),"rms":{k:w[k]["rms_dbfs"] for k in w}}),flush=True)
if __name__=="__main__":main()
