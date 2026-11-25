"""R2b: bounded hammer effective-mass discrimination, frozen dry body."""
import argparse,copy,json,math
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_damped_events import run_damped,ROOT
from g2_acoustic_integrated import make_kernels,render,freqs,SR,C
def db(p):return float(10*np.log10(max(float(p),1e-30)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert a.key in (60,64,67,72)
    a.out.mkdir(parents=True,exist_ok=True)
    base=json.loads((ROOT/'octave.json').read_text());j=next(i for i,x in enumerate(base['groups']) if x['key']==a.key)
    mass=base['groups'][j]['massKg'];f0=440*2**((a.key-69)/12);harm=f0*np.arange(1,9)
    n=round(.16*SR);count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    rows=[]
    for label,scale,speed in [('control',1.,1.),('mass-70-same-speed',.7,1.),('mass-70-same-energy',.7,math.sqrt(1/.7))]:
        model=copy.deepcopy(base);model['groups'][j]['massKg']=mass*scale
        acc=np.empty((count,n));force=np.zeros(n);i=0
        def capture(x):
            nonlocal i
            acc[:,i]=x;i+=1
        def inspect(i,g,b,jf,f,owners,pos,pos1):
            force[i]=float(np.sum(f))
        m=run_damped(model,[(0.,a.key,speed)],SR,.16,sink=capture,mode='dry',diagnostic=inspect)
        assert i==n and np.isfinite(acc).all() and abs(m['injectedJ']-.5*mass*scale*speed**2)<=1e-12
        t=np.arange(n)/SR;impulse=force.sum()/SR;F=abs(np.exp(-2j*np.pi*harm[:,None]*t)@force)/SR
        assert impulse>0 and abs(impulse-m['events'][0]['impulseNs'])<=1e-10
        p=render(acc,ks);assert np.isfinite(p).all() and np.all(p[:,:int(np.floor(SR/C+.5))]==0)
        windows={}
        for lo,hi in ((0,.02),(.02,.08),(.08,.16)):
            x=p[:,round(lo*SR):round(hi*SR)];f,P=periodogram(x,SR,axis=1,nfft=131072,window='hann',detrend=False);P=P.mean(axis=0);df=f[1]-f[0]
            bands=[float(P[(f>=.97*z)&(f<=1.03*z)].sum()*df) for z in harm]
            windows[f'{lo:g}-{hi:g}']=dict(rmsPowerPa2=float(np.mean(x*x)),fundamentalPa2=bands[0],harmonicBandsPa2=bands,H2toH1Db=db(bands[1])-db(bands[0]))
        delivered=m['injectedJ']-m['reboundRemovedJ']-m['feltJ'];assert delivered>0
        m.pop('trace')
        row=dict(label=label,massKg=mass*scale,speedMps=speed,mechanical=m,deliveredFraction=delivered/m['injectedJ'],forceRelativeToH1Db=[db(z*z)-db(F[0]*F[0]) for z in F],windows=windows)
        rows.append(row)
    c=rows[0];checks=[]
    for row in rows[1:]:
        at=row['windows']['0.02-0.08'];ct=c['windows']['0.02-0.08'];body=row['windows']['0.08-0.16'];cb=c['windows']['0.08-0.16']
        early=row['windows']['0-0.02'];ce=c['windows']['0-0.02']
        delta=dict(label=row['label'],attackDb=db(at['rmsPowerPa2'])-db(ct['rmsPowerPa2']),fundamentalDb=db(at['fundamentalPa2'])-db(ct['fundamentalPa2']),bodyDb=db(body['rmsPowerPa2'])-db(cb['rmsPowerPa2']),H2toH1DeltaDb=at['H2toH1Db']-ct['H2toH1Db'],forceH2toH1DeltaDb=row['forceRelativeToH1Db'][1]-c['forceRelativeToH1Db'][1],earlyContrastDeltaDb=(db(early['rmsPowerPa2'])-db(at['rmsPowerPa2']))-(db(ce['rmsPowerPa2'])-db(ct['rmsPowerPa2'])))
        delta['screen']=bool(delta['H2toH1DeltaDb']>=2 and delta['forceH2toH1DeltaDb']>=1 and min(delta['attackDb'],delta['fundamentalDb'],delta['bodyDb'])>=-1)
        checks.append(delta);print('G2_R2_MASS_SCREEN '+json.dumps(dict(key=a.key,**delta),allow_nan=False),flush=True)
    assert abs(rows[2]['mechanical']['injectedJ']-c['mechanical']['injectedJ'])<=1e-12
    report=dict(key=a.key,rows=rows,checks=checks,gate=True,scope='screen only; no calibrated wood, no WAV, no candidate selection; finite nominal spectral bands')
    (a.out/'mass_screen.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R2_MASS_GATE '+json.dumps(dict(key=a.key,cases=3,gate=True)),flush=True)
if __name__=='__main__':main()
