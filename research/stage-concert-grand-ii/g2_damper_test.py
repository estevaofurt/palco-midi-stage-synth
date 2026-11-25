"""R1 proof: bypass, held, release, inactive strings, restrike and triad."""
import json
import numpy as np
from g2_octave_events import run_events,ROOT
from g2_damped_events import run_damped
def capture(fn,model,events,sr,duration,**kwargs):
    p=[]
    r=fn(model,events,sr,duration,sink=lambda x:p.append(x.copy()),retain_trace=True,**kwargs)
    return r,np.stack(p,axis=1)
def diff(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def convergence(a,b):
    e={k:abs(a[k]-b[k])/max(abs(b[k]),1e-20) for k in ('mechanicalJ','boardJ','boardLoss','groupLoss','feltJ','jointLoss','damperLossJ')}
    e['trajectory']=diff(np.array(a['trace']),np.array(b['trace']))
    for i,(x,y) in enumerate(zip(a['events'],b['events'])):
        e[f'peak{i}']=abs(x['peakN']-y['peakN'])/y['peakN'];e[f'impulse{i}']=abs(x['impulseNs']-y['impulseNs'])/y['impulseNs']
        assert abs(x['durationMs']-y['durationMs'])<=.1
    assert max(e.values())<=.10
    return e
def main():
    m=json.loads((ROOT/'octave.json').read_text());sr=96000;rows=[]
    ev=[(0.,60,1.)];dur=.25
    baseline,b=capture(run_events,m,ev,sr,dur)
    bypass,p=capture(run_damped,m,ev,sr,dur,mode='bypass')
    held,h=capture(run_damped,m,ev,sr,dur,mode='release-only')
    assert diff(p,b)<=1e-9 and diff(h,b)<=1e-9 and held['damperLossJ']==0
    rows.append(dict(name='bypass-held-parity',bypassError=diff(p,b),heldError=diff(h,b),pass_=True))
    rel,z=capture(run_damped,m,ev,sr,dur,mode='release-only',releases=[(.06,60)])
    assert diff(z[:,:round(.06*sr)],h[:,:round(.06*sr)])<=1e-9
    j=rel['keys'].index(60)
    assert rel['damperGroupLossJ'][j]>0 and sum(rel['damperGroupLossJ'][i] for i in range(len(rel['keys'])) if i!=j)==0
    assert rel['mechanicalJ']<held['mechanicalJ'] and rel['groupJ'][j]<held['groupJ'][j]
    rows.append(dict(name='release-only',preReleaseError=diff(z[:,:round(.06*sr)],h[:,:round(.06*sr)]),lossJ=rel['damperLossJ'],energyRatio=rel['mechanicalJ']/held['mechanicalJ'],groupRatio=rel['groupJ'][j]/held['groupJ'][j],pass_=True))
    dryHeld,q=capture(run_damped,m,ev,sr,dur,mode='dry')
    assert dryHeld['damperGroupLossJ'][j]==0 and dryHeld['damperLossJ']>0
    rows.append(dict(name='inactive-strings',lossJ=dryHeld['damperLossJ'],heldGroupDamperLossJ=dryHeld['damperGroupLossJ'][j],pressureDifference=diff(q,h),pass_=True))
    cases=[('dry-release',ev,[(.06,60)],.25),('restrike',[(0.,60,1.),(.12,60,.5)],[(.06,60),(.18,60)],.25),('triad',[(0.,60,1.),(0.,64,1.),(0.,67,1.)],[(.06,60),(.06,64),(.06,67)],.16)]
    for name,events,offs,d in cases:
        a=run_damped(m,events,sr,d,releases=offs,retain_trace=True)
        b=run_damped(m,events,192000,d,releases=offs,retain_trace=True)
        errs=convergence(a,b);assert a['damperLossJ']>0
        if name=='restrike':assert a['events'][1]['residualMechanicalJ']>0
        rows.append(dict(name=name,lossJ=a['damperLossJ'],maxBalance=a['maxBalance'],maxDamperResidual=a['maxDamperResidual'],errors=errs,events=a['events'],pass_=True))
    for row in rows:print('G2_R1_CASE '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(required=6,passed=len(rows),gate=len(rows)==6,rows=rows,scope='experimental dampers, no voicing or acoustic approval')
    (ROOT/'r1_report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R1_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if __name__=='__main__':main()
