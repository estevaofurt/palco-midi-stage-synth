"""Shared unison load: pulse one wire and observe the unforced wires."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from shared_unison import SharedUnison
from termination_diagnostic import LOAD,pulse
ROOT=Path(__file__).parent
def run(r,N,cut,sr,offset,drive):
    t=SharedUnison(r,N,cut,sr,LOAD,offset);n=r['count'];h=1/sr;work=err=inc=0.;peak=np.zeros(n);trace=[]
    for i in range(round(.04*sr)):
        old=t.energy();F=np.zeros(n+1);F[drive]=pulse(i*h,h)
        work+=t.step(F);E=t.energy();err=max(err,abs(E+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,E-old)
        if (i+1)%(sr//4000)==0:
            e,b=t.partition();peak=np.maximum(peak,e);trace.append(np.r_[t.position(),e,b,t.loss].tolist())
    e,b=t.partition()
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0
    assert max(peak[j] for j in range(n) if j!=drive)>0
    return dict(sr=sr,cutHz=cut,N=N,offsets=offset,drive=drive,trace=trace,workJ=work,lossJ=t.loss,wireEnergyJ=e,loadEnergyJ=b,
        peakWireEnergyJ=peak.tolist(),maxBalanceJ=err,modes=len(t.w2))
def compare(a,b):
    x,y=np.asarray(a['trace']),np.asarray(b['trace'])
    e=[float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-20)) for i in range(x.shape[1])]
    return dict(traceRelative=e,gate=max(e)<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21];n=r['count'];offset=np.linspace(-.5,.5,n).tolist();zero=[0.]*n
    rows=[run(r,256,48000,192000,offset,0),run(r,384,48000,192000,offset,0),run(r,384,48000,384000,offset,0),
          run(r,384,24000,192000,offset,0),run(r,384,48000,384000,offset,1),run(r,384,48000,384000,zero,0)]
    x=np.asarray(rows[2]['trace'])[:,1];y=np.asarray(rows[4]['trace'])[:,0]
    recip=float(np.linalg.norm(x-y)/max(np.linalg.norm(x),1e-30));assert recip<=1e-7
    base=compare(rows[0],rows[1]);time=compare(rows[1],rows[2]);band=compare(rows[3],rows[1])
    summary=dict(key=a.key,strings=n,simulations=len(rows),basis=base,time=time,band=band,reciprocity=recip,
        maxBalanceJ=max(q['maxBalanceJ'] for q in rows),peakUnforcedFraction=max(rows[2]['peakWireEnergyJ'][1:])/rows[2]['workJ'],
        finalWireFractions=[e/rows[2]['workJ'] for e in rows[2]['wireEnergyJ']],gate=base['gate'] and time['gate'] and band['gate'],selectedLoad=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'unison.json').write_text(json.dumps(dict(summary=summary,rows=rows,load=LOAD,scaleSha256=hashlib.sha256(raw).hexdigest(),scope='common vertical translation only; diagnostic tension offsets, not acoustic tuning'),indent=2,allow_nan=False))
    print('G3_UNISON_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'unison convergence'
if __name__=='__main__':main()
