"""Audit mechanical fixture pressure and independent fine aperture solution; no audio."""
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import lu_factor
from scipy.fft import rfft, irfft, next_fast_len
from scipy.signal import firwin, kaiserord, upfirdn
import replay as r
from coupled369 import Grouped,direct
from fine369 import FineStream,run
from spatial import rel
from bridge import scales

def verify(root, manifest):
    n=0
    for line in manifest.read_text().splitlines():
        h,f=line.split(maxsplit=1); assert hashlib.file_digest((root/f).open('rb'),'sha256').hexdigest()==h,f;n+=1
    return n

def pressure(H,U):
    N=len(H)+len(U)-1;n=next_fast_len(N)
    return irfft(np.einsum('fkp,fp->fk',rfft(H,n=n,axis=0),rfft(U,n=n,axis=0)),n=n,axis=0)[:N]

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('prior',type=Path);p.add_argument('mechanical',type=Path);p.add_argument('observer',type=Path);a=p.parse_args();out=Path(__file__).parent
    n=verify(a.root,out/'INPUT_SHA256SUMS')+sum(verify(x,x/'SHA256SUMS') for x in (a.prior,a.mechanical,a.observer));print('verified',n,flush=True)
    r.load_defs(a.root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);r.load_defs(a.root,'G3_Acoplamento_Multirate/multirate.py',['basis']);z=np.load(a.root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(a.prior/'grid-b64.npz');A,B,G=g['A'],g['B'],g['G'];H=np.load(a.observer/'receiver369.npz')['H'];arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)]
    c=Grouped(z,A,B,np.ones((1,1)));s=FineStream(G,A,B,512);D=c.D+direct(G[:,:1,None,None],A,B);fac=lu_factor(D[80:,80:]);T=D[80:,:80];Q={d:r.basis(8,d) for d in (3,7,8)};scale=scales(z,g);rng=np.random.default_rng(271135);V,_=np.linalg.qr(rng.normal(size=(80,8)));S=scale[:,None]*V
    nt,beta=kaiserord(100,4000/192000);nt+=1-nt%2;filt=firwin(nt,22000,window=('kaiser',beta),fs=384000)
    rows=[]
    for kind in ('noise','pulse','high'):
        files={d:np.load((out if d==8 else a.mechanical)/f'd{d}-{kind}.npz') for d in Q};flow={d:(Q[d]@v['flow']).reshape(-1,369) for d,v in files.items()};u=flow[8];fine,m=run(c,s,fac,T,u[:,:80]);load=(fine['load'].reshape(64,8,80).mean(axis=1))@S
        checks=dict(fine_lower_flow=rel(fine['flow'][:,80:],u[:,80:]),fine_mechanical_load=rel(load,files[8]['load']),fine_continuity=m['fine_res'],fine_energy=m['energy'],fine_work=m['work_max_fine_prefix'],min_work=min(m['min_work']));assert max(checks[k] for k in checks if k!='min_work')<1e-10 and checks['min_work']>=-1e-10,checks
        P={d:pressure(H,v) for d,v in flow.items()};R=P[8];Y={d:upfirdn(filt,v,down=8,axis=0) for d,v in P.items()};direct_err=[];causal=[]
        for d in Q:
            times=[600,1000,1800,2400];calc=[]
            for t in times:
                ix=np.arange(max(0,t-len(H)+1),min(t+1,len(u)));calc.append(np.einsum('tkp,tp->k',H[t-ix],flow[d][ix]))
            direct_err.append(rel(P[d][times],np.array(calc)));causal.append(max(np.max(abs(P[d][:arrivals[i],i]))/max(np.max(abs(P[d][:,i])),1e-300) for i in range(2)))
        assert max(direct_err+causal)<1e-10
        comparison=[]
        for d in (3,7):
            row=dict(d=d,velocity=rel(files[d]['velocity'],files[8]['velocity']),load=rel(files[d]['load'],files[8]['load']),lower_flow=rel(flow[d][:,80:],u[:,80:]),pressure=rel(P[d],R),pressure_mics=[rel(P[d][:,i],R[:,i]) for i in range(2)],filtered_pressure=rel(Y[d],Y[8]),filtered_mics=[rel(Y[d][:,i],Y[8][:,i]) for i in range(2)]);comparison.append(row)
        row=dict(kind=kind,checks=checks,direct_pressure_error=max(direct_err),prearrival_leakage=max(causal),comparison=comparison);rows.append(row);print(json.dumps(row),flush=True);np.savez_compressed(out/f'{kind}-pressure.npz',**{f'd{d}':P[d] for d in Q},**{f'd{d}_filtered':Y[d] for d in Q});(out/'audit-results.json').write_text(json.dumps(dict(verified=n,arrivals=arrivals,blocks=64,fine_steps=512,pressure_samples=len(R),filter_taps=nt,rows=rows),indent=2))
if __name__=='__main__':main()
