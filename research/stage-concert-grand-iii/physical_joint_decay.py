"""G3.12x: joint unison/structural damping sensitivity, including attack.
Dry mechanical diagnostic, no physical fit or selected parameters."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from physical_long_decay import startup
from physical_loss_sensitivity import partition,prepare,simulate
from physical_unison_decay import detune,observations,metrics
from felt_law import params

SPREADS=(0.,.5,1.,2.)
FACTORS=(1.,.5,.25,.1)
def configurations():
    return [(s,f) for s in SPREADS for f in FACTORS]

def source(root,name,sha,expected):
    raw=(root/name).read_bytes();d=json.loads(raw)
    if d['sourceFrozenSha256']!=sha or any(d['summary'].get(k)!=v for k,v in expected.items()):
        raise ValueError('unapproved source '+name)
    return d,hashlib.sha256(raw).hexdigest()

def reference(rms,count):
    return [float(rms[:,0].max()),float(rms[:,1].max()),
        float(np.sqrt(np.mean(rms[:,2:2+count]**2,axis=1)).max()),float(rms[:,0].max())]

def attack_metrics(init,rms,ref):
    return dict(mechanicalTransferFraction=init['mechanicalEnergyJ']/init['injectedJ'],
        first50msPlateRmsMps=float(rms[0,1]),
        first50msPlateRelative=float(rms[0,1]/ref),
        # This window starts at 30ms; it is early decay, not the onset waveform.
        firstWindowStartS=.030,firstWindowEndS=.080)

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','unison','regions','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    u,uh=source(a.unison,'physical_unison_decay.json',sha,dict(gate=True,cases=20,acousticLoadIncluded=False,calibratedParameters=False))
    v,vh=source(a.regions,'structural_region_decay.json',sha,dict(gate=True,cases=28,acousticLoadIncluded=False,calibratedParameters=False))
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'));rows['_platePort']=z['ports'][:,6]
    cases=[];refs={};early={};rate=48000;n=32
    # Full factorial at 48 kHz; independent predetermined check at 96 kHz.
    for rate,n,configs,role in [(48000,32,configurations(),'development'),
        (96000,32,[(0.,1.),(.5,.25),(1.,.5),(1.,.1),(2.,.25)],'rateCheck')]:
        for spread,factor in configs:
            ww,records=detune(wires,rows,spread)
            states=[startup(k,D*factor,A,ww,rows,groups,masses,felts,rate,n,1.,speed) for speed in (.3,3.)]
            m,q,vv,O,_=states[0];O,count=observations(m,O,groups);G,audit=partition(m)
            prepared=prepare(m.M,m.K,G,O,1/rate,round(.05*rate));pending=[]
            for speed,(other,q,vv,o,init) in zip((.3,3.),states):
                o,c=observations(other,o,groups)
                if c!=count or not np.array_equal(other.D,m.D) or not np.array_equal(o,O):raise ValueError('inconsistent attack model')
                result,rms=simulate(prepared,q,vv,seconds=40.)
                pending.append((speed,result,rms,init))
            if (spread,factor)==(0.,1.):
                # Fixed strong nominal reference across both rates.
                if not refs:refs=reference(pending[-1][2],count)
                for speed,result,rms,init in pending:early[(rate,speed)]=float(rms[0,1])
            for speed,result,rms,init in pending:
                x=metrics(rms,count,refs);am=attack_metrics(init,rms,early[(rate,speed)])
                row=dict(role=role,rate=rate,partials=n,pedal=1.,spreadCents=spread,structureFactor=factor,
                    hammerSpeedMps=speed,partition=audit,commonReferenceRmsMps=refs,**init,**result,**x,**am)
                if factor==1. and rate==48000:
                    prior=next(t for t in u['cases'] if t['partials']==n and t['spreadCents']==spread and t['hammerSpeedMps']==speed)
                    replay=abs(result['initialEnergyJ']/prior['initialEnergyJ']-1.)
                    for name in ('meanWire','plate','individualRms'):
                        replay=max(replay,abs(x['observations'][name]['peakRmsMps']/prior['observations'][name]['peakRmsMps']-1.))
                    if replay>1e-7:raise ValueError('unison replay')
                    row['nominalReplayRelative']=replay
                cases.append(row)
                print('G3_JOINT_DECAY_CASE '+json.dumps({key:val for key,val in row.items() if key not in ('rmsMps','snapshots')},allow_nan=False),flush=True)
    checks=[]
    for b in [t for t in cases if t['role']=='rateCheck']:
        c=next(t for t in cases if t['role']=='development' and all(t[key]==b[key] for key in ('spreadCents','structureFactor','hammerSpeedMps')))
        def threshold(t):return t['observations']['plate']['commonThresholds']['-60']
        checks.append(dict(spreadCents=b['spreadCents'],structureFactor=b['structureFactor'],hammerSpeedMps=b['hammerSpeedMps'],
            plate48k=threshold(c),plate96k=threshold(b),peakRelative=abs(b['observations']['plate']['peakRmsMps']/c['observations']['plate']['peakRmsMps']-1.),
            earlyWindowRelative=abs(b['first50msPlateRmsMps']/c['first50msPlateRmsMps']-1.)))
    summary=dict(gate=all(t['gate'] for t in cases),cases=len(cases),developmentCases=32,rateCheckCases=10,
        diagnosticOnly=True,calibratedParameters=False,selectedParameters=None,fullAttackRecomputed=True,
        commonReferenceAcrossRates=True,maximumBalanceError=max(t['balanceRelative'] for t in cases),
        maximumNominalReplay=max(t['nominalReplayRelative'] for t in cases if 'nominalReplayRelative' in t),
        structureBasisRevalidatedForPerturbations=False,acousticLoadIncluded=False,audibleSustainMeasured=False,
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_joint_decay.json').write_text(json.dumps(dict(summary=summary,cases=cases,rateChecks=checks,
        sourceFrozenSha256=sha,unisonManifestSha256=uh,regionManifestSha256=vh),indent=2,allow_nan=False))
    print('G3_JOINT_DECAY_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('joint decay proof failed')
if __name__=='__main__':main()
