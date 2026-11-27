from pathlib import Path
import json,time,numpy as np
from compact_mechanics import assemble_compact
from dynamic_dampers import Dampers,DynamicWet
from sequential_impact import sequential
from wet_sparse import Cache,Timed,temporal,timing
from bridge import scales
from fused import FusedGrouped
from coupled369 import direct
from scheduled_stream import ScheduledStream
import replay as r
class ClosedA2(Dampers):
    def fractions(self,held,pedal):
        f=super().fractions(held,pedal);f[self.keys==45]=1.;return f
ROOT=Path(__file__).parent;root=ROOT.parent/'G3_consolidacao_20261127';N=38400;keys=[48,60,64];ranks={45:64,48:128,60:64,64:64};FS=384000
r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);r.load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(ROOT.parent/'G3_Acoplamento_369/grid-b64.npz');A,B=g['A'],g['B'];s=scales(z,g);Q=r.basis(1,1);G=temporal(g['G'],Q,N);c=FusedGrouped(z,A,B,Q);e=ScheduledStream(G,A,B,Q,32);Z=c.D+direct(G,A,B);del G
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(root/'G3_Base_Estrutural/integrated_80.npz');M,K,D,P,w=assemble_compact(base,scale,[45,48,60,64],ranks);dam=Dampers(D,w,scale);ids=[j for j,(a,*_) in enumerate(w) if a['key'] in keys];groups=[keys.index(w[j][0]['key']) for j in ids];P=P[:,ids]
t=DynamicWet(Cache(c),Cache(e),Z,s,M,K,dam,keys)
for _ in range(130):t.step(np.zeros(M.n))
# First key held; pedal down at 5 ms, subsequent launches at 15/30 ms.
commands={round(ms*FS/1000):(held,ped) for ms,held,ped in [(5,[48],1),(15,[48,60],1),(30,keys,1),(40,[60,64],1),(55,keys,1),(65,[48,64],1),(70,[48],1),(75,[48],0),(85,[],0)]}
launches=[(0,48,.3),(5760,60,1.),(11520,64,3.),(21120,48,1.)]
import sys
for variant in (sys.argv[1:] or ['pedal','a2-closed']):
    dam=(ClosedA2 if variant=='a2-closed' else Dampers)(D,w,scale)
    t=DynamicWet(Cache(c),Timed(e),Z,s,M,K,dam,[48]);events=[]
    def command(a,j):
        if j not in commands:return False
        held,pedal=commands[j];q=a.q.copy();v=a.v.copy();h0=a.c.history().copy();h1=a.e.history().copy();before=a.fractions.copy();t0=a.e.t;start=time.perf_counter();changed=a.command(held,pedal);elapsed=time.perf_counter()-start
        assert np.array_equal(a.q,q) and np.array_equal(a.v,v) and np.array_equal(a.c.history(),h0) and np.array_equal(a.e.history(),h1) and a.e.t==t0
        events.append(dict(step=j,held=held,pedal=pedal,changed=changed,before=before.tolist(),after=a.fractions.tolist(),update_ms=elapsed*1000));return changed
    start=time.perf_counter();row,signals=sequential(t,P,groups,keys,launches,N,command=command);row.update(ranks=ranks,seconds=time.perf_counter()-start,events=events,history_timing=timing(t.e.hist),commit_timing=timing(t.e.com),exterior_bytes=e.bytes,history_lags=e.L,commands_ms=[5,15,30,40,55,65,70,75,85]);(ROOT/f'{variant}.json').write_text(json.dumps(row,indent=2));np.savez_compressed(ROOT/f'{variant}.npz',**signals);print(variant,json.dumps(row),flush=True)
