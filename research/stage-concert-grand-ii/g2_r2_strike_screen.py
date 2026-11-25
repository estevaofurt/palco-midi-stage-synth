"""R2.04: one isolated strike-position hypothesis on four held Dry notes.
The active group is undamped throughout this experiment. No release or altered damper.
"""
import argparse,copy,json
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_damped_events import run_damped,ROOT
from g2_acoustic_integrated import make_kernels,render,freqs,SR,C
BASE=.13;ALT=.11;WIDTH=.005
def db(p):return float(10*np.log10(max(float(p),1e-30)))
def weights(n,L,x):return np.sin(np.pi*n*x)*np.sinc(n*WIDTH/(2*L))
def change_port(model,key,x):
    out=copy.deepcopy(model);g=next(v for v in out['groups'] if v['key']==key)
    L=.65 if key==60 else g['geometry']['lengthM'];N=g['N'];nc=len(g['ports'])//2
    assert nc==3 and g['n']==2*N
    used=[]
    for c in range(nc):
        p=np.array(g['ports'][c]);assert p[0]==BASE and not np.any(p[N:])
        ix=np.flatnonzero(p[1:N])+1;n=np.arange(1,len(ix)+1)
        assert len(ix)>=8 and np.all(np.diff(ix)==1)
        assert np.max(abs(p[ix]-weights(n,L,BASE)))<=1e-12
        used.extend(ix.tolist());p[0]=x;p[ix]=weights(n,L,x);g['ports'][c]=p.tolist()
    assert sorted(used)==list(range(1,N))
    return out,L
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--screen',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert a.key in (60,64,67,72)
    a.out.mkdir(parents=True,exist_ok=True);base=json.loads((ROOT/'octave.json').read_text())
    old=json.loads((a.screen/'mass_screen.json').read_text());assert old['gate'] and old['key']==a.key
    control=old['rows'][0]['mechanical'];assert old['rows'][0]['label']=='control'
    f0=440*2**((a.key-69)/12);harm=f0*np.arange(1,9)
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)];n=round(.16*SR)
    rows=[]
    for label,x in [('control',BASE),('strike-11pct',ALT)]:
        m,L=change_port(base,a.key,x)
        if x==BASE:m=base # exact control; reconstruction validated above
        acc=np.empty((count,n));force=np.zeros(n);i=0
        def capture(v):
            nonlocal i
            acc[:,i]=v;i+=1
        def inspect(i,g,b,jf,f,owners,pos,pos1):force[i]=float(np.sum(f))
        report=run_damped(m,[(0.,a.key,1.)],SR,.16,sink=capture,mode='dry',diagnostic=inspect)
        assert i==n and np.isfinite(acc).all()
        j=report['keys'].index(a.key);assert report['damperGroupLossJ'][j]==0
        if x==BASE:
            for k in ('injectedJ','mechanicalJ','boardJ','boardLoss','groupLoss','feltJ','jointLoss','damperLossJ','reboundRemovedJ'):
                assert abs(report[k]-control[k])<=1e-10
        impulse=force.sum()/SR;assert abs(impulse-report['events'][0]['impulseNs'])<=1e-10
        F=np.abs(np.exp(-2j*np.pi*harm[:,None]*np.arange(n)/SR)@force)/SR
        p=render(acc,ks);assert np.isfinite(p).all() and np.all(p[:,:int(np.floor(SR/C+.5))]==0)
        windows={}
        for lo,hi in ((0,.01),(.01,.02),(.02,.08),(.08,.16)):
            z=p[:,round(lo*SR):round(hi*SR)];f,P=periodogram(z,SR,axis=1,nfft=131072,window='hann',detrend=False);P=P.mean(axis=0)
            v=[db(P[(f>=.965*k)&(f<=1.08*k)].sum()*(f[1]-f[0])) for k in harm]
            windows[f'{lo:g}-{hi:g}']=dict(rmsDb=db(np.mean(z*z)),bandsDb=v)
        report.pop('trace')
        rows.append(dict(label=label,strikeFraction=x,geometryProjection=weights(np.arange(1,9),L,x).tolist(),forceRelativeToImpulseDb=[db((v/impulse)**2) for v in F],windows=windows,mechanical=report))
    g,c=rows;assert abs(g['mechanical']['injectedJ']-c['mechanical']['injectedJ'])<=1e-12
    d={w:c['windows'][w]['rmsDb']-g['windows'][w]['rmsDb'] for w in g['windows']}
    at=np.array(c['windows']['0.02-0.08']['bandsDb'])-g['windows']['0.02-0.08']['bandsDb']
    contrast=d['0-0.01']-d['0.02-0.08']
    screen=bool(min(d['0.02-0.08'],d['0.08-0.16'],at[0],contrast)>=-1 and np.count_nonzero(at[4:8]>=2)>=2)
    result=dict(key=a.key,rows=rows,attackBandAbsoluteDeltaDb=at.tolist(),rmsDeltaDb=d,earlyContrastDeltaDb=contrast,screen=screen,gate=True,scope='held Dry only; frozen mass/energy, one position hypothesis; no candidate adoption or WAV')
    (a.out/'strike_screen.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print('G2_R2_STRIKE_SCREEN '+json.dumps({k:v for k,v in result.items() if k!='rows'},allow_nan=False),flush=True)
if __name__=='__main__':main()
