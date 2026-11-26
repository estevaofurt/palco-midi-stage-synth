"""G3.14d.12: zero-added-delay partitioned acoustic history.
The instantaneous W[0] remains in the mechanical implicit solve.
Synthetic kernels only; no whole-engine realtime or physical approval."""
import argparse,json,time
from pathlib import Path
import numpy as np
from scipy.fft import rfft,irfft
from acoustic_cq_pilot import convolve
from split_radiation import relative

class PartitionedMemory:
    def __init__(self,W,block):
        W=np.asarray(W,dtype=np.float64)
        if W.ndim!=3 or W.shape[1]!=W.shape[2] or not len(W) or not np.isfinite(W).all():raise ValueError('kernel')
        if type(block)!=int or block<2:raise ValueError('block')
        self.B=block;self.m=W.shape[1];self.instant=W[0].copy()
        self.direct=np.zeros((block-1,self.m,self.m))
        n=min(len(W)-1,block-1);self.direct[:n]=W[1:n+1]
        self.recent=np.zeros((block-1,self.m))
        self.parts=max(0,(len(W)-1)//block)
        H=np.zeros((self.parts,2*block,self.m,self.m))
        for j in range(self.parts):
            a=(j+1)*block;v=W[a:a+block];H[j,:len(v)]=v
        self.H=rfft(H,axis=1) if self.parts else np.zeros((0,block+1,self.m,self.m),complex)
        self.X=np.zeros((self.parts,block+1,self.m),complex)
        self.input=np.zeros((block,self.m));self.tail=self.input.copy();self.overlap=self.input.copy()
        self.pos=0;self.number=0;self.order=np.arange(self.parts)
    def past(self):
        # Includes all delays >=1, not the instantaneous coefficient.
        return self.tail[self.pos]+np.einsum('kij,kj->i',self.direct,self.recent)
    def push(self,y):
        y=np.asarray(y,dtype=float)
        if y.shape!=(self.m,) or not np.isfinite(y).all():raise ValueError('velocity')
        self.recent[1:]=self.recent[:-1].copy();self.recent[0]=y
        self.input[self.pos]=y;self.pos+=1
        if self.pos==self.B:
            if self.parts:
                b=self.number;self.X[b%self.parts]=rfft(self.input,n=2*self.B,axis=0)
                # For output block b+1, partition j=1 uses input block b.
                # The second half of each linear convolution is saved for b+2.
                X=self.X[(b-self.order)%self.parts]
                Z=np.einsum('pfij,pfj->fi',self.H,X)
                out=irfft(Z,n=2*self.B,axis=0)
                self.tail[:]=out[:self.B]+self.overlap
                self.overlap[:]=out[self.B:]
            self.pos=0;self.number+=1
    def process(self,V):
        V=np.asarray(V,float);out=np.empty_like(V)
        for j,y in enumerate(V):
            out[j]=self.instant@y+self.past();self.push(y)
        return out

def synthetic(m,taps):
    rng=np.random.default_rng(635)
    W=rng.normal(size=(taps,m,m));W=(W+W.transpose(0,2,1))/2
    W*=np.exp(-np.arange(taps)/max(1,taps/8))[:,None,None]/(m*np.sqrt(taps))
    # General finite kernel for numerical/performance testing, not passivity.
    return W

def verify(m,taps,B):
    W=synthetic(m,taps);rng=np.random.default_rng(113);v=rng.normal(size=(3*taps+17,m))
    v[-taps:]=0
    a=PartitionedMemory(W,B);g=a.process(v);ref=convolve(W,v)
    b=PartitionedMemory(W,B);out=np.concatenate([b.process(v[i:i+13]) for i in range(0,len(v),13)])
    err=relative(g,ref);partition=bool(np.array_equal(g,out))
    return dict(rank=m,taps=taps,block=B,relative=err,partitionBitwise=partition,gate=bool(err<=1e-10 and partition))

def benchmark(m,taps,B,rate):
    W=synthetic(m,taps);a=PartitionedMemory(W,B);rng=np.random.default_rng(14)
    v=rng.normal(size=(B,m));g=np.empty_like(v)
    # Populate complete history, excluding initial allocation/warm-up.
    for _ in range(a.parts+2):a.process(v)
    times=[];peak=0.;ordinary=[];boundary=[]
    for _ in range(16):
        start=time.perf_counter_ns()
        for j,y in enumerate(v):
            t=time.perf_counter_ns();g[j]=a.instant@y+a.past();a.push(y)
            elapsed=(time.perf_counter_ns()-t)/1000
            (boundary if j==B-1 else ordinary).append(elapsed)
        times.append((time.perf_counter_ns()-start)/1000)
        peak=max(peak,float(np.max(abs(g))))
    budget=B*1e6/rate
    return dict(rank=m,taps=taps,block=B,rate=rate,medianUsPerSample=float(np.median(times)/B),
        p99BlockBudgetFraction=float(np.percentile(times,99)/budget),blockOverruns=int(np.count_nonzero(np.array(times)>budget)),
        medianOrdinaryUs=float(np.median(ordinary)),p99BoundaryUs=float(np.percentile(boundary,99)),
        kernelBytes=int(a.H.nbytes+a.direct.nbytes+a.instant.nbytes),finite=bool(np.isfinite(peak)),
        syntheticOnly=True,includesMechanicalSolve=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--rate',type=int,choices=(48000,96000),required=True);a=p.parse_args()
    proofs=[verify(m,t,B) for m,t,B in ((1,1,8),(3,7,8),(4,37,8),(4,64,16),(8,129,32),(16,257,64))]
    if not all(v['gate'] for v in proofs):raise ValueError('partition proof')
    rows=[];taps=1024 if a.rate==48000 else 2048
    for m in (4,32,64,80):
        for B in (16,64,128):
            row=benchmark(m,taps,B,a.rate);rows.append(row)
            print('G3_PARTITIONED_MEMORY_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=all(v['finite'] for v in rows),diagnosticOnly=True,rate=a.rate,proofCases=len(proofs),
        benchmarkCases=len(rows),zeroAddedAlgorithmicDelay=True,instantaneousImplicitTermSeparated=True,
        physicalKernelValidated=False,wholeEngineRealtimeValidated=False,polyphonyValidated=False,
        noParameterSelection=True)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'partitioned_acoustic_memory.json').write_text(json.dumps(dict(summary=summary,proofs=proofs,cases=rows),indent=2,allow_nan=False))
    print('G3_PARTITIONED_MEMORY_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
