"""G3.12u: controlled C4 unison detuning by tension, not output oscillators.
Same structural basis, geometry, damping law and hammer hypothesis.
No acoustic loading, audio calibration or selected tuning."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.linalg import eigh
from string_ports import element
from string_structure import Wire
from wire_physical_midpoint import load
from physical_long_decay import startup
from physical_loss_sensitivity import partition,prepare,simulate,crossings
from felt_law import params

def tension_multiplier(frequency,cents):
    if not np.isfinite(cents):raise ValueError('invalid cents')
    base=frequency(1.)
    if not np.isfinite(base) or base<=0:raise ValueError('invalid frequency')
    if cents==0:return 1.
    target=base*2**(cents/1200)
    return float(brentq(lambda x:frequency(x)/target-1.,.95,1.05,xtol=1e-13))

def offsets(count,spread):
    if type(count)!=int or count<1 or not np.isfinite(spread) or spread<0:raise ValueError('unison offsets')
    return np.linspace(-spread,spread,count) if count>1 else np.zeros(1)

def detune(wires,rows,spread):
    selected=[w for w in wires if w.port==2]
    result=[];record=[]
    for w in wires:
        if w.port!=2:result.append(w);continue
        row=rows[60];N=len(w.w2);c=float(offsets(len(selected),spread)[selected.index(w)])
        def frequency(multiplier):
            rr=dict(row,tensionPerStringN=row['tensionPerStringN']*multiplier)
            M,K,_=element(rr,N)
            return np.sqrt(eigh(K[2:,2:],M[2:,2:],subset_by_index=[0,0],eigvals_only=True)[0])/(2*np.pi)
        m=tension_multiplier(frequency,c)
        x=Wire(dict(row,tensionPerStringN=row['tensionPerStringN']*m),N,w.rear,w.port,w.id)
        actual=float(1200*np.log2(np.sqrt(x.w2[0]/w.w2[0])))
        if abs(actual-c)>1e-6:raise ValueError('detuning tolerance')
        result.append(x);record.append(dict(wireId=w.id,targetCents=c,actualCents=actual,tensionMultiplier=m,
            fixedRearFundamentalHz=float(np.sqrt(x.w2[0])/(2*np.pi))))
    return result,record

def observations(model,O,groups):
    ids=np.flatnonzero(np.asarray(groups)==2);count=len(ids)
    P=model.P[:,ids];R=np.eye(count)-np.ones((count,count))/count
    # Individual and differential velocities; mean and plate retained.
    return np.column_stack([O,P,P@R]),count

def metrics(rms,count,ref):
    mean,plate=rms[:,0],rms[:,1]
    individual=np.sqrt(np.mean(rms[:,2:2+count]**2,axis=1))
    differential=np.sqrt(np.mean(rms[:,2+count:]**2,axis=1))
    ratio=np.divide(differential**2,individual**2,out=np.zeros_like(individual),where=individual>1e-25)
    identity=float(np.max(abs(individual**2-mean**2-differential**2))/max(np.max(individual**2),1e-30))
    if identity>1e-8 or max(ratio)>1+1e-8:raise ValueError('unison observation partition')
    out={}
    for i,(name,value) in enumerate(zip(('meanWire','plate','individualRms','differentialRms'),(mean,plate,individual,differential))):
        out[name]=dict(peakRmsMps=float(value.max()),
            commonThresholds=crossings(value,ref[i]) if ref[i]>0 else None,
            ownThresholds=crossings(value,value.max()) if value.max()>1e-15 else None)
    return dict(observationIdentity=identity,observations=out,
        differentialEnergyProxyFraction=[dict(timeS=t,fraction=float(np.mean(ratio[max(0,round(t/.05)-20):round(t/.05)]))) for t in (1,5,10,15,20,30,40)],
        rmsMps=[mean.tolist(),plate.tolist(),individual.tolist(),differential.tolist()])

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','decay','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.decay/'physical_long_decay.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,cases=36,key=60,acousticLoadIncluded=False,audibleSustainMeasured=False).items()):raise ValueError('unapproved decay source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'));rows['_platePort']=z['ports'][:,6]
    rate=48000;cases=[];variants=[]
    for spread in (0.,.25,.5,1.,2.):
        ww,records=detune(wires,rows,spread);variants.append(dict(spreadCents=spread,wires=records))
        for n in (16,32):
            states=[startup(k,D,A,ww,rows,groups,masses,felts,rate,n,1.,speed) for speed in (.3,3.)]
            model,q,v,O,_=states[0];O,count=observations(model,O,groups);G,audit=partition(model)
            prepared=prepare(model.M,model.K,G,O,1/rate,2400);pending=[]
            for speed,(m,q,v,o,init) in zip((.3,3.),states):
                o,c=observations(m,o,groups)
                if c!=count or not np.array_equal(m.D,model.D) or not np.array_equal(o,O):raise ValueError('inconsistent unison state')
                result,rms=simulate(prepared,q,v);pending.append((speed,result,rms,init))
            # Fixed common reference per rank, from approved zero-spread strong case.
            if spread==0.:
                if n==16:refs={}
                rr=pending[1][2]
                refs[n]=[float(rr[:,0].max()),float(rr[:,1].max()),float(np.sqrt(np.mean(rr[:,2:2+count]**2,axis=1)).max()),float(rr[:,0].max())]
            for speed,result,rms,init in pending:
                x=metrics(rms,count,refs[n])
                row=dict(rate=rate,partials=n,pedal=1.,hammerSpeedMps=speed,spreadCents=spread,partition=audit,
                    commonReferenceRmsMps=refs[n],**init,**result,**x)
                # Verify the unperturbed case against the independently approved decay.
                if spread==0.:
                    ref=next(v for v in d['cases'] if v['rate']==rate and v['partials']==n and v['pedal']==1. and v['hammerSpeedMps']==speed)
                    replay=abs(row['initialEnergyJ']-ref['initialEnergyJ'])/ref['initialEnergyJ']
                    for name,old in (('meanWire','c4HammerPointVelocity'),('plate','platePortVelocity')):
                        replay=max(replay,abs(row['observations'][name]['peakRmsMps']/ref['metrics'][old]['peakRmsMps']-1.))
                    if replay>1e-7:raise ValueError('nominal replay')
                    row['nominalReplayRelative']=replay
                cases.append(row)
                print('G3_UNISON_DECAY_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('rmsMps','snapshots')},allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),cases=len(cases),diagnosticOnly=True,physicalHypothesis=True,
        calibratedParameters=False,selectedSpreadCents=None,acousticLoadIncluded=False,audibleSustainMeasured=False,
        maximumEnergyError=max(v['balanceRelative'] for v in cases),maximumObservationIdentity=max(v['observationIdentity'] for v in cases),
        maximumNominalReplay=max(v['nominalReplayRelative'] for v in cases if 'nominalReplayRelative' in v),
        structureBasisRevalidatedForDetuning=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_unison_decay.json').write_text(json.dumps(dict(summary=summary,variants=variants,cases=cases,
        sourceFrozenSha256=sha,decayManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_UNISON_DECAY_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('unison decay proof failed')
if __name__=='__main__':main()
