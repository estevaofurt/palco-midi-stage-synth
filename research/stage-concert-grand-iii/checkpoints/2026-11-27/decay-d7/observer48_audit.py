"""Causal anti-alias audit of the pressure receiver, not a runtime output implementation."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.signal import firwin,kaiserord,freqz,upfirdn
FS=384000; RATE=48000; M=8

def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    n,beta=kaiserord(100,4000/(FS/2));n+=1-n%2;h=firwin(n,22000,window=('kaiser',beta),fs=FS);f,z=freqz(h,worN=262144,fs=FS);db=20*np.log10(np.maximum(abs(z),1e-300));spec=dict(taps=n,delay_fine_samples=(n-1)//2,delay_ms=(n-1)/2/FS*1000,passband_max_abs_db=float(np.max(abs(db[f<=20000]))),stopband_max_db=float(np.max(db[f>=24000])))
    assert spec['passband_max_abs_db']<.001 and spec['stopband_max_db']<-95,spec
    ref=np.load(a.root/'new-reference.npz');x=ref['pressure'];N=len(ref['flow']);Nout=(N+7)//8;R=upfirdn(h,x,down=8,axis=0);r0=upfirdn(h,x[:N],down=8,axis=0);assert rel(r0[:Nout],R[:Nout])<1e-13
    rows=[]
    for m in ('d6','targeted','d7'):
        x=np.load(a.root/('new-'+m+'.npz'))['pressure'];Y=upfirdn(h,x,down=8,axis=0);y0=upfirdn(h,x[:N],down=8,axis=0);assert rel(y0[:Nout],Y[:Nout])<1e-13
        d={'mode':m,'full_combined':rel(Y,R),'full_per_mic':[rel(Y[:,i],R[:,i]) for i in range(2)],'causal_prefix_combined':rel(Y[:Nout],R[:Nout]),'causal_prefix_per_mic':[rel(Y[:Nout,i],R[:Nout,i]) for i in range(2)]};rows.append(d);print(d)
    a.output.write_text(json.dumps(dict(filter=spec,causal_prefix_samples=Nout,rows=rows),indent=2));print(spec)
if __name__=='__main__':main()
