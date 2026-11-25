"""Small-amplitude axial mechanism proof, no audio or loading."""
import argparse,json,math
from pathlib import Path
import numpy as np
from axial_fixture import AxialFixture
def run(r,sr,amp,angle):
    t=AxialFixture(r,sr,amp,angle);E0=t.energy();err=dg=peak=force=0.;ss=0.;n=round(.002*sr)
    for _ in range(n):
        dg=max(dg,t.step());err=max(err,abs(t.energy()-E0))
        peak=max(peak,abs(float(t.q[2])));force=max(force,abs(float(t.axial_force())));ss+=float(t.q[2])**2
    assert err<=max(1e-12,E0*1e-7) and dg<=1e-12 and peak>0
    return dict(sr=sr,amplitudeM=amp,angle=angle,peakAxialM=peak,rmsAxialM=math.sqrt(ss/n),peakDynamicRearForceN=force,maxBalanceJ=err,maxGradientWorkResidualJ=dg,initialJ=E0)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--key',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    sc=json.loads(a.scale.read_text());assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21];rows=[];checks=[]
    for amp in (.00005,.0001):
        lo=run(r,1536000,amp,0.);hi=run(r,3072000,amp,0.);rot=run(r,3072000,amp,.6)
        rows.extend([lo,hi,rot])
        errors={k:abs(lo[k]-hi[k])/max(abs(hi[k]),1e-20) for k in ('peakAxialM','rmsAxialM','peakDynamicRearForceN')}
        rotation=max(abs(rot[k]-hi[k])/max(abs(hi[k]),1e-20) for k in errors)
        checks.append(dict(errors=errors,rotationRelative=rotation,gate=max(errors.values())<=.05 and rotation<=1e-6))
    ratio=rows[4]['peakAxialM']/rows[1]['peakAxialM']
    summary=dict(key=a.key,simulations=len(rows),checks=checks,axialAmplitudeRatio=ratio,maxBalanceJ=max(q['maxBalanceJ'] for q in rows),gate=all(c['gate'] for c in checks) and 3.8<=ratio<=4.2,longitudinalReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'axial.json').write_text(json.dumps(dict(summary=summary,rows=rows,scope='solid fixed-end 3-coordinate conservative fixture only; no calibrated longitudinal output'),indent=2,allow_nan=False))
    print('G3_AXIAL_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'axial convergence'
if __name__=='__main__':main()
