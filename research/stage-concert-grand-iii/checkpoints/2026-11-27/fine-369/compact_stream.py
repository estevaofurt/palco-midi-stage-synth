"""Real spatial spectrum, circular history without advanced-index copies."""
import argparse,json,time
from pathlib import Path
import numpy as np
from causal import SpatialStream
from numba import njit
@njit
def accumulate(y,f,x):
    for l in range(x.shape[0]):
        for a in range(y.shape[1]):
            for b in range(y.shape[1]):
                for i in range(y.shape[2]):
                    for j in range(y.shape[3]):
                        v0=x[l,0,b,i,j];v1=x[l,1,b,i,j]
                        k0=f[0,l,a,b,i,j];k1=f[1,l,a,b,i,j]
                        y[0,a,i,j]+=k0*v0+k1*v1
                        y[1,a,i,j]+=k0*v1+k1*v0
from spatial import temporal_grid,rel
class CompactStream(SpatialStream):
    def __init__(self,K,A,B):
        super().__init__(K,A,B)
        self.imag_ratio=float(np.max(abs(self.F.imag))/max(np.max(abs(self.F.real)),1e-300))
        if self.imag_ratio>=1e-13:raise ValueError('kernel not spatially even')
        self.F=self.F.real.copy()
    def history_spec(self):
        n=min(self.t,self.L-1);y=np.zeros_like(self.X[0]);end=self.t%self.L;first=min(n,end)
        for j,count,x in [(0,first,self.X[end-first:end][::-1]),(first,n-first,self.X[self.L-(n-first):][::-1])]:
            if not count:continue
            f=self.F[:,1+j:1+j+count]
            accumulate(y,f,x)
        return y

def main():
    p=argparse.ArgumentParser();p.add_argument('previous',type=Path);a=p.parse_args();z=np.load(a.previous/'grid-b64.npz');K=temporal_grid(z['G'],z['Q']);A,B=z['A'],z['B'];u0=np.load(a.previous/'noise-signals.npz')['flow'];u=u0;rows={};ys={}
    for name,cls in [('original',SpatialStream),('compact',CompactStream)]:
        s=cls(K,A,B);y=[];s.step(u[0]);s.step(u[1]);s.reset();t=time.perf_counter();times=[]
        for x in u:
            t0=time.perf_counter();y.append(s.step(x));times.append(time.perf_counter()-t0)
        y=np.array(y);ys[name]=y;rows[name]=dict(seconds=time.perf_counter()-t,mean_us=float(np.mean(times)*1e6),full_history_mean_us=float(np.mean(times[s.L:])*1e6),kernel_bytes=s.F.nbytes,history_bytes=s.X.nbytes,archived_error=rel(y[:len(u0)],np.load(a.previous/'noise-signals.npz')['exterior']),blocks=len(u),lags=s.L)
        if name=='compact':rows[name]['imag_ratio']=s.imag_ratio
        print(name,rows[name],flush=True);del s
    error=rel(ys['compact'],ys['original']);assert error<1e-10 and max(x['archived_error'] for x in rows.values())<1e-10
    data=dict(rows=rows,relative_error=error,post_wrap_error=rel(ys['compact'][301:],ys['original'][301:]));print(data,flush=True);Path(__file__).with_name('compact-results.json').write_text(json.dumps(data,indent=2))
if __name__=='__main__':main()
