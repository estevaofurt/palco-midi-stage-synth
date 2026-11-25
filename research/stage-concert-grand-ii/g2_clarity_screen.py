"""G2.11e: bounded one-factor physical clarity diagnostic; no voicing selection."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_octave_events import run_events,ROOT
from g2_acoustic_integrated import make_kernels,render,freqs,SR
from g2_treble_candidate_audio import energy
from g2_pressure_stream import PressureStream
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(p):return float(10*np.log10(max(float(p),1e-30)))
def stats(p,keys):
    out={}
    for lo,hi in ((0,.02),(.02,.08),(.08,.25),(.25,.5),(.5,.75)):
        z=p[:,round(lo*SR):round(hi*SR)]
        f,P=periodogram(z,SR,axis=1,window='hann',nfft=131072,detrend=False);P=P.mean(axis=0);df=f[1]-f[0]
        total=float(P.sum()*df)
        def band(a,b):return float(P[(f>=a)&(f<b)].sum()*df)
        out[f'{lo:g}-{hi:g}']=dict(rmsDbPa=db(np.mean(z*z)),spectralTotalPa2=total,highPct=100*band(1000,6000)/max(total,1e-30),
            fundamentalDbPa2={str(k):db(band(.97*(440*2**((k-69)/12)),1.03*(440*2**((k-69)/12)))) for k in keys})
    out['lateRelativeDb']=out['0.5-0.75']['rmsDbPa']-out['0.02-0.08']['rmsDbPa']
    out['earlyRelativeDb']=out['0-0.02']['rmsDbPa']-out['0.02-0.08']['rmsDbPa']
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    model=json.loads((ROOT/'octave.json').read_text())
    keys=[60,64,67] if a.case=='triad' else [int(a.case)]
    events=[(0.,k,1.) for k in keys];dur=.8
    d=a.baseline/('G2-11-audit-'+a.case);m=json.loads((d/'manifest.json').read_text());raw=d/(a.case+'-pressure.npz')
    assert m['commit']=='dbd007fdeab3def76c3ff8cb3cae47741655429b' and m['audit']['gate'] and sha(raw)==m['rawSha256']
    with np.load(raw,allow_pickle=False) as z:baseline=z['pressurePa']
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    rows=[]
    for name,loss,felt in [('control',1.,1.),('board-loss-x2',2.,1.),('felt-x1.5',1.,1.5)]:
        stream=PressureStream(ks,2048);buf=np.empty((count,2048));n=0;parts=[]
        short=np.empty((count,round(.16*SR)));i=0
        def flush():
            nonlocal n
            if n:parts.append(stream.process(buf[:,:n]));n=0
        def sink(x):
            nonlocal n,i
            if i<short.shape[1]:short[:,i]=x
            i+=1;buf[:,n]=x;n+=1
            if n==2048:flush()
        q=run_events(model,events,SR,dur,sink=sink,boardLossScale=loss,feltScale=felt);flush()
        p=np.concatenate([*parts,stream.finish()],axis=1)
        assert i==round(dur*SR) and np.isfinite(p).all()
        if name=='control':
            err=float(np.linalg.norm(p[:,:i]-baseline[:,:i])/np.linalg.norm(baseline[:,:i]))
            assert err<=1e-9
        else:err=None
        # Separate finite-window mechanical budget, identical event schedule and settings.
        audit=run_events(model,events,SR,.16,boardLossScale=loss,feltScale=felt)
        e1=energy(short,8,16);e2=energy(short,16,32)
        ae=abs(e1-e2)/max(e2,1e-30)
        if ae>.10:
            e3=energy(short,32,64);ae=abs(e2-e3)/max(e3,1e-30);e2=e3
        work=audit['boardJ']+audit['boardLoss']
        rad=dict(angularError=ae,radiatedJ=e2,boardWorkJ=work,gate=bool(ae<=.10 and e2<=min(work,audit['injectedJ'])))
        st=stats(p,keys);q.pop('trace')
        row=dict(case=a.case,variant=name,boardLossScale=loss,feltScale=felt,controlParityError=err,radiation=rad,mechanical=q,stats=st)
        rows.append(row)
        print('G2_11E_CASE '+json.dumps({k:v for k,v in row.items() if k!='mechanical'},allow_nan=False),flush=True)
    base=rows[0]['stats'];checks=[]
    for row in rows[1:]:
        s=row['stats'];a0=base['0.02-0.08'];a1=s['0.02-0.08']
        attack=a1['rmsDbPa']-a0['rmsDbPa']
        fdelta={k:a1['fundamentalDbPa2'][k]-a0['fundamentalDbPa2'][k] for k in a0['fundamentalDbPa2']}
        late=s['lateRelativeDb']-base['lateRelativeDb'];early=s['earlyRelativeDb']-base['earlyRelativeDb']
        # Directional diagnostic, no absolute piano target or perceptual gate.
        check=dict(variant=row['variant'],attackDeltaDb=attack,fundamentalDeltaDb=fdelta,relativeLateDeltaDb=late,
            relativeEarlyDeltaDb=early,highPctDelta=a1['highPct']-a0['highPct'],radiationPass=row['radiation']['gate'],
            tailScreen=bool(row['radiation']['gate'] and late<=-3 and attack>=-1 and min(fdelta.values())>=-1),
            attackScreen=bool(row['radiation']['gate'] and early>=2 and attack>=-1 and min(fdelta.values())>=-1 and late<=1))
        checks.append(check);print('G2_11E_SCREEN '+json.dumps(check,allow_nan=False),flush=True)
    (a.out/'report.json').write_text(json.dumps(dict(scope='sensitivity, not voicing',rows=rows,checks=checks,gate=len(rows)==3),indent=2,allow_nan=False))
if __name__=='__main__':main()
