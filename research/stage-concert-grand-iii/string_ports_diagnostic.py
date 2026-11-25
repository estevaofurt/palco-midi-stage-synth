"""G3.03g: full front/rear port proof; geometry and support values diagnostic."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from string_ports import PortString
from duplex_diagnostic import LOSS
from termination_diagnostic import LOAD,pulse
FRONT=dict(massKg=.02,stiffnessNm=1e8,dampingNsm=20.)
def run(r,N,cut,sr,frontRatio,rearRatio,drive):
    t=PortString(r,N,cut,sr,frontRatio,rearRatio,FRONT,LOAD,LOSS);h=1/sr
    work=err=inc=0.;trace=[];peak={}
    for i in range(round(.02*sr)):
        F=np.zeros(3);F[drive]=pulse(i*h,h);old=t.energy();work+=t.step(F);E=t.energy()
        err=max(err,abs(E+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,E-old)
        if (i+1)%(sr//4000)==0:
            e=t.partition()
            for name,x in e.items():peak[name]=max(peak.get(name,0.),x)
            trace.append(np.r_[t.position(),list(e.values()),list(t.losses.values())].tolist())
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0
    return dict(N=N,cutHz=cut,sr=sr,frontRatio=frontRatio,rearRatio=rearRatio,drive=drive,trace=trace,workJ=work,
        stored=t.partition(),losses=t.losses,peakStoredJ=peak,maxBalanceJ=err)
def compare(a,b):
    x,y=np.asarray(a['trace']),np.asarray(b['trace'])
    errors=[float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-20)) for i in range(x.shape[1])]
    return dict(errors=errors,gate=max(errors)<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--key',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21];f=.1;b=.25
    rows=[run(r,128,48000,192000,f,b,0),run(r,192,48000,192000,f,b,0),
          run(r,192,96000,384000,f,b,0),run(r,192,96000,768000,f,b,0),
          run(r,192,48000,384000,f,b,0),run(r,192,96000,768000,f,b,1),
          run(r,192,96000,768000,f,b,2),run(r,192,96000,768000,0.,b,0)]
    x=np.asarray(rows[3]['trace']);reciprocity=[]
    for j in (1,2):
        y=np.asarray(rows[4+j]['trace'])[:,0];reciprocity.append(float(np.linalg.norm(x[:,j]-y)/max(np.linalg.norm(x[:,j]),1e-30)))
    assert max(reciprocity)<=1e-7
    base=compare(rows[0],rows[1]);time=compare(rows[2],rows[3]);band=compare(rows[4],rows[2])
    summary=dict(key=a.key,simulations=len(rows),basis=base,time=time,band=band,reciprocity=reciprocity,
        maxBalanceJ=max(q['maxBalanceJ'] for q in rows),
        peakFrontDuplexFraction=rows[3]['peakStoredJ']['frontDuplex']/rows[3]['workJ'],
        peakRearDuplexFraction=rows[3]['peakStoredJ']['rearDuplex']/rows[3]['workJ'],
        gate=base['gate'] and time['gate'] and band['gate'],selectedGeometry=None,selectedLoads=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'string_ports.json').write_text(json.dumps(dict(summary=summary,rows=rows,frontLoad=FRONT,rearLoad=LOAD,
        scaleSha256=hashlib.sha256(raw).hexdigest(),scope='solid single wire, both mobile supports and duplex; no actual bridge'),indent=2,allow_nan=False))
    print('G3_STRING_PORTS_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'string ports convergence'
if __name__=='__main__':main()
