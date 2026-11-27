"""Fine causal 384 kHz reference with d3 upper input fixed; d8 lower equivalent."""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.linalg import lu_factor,lu_solve
import replay as r
from coupled369 import Grouped,direct
from causal import SpatialStream
from spatial import rel
FS=384000
class FineStream(SpatialStream):
    def __init__(self,G,A,B,steps):
        # Only lags observable in the finite prefix; exact on that prefix.
        super().__init__(G[:, :steps,None,None], A,B)
        self.imag_ratio=float(np.max(abs(self.F.imag))/max(np.max(abs(self.F.real)),1e-300))
        assert self.imag_ratio<1e-13
        self.F=self.F.real.copy()
    def history_spec(self):
        n=min(self.t,self.L-1);y=np.zeros_like(self.X[0]);assert self.t<=self.L
        if n:
            x=self.X[self.t-n:self.t][::-1];f=self.F[:,1:n+1,0,0]
            for k in range(2):
                for a in (0,1):
                    xx=x[:,k^a,0];ff=f[a]
                    y[k,0].real+=np.einsum('lij,lij->ij',ff,xx.real)
                    y[k,0].imag+=np.einsum('lij,lij->ij',ff,xx.imag)
        return y
    def commit(self,u,h):
        x=self.encode(u);y=h+self.decode(self.direct_spec(x));self.X[self.t%self.L]=x;self.t+=1;return y

def run(c,s,fac,T,top,flow=None):
    c.reset();s.reset();p=c.p;U=[];I=[];O=[];loss=wi=we=wt=scale=energy=work=0.;mins=np.zeros(3);start=time.perf_counter()
    for j,v in enumerate(top):
        ch=c.history();eh=s.history();u=np.r_[v,lu_solve(fac,-(T@v+(ch+eh)[0,p:]))] if flow is None else flow[j]
        yi,dl,E=c.step(u[None]);ye=s.commit(u[None],eh);yi=yi[0];ye=ye[0];y=yi+ye
        a=float(u@yi/FS);b=float(u@ye/FS);k=float(v@y[:p]/FS);wi+=a;we+=b;wt+=k;loss+=dl;scale+=abs(a)+abs(b);mins=np.minimum(mins,[wi,we,wt]);energy=max(energy,abs(wi-loss-E)/max(scale,1e-300));work=max(work,abs(wt-wi-we)/max(scale,1e-300));U.append(u);I.append(yi);O.append(ye)
    U,I,O=map(np.array,(U,I,O));Y=I+O;den=max(np.linalg.norm(I[:,p:])+np.linalg.norm(O[:,p:]),1e-300)
    return dict(flow=U,inside=I,exterior=O,load=Y[:,:p],residual=Y[:,p:]),dict(energy=energy,work_final=abs(wt-wi-we)/max(scale,1e-300),work_max_fine_prefix=work,min_work=(mins/max(scale,1e-300)).tolist(),fine_res=float(np.linalg.norm(Y[:,p:])/den),seconds=time.perf_counter()-start)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('previous',type=Path);ap.add_argument('--blocks',type=int,default=64);ap.add_argument('--kinds',nargs='+',default=['noise','pulse','high']);a=ap.parse_args();out=Path(__file__).parent
    for base,manifest in [(a.root,out/'INPUT_SHA256SUMS'),(a.previous,a.previous/'SHA256SUMS')]:
        for h,name in (line.split(maxsplit=1) for line in manifest.read_text().splitlines() if line.strip()):assert hashlib.sha256((base/name).read_bytes()).hexdigest()==h,name
    r.load_defs(a.root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(a.root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(a.previous/'grid-b64.npz');A,B,Q,G=g['A'],g['B'],g['Q'],g['G'];p=A.shape[1];c=Grouped(z,A,B,np.ones((1,1)));s=FineStream(G,A,B,8*a.blocks);De=direct(G[:,:1,None,None],A,B);D=c.D+De;L=D[p:,p:];fac=lu_factor(L);T=D[p:,:p];print('fine system',L.shape,np.linalg.cond(L),'imag ratio',s.imag_ratio,flush=True)
    rows=[]
    for kind in a.kinds:
        old=np.load(a.previous/(kind+'-signals.npz'));V=old['flow'][:a.blocks];assert len(V)==a.blocks;flow=(Q@V).reshape(-1,369);top=flow[:,:p]
        d3,m3=run(c,s,fac,T,top,flow);ref,m8=run(c,s,fac,T,top)
        project=lambda x: Q.T@x.reshape(a.blocks,8,-1)
        checks=dict(archived_exterior=rel(project(d3['exterior']),old['exterior'][:a.blocks]),archived_load=rel(project(d3['load']),old['load'][:a.blocks]),d3_projected_res=float(np.linalg.norm(project(d3['residual']))/max(np.linalg.norm(d3['inside'][:,p:])+np.linalg.norm(d3['exterior'][:,p:]),1e-300)))
        assert max(checks.values())<1e-10,checks
        assert max(m3['energy'],m3['work_final'],m8['energy'],m8['work_max_fine_prefix'],m8['fine_res'])<1e-10,(m3,m8)
        assert min(m8['min_work'])>=-1e-10,m8
        row=dict(kind=kind,blocks=a.blocks,d3=m3,d8=m8,checks=checks,opening_error=rel(d3['flow'][:,p:],ref['flow'][:,p:]),load_fine_error=rel(d3['load'],ref['load']),load_projected_error=rel(project(d3['load']),project(ref['load'])),exterior_error=rel(d3['exterior'],ref['exterior']))
        rows.append(row);print(json.dumps(row),flush=True);(out/'results.json').write_text(json.dumps(dict(condition=float(np.linalg.cond(L)),kernel_imag_ratio=s.imag_ratio,rows=rows),indent=2));np.savez_compressed(out/(kind+'-fine-signals.npz'),**{'d3_'+k:v for k,v in d3.items()},**{'d8_'+k:v for k,v in ref.items()})
if __name__=='__main__':main()
