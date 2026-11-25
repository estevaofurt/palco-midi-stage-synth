"""R2 C5 discriminant: trace stored energy and signed power transfer, frozen controls.
Existing audited WAV/pressure, mechanical replay only; no voicing or new audio.
"""
import argparse,copy,json,math
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_damped_events import run_damped,ROOT,KJ,CJ
from g2_r2_mass_pack import SOURCES,GAIN,sha,read
SR=96000
TIMES=(.02,.08,.16,.25,.5,.75,.8,1.3,1.5)
WINDOWS=((0,.01),(.01,.02),(.02,.08),(.08,.25),(.25,.75),(.8,1.3))
def db(x):return float(10*np.log10(max(float(x),1e-30)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--variant',choices=['dry','mass70-energy'],required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert a.key in (60,72)
    a.out.mkdir(parents=True,exist_ok=True)
    m=json.loads((a.source/'manifest.json').read_text())
    assert m['key']==a.key and m['commit']==SOURCES[a.key]['commit'] and m['gate'] and m['gain']==GAIN and m['durationS']==1.5
    row=next(x for x in m['rows'] if x['label']==a.variant)
    wav=a.source/f'{a.key}-{a.variant}.wav';raw=a.source/f'{a.key}-{a.variant}-pressure.npz'
    assert sha(wav)==row['wavSha256'] and sha(raw)==row['rawSha256'] and row['radiation']['gate'];read(wav)
    with np.load(raw,allow_pickle=False) as z:p=z['pressurePa']
    assert p.shape[0]==3 and p.shape[1]>=144000 and np.isfinite(p).all()
    model=json.loads((ROOT/'octave.json').read_text());keys=[x['key'] for x in model['groups']];j=keys.index(a.key);ng=len(keys)
    if a.variant=='mass70-energy':model['groups'][j]['massKg']*=.7
    events=row['events'];assert events==[[0.,a.key,1. if a.variant=='dry' else math.sqrt(1/.7)]]
    h=1/SR;injected=.5*model['groups'][j]['massKg']*events[0][2]**2
    f0=440*2**((a.key-69)/12)
    targets={round(t*SR)-1:t for t in TIMES};snap=[];boardwork=np.zeros(ng);groupwork=np.zeros(ng);damper=np.zeros(ng);contact=0.;jointloss=0.
    lastboard=np.zeros(ng);lastrel=np.zeros(ng)
    def inspect(i,g,b,jf,f,owners,pos,pos1):
        nonlocal lastboard,lastrel,contact,jointloss
        assert all(k==j for k in owners)
        if len(f):contact+=float(f@(pos1[j][1:]-pos[j][1:]))
        current=b.P.T@b.q
        dx=np.array([v[0]-u[0] for u,v in zip(pos,pos1)])
        boardwork[:]+=-jf*(current-lastboard);groupwork[:]+=jf*dx
        rr=np.array([v[0] for v in pos1])-current
        dr=rr-lastrel;jointloss+=CJ*float(dr@dr)/h
        lastboard=current.copy();lastrel=rr.copy()
        for k in range(ng):
            if k!=j:
                d=pos1[k][1:]-pos[k][1:];damper[k]+=float(d@d)/h
        if i not in targets:return
        assert abs(boardwork.sum()-b.energy()-b.loss)<=1e-10
        e=np.array([q.energy() for q in g]);loss=np.array([q.loss for q in g])
        assert np.max(abs(groupwork+(np.arange(ng)==j)*contact-e-loss-damper))<=1e-10
        joint=.5*KJ*float(rr@rr)
        assert abs(boardwork.sum()+groupwork.sum()+joint+jointloss)<=1e-10
        boardenergy=.5*(b.v*b.v+b.w2*b.q*b.q);hz=np.sqrt(b.w2)/(2*np.pi)
        active=g[j];activeenergy=.5*(active.v*active.v+active.w2*active.q*active.q);ahz=np.sqrt(active.w2)/(2*np.pi)
        def bands(en,freq):
            return [float(en[(freq>=.965*k*f0)&(freq<=1.08*k*f0)].sum()) for k in range(1,9)]
        snap.append(dict(t=targets[i],activeJ=float(e[j]),inactiveJ=float(e.sum()-e[j]),boardJ=b.energy(),jointJ=joint,
            activeLossJ=float(loss[j]),inactiveLossJ=float(loss.sum()-loss[j]),damperLossJ=float(damper.sum()),boardLossJ=b.loss,jointLossJ=jointloss,
            contactWorkJ=contact,boardSignedWorkByGroupJ=boardwork.tolist(),groupSignedWorkJ=groupwork.tolist(),groupEnergyJ=e.tolist(),
            boardModalBandJ=bands(boardenergy,hz),activeModalBandJ=bands(activeenergy,ahz)))
    result=run_damped(model,events,SR,1.5,mode='dry',diagnostic=inspect)
    assert len(snap)==len(TIMES) and result['events'][0]['retireSample']<round(TIMES[0]*SR)
    prev=row['mechanical']
    for k in ('injectedJ','reboundRemovedJ','mechanicalJ','boardJ','boardLoss','groupLoss','feltJ','jointLoss','damperLossJ'):
        assert abs(result[k]-prev[k])<=1e-10
    assert abs(result['injectedJ']-injected)<=1e-12
    assert abs(contact-injected+result['reboundRemovedJ']+result['feltJ'])<=1e-10
    assert abs(damper.sum()-result['damperLossJ'])<=1e-10 and abs(jointloss-result['jointLoss'])<=1e-10
    # Pressure bands are measured from the pinned existing signal, not identified modal stems.
    windows=[]
    for lo,hi in WINDOWS:
        x=p[:,round(lo*SR):round(hi*SR)]
        f,P=periodogram(x,SR,axis=1,window='hann',nfft=262144,detrend=False);df=f[1]-f[0]
        partials=[(P[:,(f>=.965*k*f0)&(f<=1.08*k*f0)].sum(axis=1)*df).tolist() for k in range(1,9)]
        windows.append(dict(t=[lo,hi],rmsPaDb=db(np.mean(x*x)),nominalBandPowerPa2=partials))
    at=windows[2]['rmsPaDb']
    for w in windows:w['relativeToAttackDb']=w['rmsPaDb']-at
    report=dict(key=a.key,variant=a.variant,source=SOURCES[a.key],injectedJ=injected,keys=keys,snapshots=snap,pressureWindows=windows,gate=True,
        scope='mechanical replay and existing pressure, no new audio or changed parameters',
        limitations=['nominal modal bands may overlap or miss detuned modes; not isolated partial stems','finite 1.5s held note; no post-release diagnosis','reference microphone and dynamics differ; no calibrated SPL'])
    (a.out/'energy_trace.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    for s in snap:
        print('G2_R2_C5_ENERGY '+json.dumps(dict(key=a.key,variant=a.variant,t=s['t'],**{k:s[k]/injected for k in ('activeJ','inactiveJ','boardJ','jointJ','activeLossJ','inactiveLossJ','damperLossJ','boardLossJ','jointLossJ','contactWorkJ')},boardWorkFraction=sum(s['boardSignedWorkByGroupJ'])/injected),allow_nan=False),flush=True)
    print('G2_R2_C5_GATE '+json.dumps(dict(key=a.key,variant=a.variant,snapshots=len(snap),gate=True)),flush=True)
if __name__=='__main__':main()
