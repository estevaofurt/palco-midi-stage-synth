"""Independent reference and timing on the actual 80-mode/10-wire model."""
import argparse,json,time,copy
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur
from distributed_felt import contact,damping_levels
from fixed_contact_midpoint import FixedContacts
from split_radiation import relative
def run(z,wires,rows,rate,n,width,level):
    ww=copy.deepcopy(wires)
    for j,w in enumerate(ww):w.port=j
    make=lambda:Compiled(z['stiffness'],z['damping'],np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
    a,b,c=make(),make(),make();B,I,wt=contact(a,rows,width)
    groups=np.array([w.port for w in wires]);d=2./np.bincount(groups)[groups]*level
    d=damping_levels(d,wt)
    A,R,C=[PointSchur(v,B,I) for v in (a,b,c)]
    for t in (A,R,C):t.set_levels(d)
    fixed=FixedContacts(A);warm=FixedContacts(C)
    f=np.random.default_rng(28).normal(size=(513,len(ww)));f[256:]=0.
    o=np.zeros_like(f);l=np.zeros((len(f),2));acc=np.zeros((len(f),80))
    warm.process(f,o,l,acc)
    start=time.perf_counter();fixed.process(f,o,l,acc);compiled=time.perf_counter()-start
    ref=[];led=[];ar=[];start=time.perf_counter()
    for F in f:
        old=b.v.copy();y,w,k=R.step(F);ref.append(y);led.append([w,k]);ar.append((b.v-old)*rate)
    python=time.perf_counter()-start
    errors=dict(observer=relative(o,np.array(ref)),ledger=relative(l,np.array(led)),acceleration=relative(acc,np.array(ar)),
        state=relative(np.asarray(A.state()),np.asarray(R.state())),
        balance=abs(a.energy()+l[:,1].sum()-l[:,0].sum())/max(abs(l[:,0]).sum(),a.energy(),1e-30))
    if max(errors.values())>1e-8 or min(l[:,1])<-1e-18:raise ValueError(str(errors))
    result=dict(rate=rate,partials=n,widthM=width,level=level,errors=errors,compiledUsPerSample=compiled*1e6/len(f),
        referenceUsPerSample=python*1e6/len(f),speedup=python/max(compiled,1e-30))
    print('G3_FIXED_CONTACT_CASE '+json.dumps(result),flush=True)
    return result
def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    cases=[run(z,wires,rows,r,n,w,d) for r,n in ((48000,32),(96000,32),(48000,64)) for w in (0.,.020) for d in (.5,1.)]
    summary=dict(gate=True,cases=len(cases),maximumError=max(max(v['errors'].values()) for v in cases),
        minimumSpeedup=min(v['speedup'] for v in cases),diagnosticOnly=True,realTimeApproved=False,sourceFrozenSha256=sha)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'fixed_contact_midpoint.json').write_text(json.dumps(dict(summary=summary,cases=cases),indent=2))
    print('G3_FIXED_CONTACT_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
