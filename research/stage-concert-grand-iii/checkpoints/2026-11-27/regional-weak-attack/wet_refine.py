"""Fine mechanical midpoint coupling with full aperture at every acoustic substep."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from assembly_rank import assemble
from hammer import Wet,impact
from bridge import scales
from fused import FusedGrouped
from coupled369 import direct
from constant_stream import ConstantStream
from parallel_stream import ParallelStream
import replay as r
from scipy.linalg import eigvalsh
ROOT=Path(__file__).parent
class Cache:
    """History is immutable until commit/step or reset; avoid duplicate preview."""
    def __init__(self,obj): self.obj=obj;self.h=None
    def __getattr__(self,k): return getattr(self.obj,k)
    def history(self):
        if self.h is None:self.h=self.obj.history()
        return self.h
    def step(self,*args):
        y=self.obj.step(*args);self.h=None;return y
    def commit(self,*args):
        y=self.obj.commit(*args);self.h=None;return y
    def reset(self):self.obj.reset();self.h=None

def temporal(G,Q,N):
    m,d=Q.shape;n=G.shape[-1];L=min(N,(G.shape[1]+m-2)//m+1);K=np.zeros((2,L,d,d,n,n))
    for a in range(m):
        for b in range(m):
            l=np.arange(L)*m+a-b;ok=(l>=0)&(l<G.shape[1]);K[:,ok]+=G[:,l[ok],None,None]*np.outer(Q[a],Q[b])[None,None,:,:,None,None]
    return K

def main():
    p=argparse.ArgumentParser();p.add_argument('--rate',type=int,required=True);p.add_argument('--partials',type=int,default=32);p.add_argument('--speed',type=float,nargs='+',default=[.3,3.]);p.add_argument('--ms',type=float,default=4.);p.add_argument('--key',type=int,choices=[48,60,64],default=60);p.add_argument('--parallel',action='store_true');a=p.parse_args();assert 384000%a.rate==0
    root=ROOT.parent/'G3_consolidacao_20261127';prior=ROOT.parent/'G3_Acoplamento_369';N=round(a.ms/1000*a.rate);m=384000//a.rate
    r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);r.load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(prior/'grid-b64.npz');A,B=g['A'],g['B'];s=scales(z,g);Q=r.basis(m,m);G=temporal(g['G'][:,:m*N],Q,N);c=FusedGrouped(z,A,B,Q);e=(ParallelStream if a.parallel else ConstantStream)(G,A,B,Q);Z=c.D+direct(G,A,B);del G
    scale=json.loads((ROOT/'scale_geometry.json').read_text());i0=np.load(root/'G3_Base_Estrutural/integrated_80.npz');M,K,D,P,L,wires=assemble(i0,scale,a.key,a.partials);P=P[:,[j for j,(w,*_) in enumerate(wires) if w['key']==a.key]]
    for speed in a.speed:
        t=Wet(Cache(c),Cache(e),Z,s,M,K,D,L);start=time.perf_counter();row,signals=impact(t,P,a.key,speed,N);row.update(partials=a.partials,m=m,seconds=time.perf_counter()-start,symmetry=e.symmetry_error,history_lags=e.L,parallel=a.parallel);name=f'{a.key}-{a.partials}-{a.rate}-{speed}-{N}';(ROOT/(name+'.json')).write_text(json.dumps(row,indent=2));np.savez_compressed(ROOT/(name+'.npz'),**signals);print(json.dumps(row),flush=True)
if __name__=='__main__':main()
