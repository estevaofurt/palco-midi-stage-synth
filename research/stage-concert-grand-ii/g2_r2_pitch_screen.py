"""R2.06 preparation: conservative pitch screening of existing R2c notes.
Not the AF-1 product gate; no target retuning or validated uncertainty model.
"""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.signal import periodogram,find_peaks
from g2_r2_mass_pack import KEYS,SOURCES,GAIN,sha,read
from g2_c5_analysis import onset_details
FS=48000
WINDOWS=((.08,.25),(.25,.75),(.8,1.3))
def cents(f,f0):return float(1200*np.log2(f/f0))
def peak_estimate(z,f0,fs=FS):
    z=np.asarray(z);n=len(z);assert n>0 and np.isfinite(z).all()
    f,p=periodogram(z,fs,window='hann',nfft=1<<(8*n-1).bit_length(),detrend=False)
    idx=np.flatnonzero((f>=.95*f0)&(f<=1.05*f0))
    j=int(idx[np.argmax(p[idx])]);band=float(p[idx].sum());total=float(p.sum())
    if band<=1e-30 or total<=1e-30:
        return dict(hz=None,reason='silent or absent fundamental',bandFraction=0.)
    # Fit local log power around peak. Zero padding interpolates, not resolution.
    a,b,c=np.log(np.maximum(p[j-1:j+2],1e-300));den=a-2*b+c
    offset=float(.5*(a-c)/den) if den<0 else 0.
    hz=float(f[j]+np.clip(offset,-.5,.5)*(f[1]-f[0]))
    peaks=find_peaks(p[idx])[0];others=[]
    for k in idx[peaks]:
        if abs(f[k]-hz)>=1/(n/fs) and p[k]>=p[j]*.25:others.append(float(f[k]))
    # This is an operational ambiguity flag, not evidence of isolated string modes.
    reason=None
    if j in (idx[0],idx[-1]):reason='search edge'
    elif band/total<.01:reason='weak fundamental band'
    elif others:reason='competing resolved peaks'
    return dict(hz=hz,cents=cents(hz,f0),bandFraction=band/total,physicalResolutionHz=fs/n,competingPeaksHz=others,reason=reason)
def analyze(y,key):
    f0=440*2**((key-69)/12);start=onset_details(y,FS)['sample'];rows=[]
    for lo,hi in WINDOWS:
        z=y[start+round(lo*FS):start+round(hi*FS)]
        assert len(z)==round(hi*FS)-round(lo*FS)
        # Two independent channel estimates, plus two shorter halves for sensitivity.
        signals=[z[:,0],z[:,1],z[:len(z)//2,0],z[len(z)//2:,0],z[:len(z)//2,1],z[len(z)//2:,1]]
        p=[peak_estimate(x,f0) for x in signals]
        estimates=[v['cents'] for v in p if v['hz'] is not None]
        if len(estimates)!=6:
            row=dict(window=[lo,hi],estimates=p,status='indeterminate',reason='absent peak')
        else:
            center=float(np.mean(estimates[:2]))
            # Conservative resolution allowance, not calibrated statistical uncertainty.
            halfbin=max(abs(cents(f0+FS/(2*len(z)),f0)),abs(cents(f0-FS/(2*len(z)),f0)))
            allowance=max(abs(v-center) for v in estimates)+halfbin
            good=not any(v['reason'] for v in p) and abs(center)+allowance<=5
            row=dict(window=[lo,hi],estimates=p,centerCents=center,channelAndSubwindowSpreadCents=float(max(estimates)-min(estimates)),
                resolutionAllowanceCents=halfbin,diagnosticAllowanceCents=allowance,status='within_screen' if good else 'review',
                reason='not a calibrated uncertainty or AF-1 pass')
        rows.append(row)
    return dict(key=key,targetHz=f0,windows=rows,scope='nominal A440 equal temperament development target; not final stretch curve')
def selftest():
    t=np.arange(FS*2)/FS;f0=440.
    for offset in (0,8,-8):
        z=np.sin(2*np.pi*f0*2**(offset/1200)*t)
        a=peak_estimate(z,f0);assert abs(a['cents']-offset)<.1 and a['reason'] is None
    a=peak_estimate(np.zeros_like(t),f0);assert a['hz'] is None
    a=peak_estimate(np.sin(2*np.pi*440*t)+np.sin(2*np.pi*445*t),f0);assert a['reason']=='competing resolved peaks'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    selftest();a.out.mkdir(parents=True,exist_ok=True);rows=[]
    for k,note in KEYS.items():
        d=a.root/f'G2-R2C-note-{k}';m=json.loads((d/'manifest.json').read_text())
        assert m['commit']==SOURCES[k]['commit'] and m['key']==k and m['gain']==GAIN and m['gate'] and len(m['rows'])==2
        for item in m['rows']:
            label=item['label'];wav=d/f'{k}-{label}.wav';assert sha(wav)==item['wavSha256'] and item['radiation']['gate']
            row=dict(note=note,label=label,source=SOURCES[k],wavSha256=sha(wav),**analyze(read(wav),k))
            rows.append(row)
            print('G2_R2_PITCH_SCREEN '+json.dumps(dict(note=note,label=label,windows=[{k:v for k,v in w.items() if k!='estimates'} for w in row['windows']]),allow_nan=False),flush=True)
    assert len(rows)==8
    report=dict(rows=rows,gate=True,scope='diagnostic execution only; no tuning approval',limitations=['1.5s clips only, one nominal intensity','resolution allowance is not validated uncertainty','fundamental peak may be coupled or beating, not individual unison string','no final stretch target, no MIDI matrix, no F12.5 pass'])
    (a.out/'pitch_screen.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R2_PITCH_GATE '+json.dumps(dict(clips=8,windows=24,softwareChecks=5,gate=True,af1=False)),flush=True)
if __name__=='__main__':main()
