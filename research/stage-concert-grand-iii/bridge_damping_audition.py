"""G3.14d.22: gated short bridge-damping audition, no production tuning.
Reuse same-basis frozen mechanics, CQ and pressure from the long run."""
import argparse,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from frozen_regional_loss import bundle,contract
from physical_acoustic_audition import render
from physical_attack_comparison import checked,compare,bands
from attack_flutter import write_checked

RATE=48000
FACTORS=(.75,.5,.25)

def candidate_damping(G,factor):
    if factor not in FACTORS or G.shape!=(3,80,80) or not np.isfinite(G).all():raise ValueError('damping hypothesis')
    D=G[0]+G[1]+factor*G[2]
    if np.linalg.norm(D-D.T)>1e-10*max(np.linalg.norm(D),1e-30) or np.linalg.eigvalsh((D+D.T)/2).min()<-1e-10*max(np.linalg.norm(D),1e-30):raise ValueError('nonpassive damping')
    return D

def late_ratio(y,ref):
    a=np.array([v['fundamentalRmsPa'] for v in bands(y)])
    b=np.array([v['fundamentalRmsPa'] for v in bands(ref)])
    if a.shape!=(5,2) or b.shape!=a.shape or np.any(b<=0):raise ValueError('window coverage')
    return (a/b).tolist()

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','bundle','loss','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,G,K,doc=bundle(a.bundle,sha,wires)
    d=json.loads((a.loss/'frozen_regional_loss.json').read_text());s=d['summary']
    contract(s,dict(gate=True,cases=2,sameBasisBundle=True,rebuiltCoordinates=False,sourceFrozenSha256=sha))
    speed=doc['summary']['speed']
    if {v['wet'] for v in d['cases']}!={True,False} or any(v['speed']!=speed or v['pressureReplayRelative']>1e-6 for v in d['cases']):raise ValueError('regional replay prerequisite')
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    old={}
    for wet in (False,True):
        row=next(v for v in doc['cases'] if v['wet']==wet)
        old[wet]=checked(a.bundle/'long',row['native'],40)[:5*RATE]
    gain=doc['summary']['commonGain'];a.out.mkdir(parents=True,exist_ok=True);results=[]
    for factor in FACTORS:
        D=candidate_damping(G,factor)
        y,row=render(z['stiffness'],D,z['wirePorts'],wires,rows,z['projection'],z['weights'],K,RATE,speed,True)
        dry=compare(y,old[False]);wet=compare(y,old[True])
        ratios=late_ratio(y,old[False]);wetRatios=late_ratio(y,old[True])
        label='C4_bridge_'+str(round(factor*100))+'pct'
        row.update(bridgeFactor=factor,vsDryNominal=dry,vsWetNominal=wet,
            fundamentalRatioToDry=ratios,fundamentalRatioToWet=wetRatios,
            attackScreeningGate=dry['attackScreeningGate'],
            lateWindowAtLeastDry=bool(min(ratios[-1])>=1.),
            native=write_checked(a.out/(label+'_pressure_5s.wav'),y,RATE,True,gain))
        # Never adjust gain separately or clip candidate audio.
        row['listen']=write_checked(a.out/(label+'_5s.wav'),y,RATE,False,gain) if np.max(abs(y))*gain<.999 else None
        row['fixedGainClippingPrevented']=row['listen'] is None
        results.append(row)
        print('G3_BRIDGE_AUDITION_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('pressureEnvelope','hammerContacts','attackBands')},allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,cases=len(results),speed=speed,seconds=5,rate=RATE,
        sourceFrozenSha256=sha,bridgeFactors=list(FACTORS),otherDampingNominal=True,
        noOutputEQ=True,commonGain=gain,eligibleForLongTest=[v['bridgeFactor'] for v in results if v['attackScreeningGate'] and v['lateWindowAtLeastDry']],
        selectedParameters=None,physicalFeedbackAccepted=False,audibleSustainMeasured=False,above500HzDiagnosticOnly=True)
    (a.out/'bridge_audition.json').write_text(json.dumps(dict(summary=summary,cases=results),indent=2,allow_nan=False))
    print('G3_BRIDGE_AUDITION_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
