"""G2.11a: bounded mechanical gates, no audio or voicing."""
import json
from pathlib import Path
import numpy as np
from g2_shared_hammer import run
from g2_octave_events import run_events,data,ROOT
def main():
    model=json.loads((ROOT/'octave.json').read_text())
    assert model['playable']==list(range(60,73))
    assert len(model['groups'])==15
    for group in data['groups']:
        same=next(g for g in model['groups'] if g['key']==group['key'])
        assert all(same[k]==group[k] for k in ('M','C','K','ports','n','N'))
    checks=[]
    for j,key in enumerate((48,60,84)):
        cap={};r=run([j],1.,96000,6000,capture=cap,duration_s=.04)
        frames=[];q=run_events(data,[(0.,key,1.)],96000,.04,sink=lambda a:frames.append(a.copy()))
        acc=np.stack(frames,axis=1);err=float(np.linalg.norm(acc-cap['acc'])/np.linalg.norm(cap['acc']))
        assert err<=1e-9
        checks.append(dict(kind='anchor-parity',key=key,pressureSourceRelativeError=err,pass_=True))
    rows=[]
    for key in range(60,73):
        q=run_events(model,[(0.,key,1.)],96000,.04)
        assert q['groupJ'][q['keys'].index(key)]>0
        rows.append(q);print('G2_11_KEY '+json.dumps(dict(key=key,event=q['events'][0],balance=q['maxBalance'],boardJ=q['boardJ']),allow_nan=False),flush=True)
    for name,events,dur in [('triad',[(0.,60,1.),(0.,64,1.),(0.,67,1.)],.04),('sequence-restrike',[(0.,60,1.),(.04,64,1.),(.08,60,.5),(.12,67,1.)],.16)]:
        q=run_events(model,events,96000,dur,retain_trace=True);z=run_events(model,events,192000,dur,retain_trace=True)
        errors={k:abs(q[k]-z[k])/max(abs(z[k]),1e-20) for k in ('mechanicalJ','boardJ','boardLoss','feltJ','jointLoss','groupLoss')}
        for i,(a,b) in enumerate(zip(q['events'],z['events'])):
            errors[f'peak{i}']=abs(a['peakN']-b['peakN'])/b['peakN']
            errors[f'impulse{i}']=abs(a['impulseNs']-b['impulseNs'])/b['impulseNs']
            assert abs(a['durationMs']-b['durationMs'])<=.1
        x,y=np.array(q['trace']),np.array(z['trace'])
        errors['trajectory']=float(np.linalg.norm(x-y)/np.linalg.norm(y))
        assert max(errors.values())<=.1
        if name=='sequence-restrike':
            assert q['events'][2]['key']==60 and q['events'][2]['residualMechanicalJ']>0
        checks.append(dict(kind=name,errors=errors,pass_=True))
        print('G2_11_EVENTS '+json.dumps(dict(name=name,events=q['events'],errors=errors,balance=q['maxBalance']),allow_nan=False),flush=True)
    report=dict(scope='mechanical octave pilot; no audio, dampers or tuning gate',keys=rows,checks=checks,required=18,passed=len(rows)+len(checks),gate=len(rows)+len(checks)==18)
    (ROOT/'octave_report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_11_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if __name__=='__main__':main()
