"""Polarization cross-mobility proof with unchanged string scale."""
import argparse,json,hashlib,math
from pathlib import Path
import numpy as np
from polarized_wire import PolarizedWire
from termination_diagnostic import pulse
ISO=dict(massKg=.005,stiffnessNm=[1e6,1e6],dampingNsm=[5.,5.])
ANISO=dict(massKg=.005,stiffnessNm=[1e6,4e6],dampingNsm=[5.,10.])
ANGLE=math.radians(25.)
def simulate(r,N,cut,sr,load,angle,drive):
    t=PolarizedWire(r,N,cut,sr,load,angle);h=1/sr;work=err=inc=0.;trace=[];peak=np.zeros((2,2))
    for i in range(round(.02*sr)):
        F=np.zeros((2,2));F[drive]=pulse(i*h,h);old=t.energy()
        z=t.step(F);work+=z['work'];err=max(err,abs(t.energy()+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,t.energy()-old)
        pos=t.position();peak=np.maximum(peak,abs(pos))
        if (i+1)%(sr//4000)==0:trace.append(pos.tolist())
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0
    return dict(cutHz=cut,sr=sr,angle=angle,load=load,drive=list(drive),workJ=work,lossJ=t.loss,storedJ=t.energy(),loadStoredJ=t.load_energy(),maxBalanceJ=err,peakM=peak.tolist(),trace=trace)
def compare(a,b):
    x=np.asarray(a['trace']);y=np.asarray(b['trace'])
    errors={f'port{p}axis{d}':float(np.linalg.norm(x[:,p,d]-y[:,p,d])/max(np.linalg.norm(y[:,p,d]),1e-20)) for p in range(2) for d in range(2)}
    for k in ('workJ','lossJ','storedJ'):errors[k]=abs(a[k]-b[k])/max(abs(b[k]),1e-20)
    return dict(errors=errors,gate=max(errors.values())<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--key',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][a.key-21]
    rows=[simulate(r,768,96000,384000,ANISO,ANGLE,(0,0)),simulate(r,768,96000,768000,ANISO,ANGLE,(0,0)),
          simulate(r,768,72000,384000,ANISO,ANGLE,(0,0)),simulate(r,768,96000,768000,ANISO,ANGLE,(1,1)),
          simulate(r,768,96000,384000,ISO,ANGLE,(0,0)),simulate(r,768,96000,384000,ANISO,0.,(0,0))]
    x=np.array(rows[1]['trace'])[:,1,1];y=np.array(rows[3]['trace'])[:,0,0]
    reciprocal=float(np.linalg.norm(x-y)/max(np.linalg.norm(x),1e-30))
    assert reciprocal<=1e-7
    for q in rows[4:]:assert np.max(np.asarray(q['peakM'])[:,1])<=1e-12
    assert rows[1]['peakM'][1][1]>1e-12
    time=compare(rows[0],rows[1]);band=compare(rows[2],rows[0])
    summary=dict(key=a.key,simulations=6,reciprocity=reciprocal,time=time,band=band,maxBalanceJ=max(x['maxBalanceJ'] for x in rows),
        peakRearVerticalM=rows[1]['peakM'][1][0],peakRearLateralM=rows[1]['peakM'][1][1],gate=time['gate'] and band['gate'],selectedLoad=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'polarization.json').write_text(json.dumps(dict(summary=summary,rows=rows,scaleSha256=hashlib.sha256(raw).hexdigest(),scope='linear vector wire with rotated co-diagonal diagnostic rear load only'),indent=2,allow_nan=False))
    print('G3_POLARIZATION_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'polarization convergence'
if __name__=='__main__':main()
