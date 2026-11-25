"""Predeclared rear-duplex comparison, no acoustical calibration."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from duplex_string import Duplex
from termination_diagnostic import LOAD,pulse
LOSS=dict(mainSigma0PerS=.1,mainSigma2S=1e-9,duplexSigmaPerS=1.)
MUTED=dict(LOSS,duplexSigmaPerS=200.)
ZERO=dict(mainSigma0PerS=0.,mainSigma2S=0.,duplexSigmaPerS=0.)
def run(r,N,cut,sr,ratio,loss):
    t=Duplex(r,N,cut,sr,LOAD,ratio,loss);h=1/sr;work=err=inc=0.;trace=[];peak=0.
    for i in range(round(.02*sr)):
        old=t.energy();work+=t.step([pulse(i*h,h),0.]);E=t.energy()
        err=max(err,abs(E+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,E-old)
        if (i+1)%(sr//4000)==0:
            p=t.partition();peak=max(peak,p['duplexJ'])
            trace.append(np.r_[t.position(),p['mainJ'],p['duplexJ'],p['loadJ'],t.lossMain,t.lossDuplex,t.b.loss].tolist())
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0
    assert (peak>0 if ratio else peak==0)
    return dict(N=N,cutHz=cut,sr=sr,ratio=ratio,lossParameters=loss,trace=trace,workJ=work,stored=t.partition(),
        lossMainJ=t.lossMain,lossDuplexJ=t.lossDuplex,lossSupportJ=t.b.loss,maxBalanceJ=err,peakDuplexJ=peak)
def compare(a,b):
    x,y=np.asarray(a['trace']),np.asarray(b['trace'])
    e=[float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-20)) for i in range(x.shape[1])]
    return dict(errors=e,gate=max(e)<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--key',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21];ratio=.25
    rows=[run(r,128,48000,192000,ratio,LOSS),run(r,192,48000,192000,ratio,LOSS),run(r,192,48000,384000,ratio,LOSS),
          run(r,192,96000,384000,ratio,LOSS),run(r,192,96000,768000,ratio,LOSS),
          run(r,192,96000,768000,ratio,MUTED),run(r,192,96000,768000,0.,LOSS),run(r,192,96000,768000,ratio,ZERO)]
    base=compare(rows[0],rows[1]);time=compare(rows[3],rows[4]);band=compare(rows[2],rows[3])
    summary=dict(key=a.key,simulations=len(rows),basis=base,time=time,band=band,
        maxBalanceJ=max(q['maxBalanceJ'] for q in rows),peakDuplexFraction=rows[4]['peakDuplexJ']/rows[4]['workJ'],
        lossDuplexFractions=[rows[i]['lossDuplexJ']/rows[i]['workJ'] for i in (4,5)],
        gate=base['gate'] and time['gate'] and band['gate'],selectedGeometry=None,selectedLoss=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'duplex.json').write_text(json.dumps(dict(summary=summary,rows=rows,load=LOAD,scaleSha256=hashlib.sha256(raw).hexdigest(),
        scope='single solid wire, rear duplex only, linear vertical, uncalibrated loss coefficients'),indent=2,allow_nan=False))
    print('G3_DUPLEX_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'duplex convergence'
if __name__=='__main__':main()
