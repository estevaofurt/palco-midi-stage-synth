"""Bridge coupled to adjacent notes, offline pulse verification."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from bridge_strings import centerline,Coupled
from termination_diagnostic import pulse
ROOT=Path(__file__).parent
def run(center,rows,keys,sub,N,cut,sr,cfg,section,drive):
    t=Coupled(center,rows,keys,sub,N,cut,sr,cfg,section)
    work=err=inc=0.;trace=[];peak=0.;h=1/sr
    for i in range(round(.02*sr)):
        old=t.energy();F=np.zeros(4);F[drive]=pulse(i*h,h);work+=t.step(F);E=t.energy()
        err=max(err,abs(E+t.loss-work))
        if i>=round(.001*sr):inc=max(inc,E-old)
        if (i+1)%(sr//4000)==0:
            e=t.partition();peak=max(peak,e[str(keys[1-drive])])
            trace.append(np.r_[t.position(),list(e.values()),list(t.losses.values())].tolist())
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and t.loss>=0 and peak>0
    return dict(subdiv=sub,N=N,cutHz=cut,sr=sr,drive=drive,trace=trace,workJ=work,stored=t.partition(),losses=t.losses,
        peakUnforcedJ=peak,maxBalanceJ=err,modes=len(t.w2))
def compare(a,b):
    x,y=np.asarray(a['trace']),np.asarray(b['trace'])
    e=[float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-20)) for i in range(x.shape[1])]
    return dict(errors=e,gate=max(e)<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--case',choices=['bass','middle','treble'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    cfg=json.loads((ROOT/'bridge_hypothesis.json').read_text());layout=layout_build(sc,json.loads((ROOT/'layout_hypothesis.json').read_text()))
    section='bass' if a.case=='bass' else 'treble';keys={'bass':[45,46],'middle':[60,61],'treble':[84,85]}[a.case]
    center=centerline(layout['bridgeAttachmentNodes'][section]);rr={r['key']:r for r in sc['rows']}
    def sim(sub,N,cut,sr,drive=0):return run(center,rr,keys,sub,N,cut,sr,cfg,section,drive)
    rows=[sim(2,256,24000,192000),sim(4,384,24000,192000),sim(4,384,48000,192000),sim(4,384,48000,384000),sim(4,384,48000,384000,1)]
    x=np.asarray(rows[3]['trace'])[:,1];y=np.asarray(rows[4]['trace'])[:,0]
    recip=float(np.linalg.norm(x-y)/max(np.linalg.norm(x),1e-30));assert recip<=1e-7
    base=compare(rows[0],rows[1]);band=compare(rows[1],rows[2]);time=compare(rows[2],rows[3])
    geometry={k:v for k,v in center.items() if k not in ('xyz','offsets','keys')}
    summary=dict(case=a.case,keys=keys,simulations=len(rows),geometry=geometry,base=base,band=band,time=time,reciprocity=recip,
        peakUnforcedFraction=rows[3]['peakUnforcedJ']/rows[3]['workJ'],maxBalanceJ=max(q['maxBalanceJ'] for q in rows),
        gate=base['gate'] and band['gate'] and time['gate'],bridgeReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'bridge_strings.json').write_text(json.dumps(dict(summary=summary,rows=rows,centerlineXYZ=center['xyz'].tolist(),centerlineKeys=center['keys'],wireOffsetsM=center['offsets'],
        scaleSha256=hashlib.sha256(raw).hexdigest(),scope='full section centerline beam, two representative wires, fixed front, temporary foundation, no duplex, no board or audio'),indent=2,allow_nan=False))
    print('G3_BRIDGE_STRINGS_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'coupled bridge convergence'
if __name__=='__main__':main()
