from pathlib import Path
import json,time,numpy as np
from regional_compact import assemble_regional
from assembly_rank import SPREAD
from dynamic_dampers import Dampers,DynamicWet
from sequential_stream import sequential
from wet_sparse import Cache,Timed,temporal,timing
from bridge import scales
from fused import FusedGrouped
from coupled369 import direct
from scheduled_stream import ScheduledStream
import replay as r
from refined_cavity import factory
import argparse
p=argparse.ArgumentParser();p.add_argument("--rate",type=int,choices=[192000,384000],default=384000);p.add_argument("--rank",choices=["mixed","uniform"],default="mixed");p.add_argument("--control",choices=["pedal","closed"],default="pedal");p.add_argument("--coeff",choices=["refined","historic"],default="refined");p.add_argument("--ms",type=int,choices=[18,50,100,150,200,250],default=250);args=p.parse_args()
class ClosedAdded(Dampers):
    def fractions(self,held,pedal):
        f=super().fractions(held,pedal);f[np.isin(self.keys,[33,55,72])]=1.;return f
ROOT=Path(__file__).parent;root=ROOT.parent/'G3_consolidacao_20261127';N=round(args.ms/1000*args.rate);keys=[48,60,64];ranks={33:64,45:64,48:128,55:64,60:64,64:64,72:64};ranks={k:128 for k in ranks} if args.rank=="uniform" else ranks;spread={k:SPREAD.get(k,0.) for k in ranks};shift={k:5.5 if k==48 else 0. for k in ranks};FS=args.rate;m=384000//FS
r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);r.load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(ROOT.parent/'G3_Acoplamento_369/grid-b64.npz');A,B=g['A'],g['B'];s=scales(z,g);Q=r.basis(m,m);G=temporal(g['G'],Q,N);original=r.Cavity
try:
    if args.coeff=="refined":r.Cavity=factory(original)
    c=FusedGrouped(z,A,B,Q)
finally:r.Cavity=original
e=ScheduledStream(G,A,B,Q,32);Z=c.D+direct(G,A,B);del G
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(root/'G3_Base_Estrutural/integrated_80.npz');M,K,D,P,w=assemble_regional(base,scale,list(ranks),ranks,spread,shift);dam=Dampers(D,w,scale);ids=[j for j,(a,*_) in enumerate(w) if a['key'] in keys];groups=[keys.index(w[j][0]['key']) for j in ids];P=P[:,ids]
t=DynamicWet(Cache(c),Cache(e),Z,s,M,K,dam,keys)
for _ in range(130):t.step(np.zeros(M.n))
# 18 ms is an exact regression schedule; longer tests use an explicit experimental event schedule.
if args.ms==18:
    timeline=[(1,[48,60],0),(2,keys,0),(2.5,keys,1),(5,[48,64],1),(6,[64],1),(8,[48,64],1),(12,[],0),(15,[],1)]
    strikes=[(0,48,.3),(1,60,1.),(2,64,3.)]
else:
    timeline=[(5,[48],1),(15,[48,60],1),(30,keys,1),(40,[60,64],1),(55,keys,1),(65,[48,64],1),(70,[48],1),(75,[48],0),(85,[],0),(105,[],1),(120,[60],1),(145,[],1),(160,[64],1),(185,[],1),(200,[],0)]
    strikes=[(0,48,.3),(15,60,1.),(30,64,3.),(55,48,1.),(120,60,.7),(160,64,.5)]
commands={round(ms*FS/1000):(held,ped) for ms,held,ped in timeline if ms<args.ms}
launches=[(round(ms*FS/1000),key,speed) for ms,key,speed in strikes if ms<args.ms]
for variant in [f'long-{args.ms}ms-{args.coeff}-{FS}-{args.rank}-{args.control}']:
    dam=(ClosedAdded if args.control=='closed' else Dampers)(D,w,scale)
    t=DynamicWet(Cache(c),Timed(e),Z,s,M,K,dam,[48]);events=[]
    def command(a,j):
        if j not in commands:return False
        held,pedal=commands[j];q=a.q.copy();v=a.v.copy();h0=a.c.history().copy();h1=a.e.history().copy();before=a.fractions.copy();t0=a.e.t;start=time.perf_counter();changed=a.command(held,pedal);elapsed=time.perf_counter()-start
        assert np.array_equal(a.q,q) and np.array_equal(a.v,v) and np.array_equal(a.c.history(),h0) and np.array_equal(a.e.history(),h1) and a.e.t==t0
        events.append(dict(step=j,held=held,pedal=pedal,changed=changed,before=before.tolist(),after=a.fractions.tolist(),update_ms=elapsed*1000));return changed
    start=time.perf_counter();row,signals=sequential(t,P,groups,keys,launches,N,command=command,output=ROOT/variant);row.update(coeff=args.coeff,control=args.control,m=m,ranks=ranks,spread=spread,shift=shift,seconds=time.perf_counter()-start,events=events,history_timing=timing(t.e.hist),commit_timing=timing(t.e.com),exterior_bytes=e.bytes);(ROOT/f'{variant}.json').write_text(json.dumps(row,indent=2));print(variant,json.dumps(row),flush=True)
