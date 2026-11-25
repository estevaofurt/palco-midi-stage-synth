"""Measure source reuse on the actual archived 628-element mesh.
Use a fixed subset of held-out target blocks; no new fit or full audit.
"""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from bem_third_strip_replay import validate_source
from bem_prepared_operator import PreparedOperator
from bem_p1_static_moments import operators
from bem_edge_audit import edge_samples
from exterior_bem import elements
from split_radiation import relative
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    doc=json.loads((a.archive/'bem_candidate.json').read_text())
    with np.load(a.archive/'candidate_matrices.npz',allow_pickle=False) as z:
        arrays={k:z[k] for k in ('triangles','labels','density','prescribed','computed','radiation','pressure')}
    validate_source(doc,arrays,30.,sha);t=arrays['triangles'];q=arrays['density']
    y,w=edge_samples(t,5);_,n,_=elements(t);N,Q=y.shape[:2]
    # Spread 192 targets over the full boundary; identical for all runs.
    ix=np.linspace(0,N*Q-1,192,dtype=int);o=ix//Q;x=y.reshape(-1,3)[ix];nn=n[o]
    k=2*np.pi*80/343.;rows=[]
    for order in (6,8,10):
        start=time.perf_counter();prepared=PreparedOperator(t,order);setup=time.perf_counter()-start
        def run(op):
            G=[];D=[]
            for i in range(0,len(x),24):
                sl=slice(i,i+24);g,d=op(t,x[sl],nn[sl],o[sl],k,order)
                G.append(g);D.append(d)
            return np.vstack(G),np.vstack(D)
        # Warm both paths, then alternate order to reduce timing bias.
        ref=run(operators);new=run(prepared)
        err=max(relative(v,w) for v,w in zip(ref,new));assert err<=1e-12
        flow=relative(ref[1]@q,new[1]@q);assert flow<=1e-12
        oldTimes=[];newTimes=[]
        for j in range(2):
            for op,ts in ((operators,oldTimes),(prepared,newTimes)) if j==0 else ((prepared,newTimes),(operators,oldTimes)):
                start=time.perf_counter();v=run(op);ts.append(time.perf_counter()-start)
                assert max(relative(a,b) for a,b in zip(v,ref))<=1e-12
        row=dict(sourceOrder=order,targets=len(x),elements=N,sourceBytes=prepared.sourceBytes,setupSeconds=setup,
            legacySeconds=oldTimes,preparedSeconds=newTimes,maximumRelative=err,flowRelative=flow,
            medianSpeedup=float(np.median(oldTimes)/np.median(newTimes)),gate=True)
        rows.append(row);print('G3_PREPARED_BEM_CASE '+json.dumps(row),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    summary=dict(gate=True,diagnosticOnly=True,angleDeg=30,frequencyHz=80,fullAuditBenchmark=False,solverApproved=False,radiationReady=False)
    (a.out/'prepared_bem.json').write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_PREPARED_BEM_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
