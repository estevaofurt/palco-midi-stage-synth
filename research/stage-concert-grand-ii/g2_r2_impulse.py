"""R2a: measure actual hammer impulse, signed work, modal energy, and pressure, frozen dry."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_damped_events import run_damped,ROOT
from g2_acoustic_integrated import make_kernels,render,freqs,SR,C
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(p):return float(10*np.log10(max(float(p),1e-30)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--speed',type=float,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);a=ap.parse_args()
    assert a.key in (60,64,67,72) and a.speed in (.5,1.,2.)
    a.out.mkdir(parents=True,exist_ok=True)
    model=json.loads((ROOT/'octave.json').read_text());keys=[x['key'] for x in model['groups']];j=keys.index(a.key)
    dur=.16;n=round(dur*SR);h=1/SR;count=int(np.sum(freqs<6000));acc=np.empty((count,n));force=np.zeros(n);i=0
    last_board=np.zeros(len(keys));board_work=np.zeros(len(keys));contact_work=0.;snapshots=[]
    f0=440*2**((a.key-69)/12);harm=np.arange(1,9)*f0
    sample_targets={round(t*SR)-1:t for t in (.004,.008,.020,.080,.160)}
    def capture(x):
        nonlocal i
        acc[:,i]=x;i+=1
    def inspect(i,g,b,jf,f,owners,pos,pos1):
        nonlocal contact_work,last_board
        assert all(k==j for k in owners)
        force[i]=float(np.sum(f))
        if len(f):contact_work+=float(f@(pos1[j][1:]-pos[j][1:]))
        current=b.P.T@b.q
        board_work[:]+=-jf*(current-last_board);last_board=current.copy()
        if i in sample_targets:
            z=g[j];e=.5*(z.v*z.v+z.w2*z.q*z.q);hz=np.sqrt(z.w2)/(2*np.pi)
            bands=[float(e[abs(hz-t)<=.03*t].sum()) for t in harm]
            snapshots.append(dict(timeS=sample_targets[i],groupJ=float(e.sum()),groupHarmonicBandJ=bands,groupOtherJ=float(e.sum()-sum(bands)),
                                  otherGroupsJ=sum(v.energy() for k,v in enumerate(g) if k!=j),boardJ=b.energy(),boardWorkJ=float(board_work.sum()),contactWorkJ=contact_work))
    result=run_damped(model,[(0.,a.key,a.speed)],SR,dur,sink=capture,mode='dry',diagnostic=inspect)
    assert i==n and len(snapshots)==5 and np.isfinite(acc).all()
    delivered=result['injectedJ']-result['reboundRemovedJ']-result['feltJ']
    assert abs(contact_work-delivered)<=1e-10 and abs(board_work.sum()-result['boardJ']-result['boardLoss'])<=1e-10
    impulse=force.sum()*h;assert impulse>0 and abs(impulse-result['events'][0]['impulseNs'])<=1e-10
    t=np.arange(n)*h;F=np.abs(np.exp(-2j*np.pi*harm[:,None]*t)@force)*h
    ks=[k[:count] for k in make_kernels(128,96)];p=render(acc,ks)
    assert np.isfinite(p).all() and np.max(abs(p))>0 and np.all(p[:,:int(np.floor(SR/C+.5))]==0)
    parity=None
    if a.key==60 and a.speed==1.:
        d=a.baseline;m=json.loads((d/'manifest.json').read_text());raw=d/'pressure.npz'
        assert m['commit']=='95c2419c6a52289982e142669ee8ea610a8c7d89' and m['case']=='C4-held' and m['mode']=='dry' and m['radiation']['gate'] and sha(raw)==m['rawSha256']
        with np.load(raw,allow_pickle=False) as q:old=q['pressurePa'][:,:n]
        parity=float(np.linalg.norm(p[:,:n]-old)/np.linalg.norm(old));assert parity<=1e-9
    windows=[]
    for lo,hi in ((0,.01),(.01,.02),(.02,.08),(.08,.16)):
        z=p[:,round(lo*SR):round(hi*SR)];f,P=periodogram(z,SR,axis=1,nfft=131072,window='hann',detrend=False)
        bands=[]
        for x in harm:
            ix=(f>=.97*x)&(f<=1.03*x);bands.append([float(v) for v in P[:,ix].sum(axis=1)*(f[1]-f[0])])
        windows.append(dict(startS=lo,endS=hi,rmsPa=np.sqrt(np.mean(z*z,axis=1)).tolist(),nominalBandPowerPa2=bands,frequencyResolutionHz=1/(hi-lo)))
    result.pop('trace')
    row=dict(key=a.key,speedMps=a.speed,mechanical=result,contactWorkJ=contact_work,contactDeliveredCheckJ=contact_work-delivered,boardSignedWorkJ=board_work.tolist(),forceHarmonicAmplitudeRelativeToImpulseDb=[db((z/impulse)**2) for z in F],snapshots=snapshots,windows=windows,baselinePrefixError=parity,gate=True,scope='diagnostic only; no changed parameter; nominal bands not isolated partials')
    (a.out/'impulse.json').write_text(json.dumps(row,indent=2,allow_nan=False))
    print('G2_R2_IMPULSE '+json.dumps(row,allow_nan=False),flush=True)
if __name__=='__main__':main()
