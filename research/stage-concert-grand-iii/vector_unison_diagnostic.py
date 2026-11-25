"""Vector unison cross-wire cross-polarization pulse proof."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from vector_unison import VectorUnison
from polarization_diagnostic import ANISO,ISO,ANGLE
from termination_diagnostic import pulse
ROOT=Path(__file__).parent
def run(r,N,cut,sr,load,angle,drive):
    n=r['count'];t=VectorUnison(r,N,cut,sr,load,angle,np.linspace(-.5,.5,n).tolist())
    h=1/sr;work=err=inc=0.;trace=[];peak=np.zeros((n+1,2))
    for i in range(round(.02*sr)):
        F=np.zeros((n+1,2));F[drive]=pulse(i*h,h);E=t.energy();work+=t.step(F)
        err=max(err,abs(t.energy()+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,t.energy()-E)
        pos=t.position();peak=np.maximum(peak,abs(pos))
        if (i+1)%(sr//4000)==0:
            e,b=t.partition();trace.append(np.r_[pos.ravel(),e,b,t.loss].tolist())
    e,b=t.partition();assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0
    return dict(trace=trace,peakM=peak.tolist(),workJ=work,wireEnergyJ=e,loadEnergyJ=b,lossJ=t.loss,maxBalanceJ=err)
def compare(a,b):
    x,y=np.asarray(a['trace']),np.asarray(b['trace'])
    e=[float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-20)) for i in range(x.shape[1])]
    return dict(errors=e,gate=max(e)<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--key',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21];n=r['count'];assert n>=2
    rows=[run(r,256,48000,192000,ANISO,ANGLE,(0,0)),run(r,384,48000,192000,ANISO,ANGLE,(0,0)),
          run(r,384,48000,384000,ANISO,ANGLE,(0,0)),run(r,384,24000,192000,ANISO,ANGLE,(0,0)),
          run(r,384,48000,384000,ANISO,ANGLE,(1,1)),run(r,384,48000,384000,ISO,ANGLE,(0,0)),
          run(r,384,48000,384000,ANISO,0.,(0,0))]
    x=np.asarray(rows[2]['trace'])[:,3];y=np.asarray(rows[4]['trace'])[:,0]
    reciprocal=float(np.linalg.norm(x-y)/max(np.linalg.norm(x),1e-30));assert reciprocal<=1e-7
    assert rows[2]['peakM'][1][1]>1e-12
    for q in rows[5:]:assert np.max(np.asarray(q['peakM'])[:,1])<=1e-12
    base=compare(rows[0],rows[1]);time=compare(rows[1],rows[2]);band=compare(rows[3],rows[1])
    summary=dict(key=a.key,simulations=len(rows),basis=base,time=time,band=band,reciprocity=reciprocal,
        peakUnforcedLateralM=rows[2]['peakM'][1][1],maxBalanceJ=max(q['maxBalanceJ'] for q in rows),
        gate=base['gate'] and time['gate'] and band['gate'],selectedLoad=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'vector_unison.json').write_text(json.dumps(dict(summary=summary,rows=rows,scaleSha256=hashlib.sha256(raw).hexdigest(),scope='co-diagonal diagnostic shared support; not real bridge'),indent=2,allow_nan=False))
    print('G3_VECTOR_UNISON_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'vector unison convergence'
if __name__=='__main__':main()
