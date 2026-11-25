"""Closed rigid sphere benchmark; does not certify the grand piano lid."""
import argparse,json
from pathlib import Path
import numpy as np
from rigid_scattering import benchmark
from split_radiation import relative
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'rigid_scattering.json'
    sources=np.array([[1.2,.3,.2],[.1,-1.4,.3],[-1.2,.1,.4]])
    observers=np.array([[1.5,1.,.5],[-.6,1.4,.2],[.2,.3,1.5]])
    rows=[];outputs=[];frequencies=[30.,50.,80.,110.,150.]
    for n in (24,48,96,144):
        y=[];z=[];reports=[]
        for f in frequencies:
            v,w,q=benchmark(.55,2*np.pi*f/343.,sources,observers,n);y.append(v);z.append(w);reports.append(dict(frequencyHz=f,**q))
        row=dict(sources=n,gate=all(q['gate'] for q in reports),reports=reports)
        for key in ('heldoutBoundaryResidual','scatteredPressureRelative','reciprocity','powerRelative'):
            row[key]=max(q[key] for q in reports)
        rows.append(row);outputs.append((np.array(y),np.array(z)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_SCATTER_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[dict(pressure=relative(x[0],y[0]),impedance=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and max(checks[-1].values())<=.01
    summary=dict(gate=gate,convergence=checks,closedObstacleBenchmarkOnly=True,finiteLidReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=frequencies),indent=2,allow_nan=False))
    print('G3_SCATTER_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
