"""G2.02a: verified C5 recordings, descriptive stereo power analysis only."""
import argparse, hashlib, json, math, tempfile, urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import periodogram
from scipy.fft import rfft, next_fast_len

def db(p):
    return float(10*np.log10(max(float(p),1e-30)))

def onset_v1(y,fs):
    n=round(.002*fs)
    p=np.mean(y[:len(y)//n*n].reshape(-1,n,y.shape[1])**2,axis=(1,2))
    if not len(p) or p.max()<1e-12: raise ValueError("silent")
    ix=np.flatnonzero(p>=max(p.max()*1e-4,1e-12))
    return int(ix[0]*n)

def onset_details(y,fs):
    # RMS over 2ms; sustained -26dB peak-relative trigger, limited backtracking.
    # This identifies acoustic onset operationally, not physical hammer contact.
    n=round(.002*fs)
    p=np.mean(y[:len(y)//n*n].reshape(-1,n,y.shape[1])**2,axis=(1,2))
    if len(p)<3 or p.max()<1e-12: raise ValueError("silent or short")
    peak=float(p.max()); rms=np.sqrt(p); pk=math.sqrt(peak)
    hi=max(.05*pk,1e-6); lo=max(.02*pk,1e-6)
    active=rms>=hi
    hits=np.flatnonzero(active[:-2]&active[1:-1]&active[2:])
    if not len(hits):raise ValueError("no sustained onset")
    hit=int(hits[0]); start=hit
    for _ in range(6):
        if start==0 or rms[start-1]<lo:break
        start-=1
    legacy=onset_v1(y,fs)
    before=rms[max(0,start-50):start]
    contrast=20*math.log10(max(pk,1e-15)/max(float(np.median(before)) if len(before) else 0,1e-15)) if len(before) else None
    local=float(np.max(rms[start:min(len(rms),start+40)]))
    return {"sample":start*n,"v1_sample":legacy,"shift_ms":1000*(start*n-legacy)/fs,
            "method":"rms-v2-2ms-3-consecutive-5pct-peak-2pct-backtrack-12ms",
            "trigger_sample":hit*n,"pre_peak_contrast_db":contrast,
            "first_80ms_peak_relative_db":20*math.log10(max(local/pk,1e-15)),
            "flags":(["large_shift_review"] if abs(start*n-legacy)>.02*fs else [])+
                    (["low_pre_onset_contrast_review"] if contrast is not None and contrast<26 else [])+
                    (["weak_first_80ms_review"] if local<.1*pk else [])}

def onset(y,fs):
    return onset_details(y,fs)["sample"]

def measure(y,fs,midi):
    if fs!=48000 or y.ndim!=2 or y.shape[1]!=2 or not np.isfinite(y).all(): raise ValueError("format")
    det=onset_details(y,fs); start=det['sample']; x=y[start:]; f0=440*2**((midi-69)/12)
    windows={}
    for a,b in [(0,.02),(.02,.08),(.08,.25),(.25,.75),(.8,1.3),(2.5,3),(5,5.5),(9,9.5),(19,19.5),(29,29.5)]:
        z=x[round(a*fs):round(b*fs)]
        if len(z)!=round(b*fs)-round(a*fs): continue
        f,p=periodogram(z,fs=fs,window="hann",axis=0,nfft=next_fast_len(len(z)*4),scaling="density",detrend=False)
        p=p.mean(axis=1); df=f[1]-f[0]; power=float(p.sum()*df)
        bands=[0,80,250,1000,3000,6000,12000,24000.001]
        out={"rms_dbfs":db(np.mean(z*z)),"band_power_pct":[float(p[(f>=lo)&(f<hi)].sum()*df/max(power,1e-30)*100) for lo,hi in zip(bands,bands[1:])]}
        # Below-fundamental attack power is an exploratory proxy, not isolated hammer sound.
        if f0>=500 and b<=.25: out["below_0_7_f0_pct"]=float(p[(f>=80)&(f<.7*f0)].sum()*df/max(power,1e-30)*100)
        if b-a>=.4:
            vals=[]; peaks=[]
            for k in range(1,9):
                lo=k*f0*.965; hi=k*f0*1.08
                if hi>=fs/2:break
                mask=(f>=lo)&(f<=hi)
                vals.append(float(p[mask].sum()*df))
                ii=np.flatnonzero(mask)
                j=ii[np.argmax(p[ii])]
                peaks.append(float(f[j]))
            out["partial_band_relative_db"]=[db(v)-db(vals[0]) for v in vals]
            out["partial_band_power_dbfs"]=[db(v) for v in vals]
            out["peak_bin_hz"]=peaks
        windows[f"{a:g}-{b:g}"]=out
    return {"midi":midi,"nominal_hz":f0,"onset_s":start/fs,"onset_diagnostics":det,"duration_s":len(y)/fs,"peak_dbfs":db(np.max(y*y)),"windows":windows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    m=json.loads(Path(__file__).with_name("c5_reference_manifest.json").read_text())
    result={"source":{k:v for k,v in m.items() if k!="files"},"bands_hz":[0,80,250,1000,3000,6000,12000,24000],"limitations":["edited library, not calibrated force-pressure data","layer numbers not physical hammer speeds","onset v2 is operational threshold; spectral leakage affects attack proxy","partial bands are approximate, not isolated modal powers","no inference of physical damping or sustain audibility from source truncation"],"cases":[]}
    with tempfile.TemporaryDirectory() as tmp:
        for item in m["files"]:
            url=f"https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/{m['commit']}/{item['path']}"
            req=urllib.request.Request(url,headers={"User-Agent":"StageSynth-G2-acoustic-research"})
            with urllib.request.urlopen(req,timeout=60) as r:
                b=r.read(item["bytes"]+1)
            git=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
            if len(b)!=item["bytes"] or git!=item["git_blob_sha1"]:raise ValueError("source identity mismatch")
            p=Path(tmp)/Path(item["path"]).name;p.write_bytes(b)
            y,fs=sf.read(p,always_2d=True,dtype="float64")
            note=int(p.name[1]);layer=int(p.stem.split("v")[1])
            row=measure(y,fs,12*(note+1))
            row.update({"note":f"C{note}","layer":layer,"sha256":hashlib.sha256(b).hexdigest(),"url":url,**item})
            result["cases"].append(row)
            print("G2_C5_CASE",json.dumps({"note":row["note"],"layer":layer,"duration":row["duration_s"],"onset":row["onset_diagnostics"],"windows":{k:v for k,v in row["windows"].items() if k in ["0-0.02","0.02-0.08","0.25-0.75","2.5-3","9-9.5"]}}),flush=True)
            p.unlink()
    assert len(result["cases"])==15
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False))
if __name__=="__main__":main()
