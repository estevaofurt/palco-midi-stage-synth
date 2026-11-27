"""Audit flushed 50ms prefixes while long runs advance. Does not assume future
flow zero or interpret an incomplete run as a completed 250 ms simulation."""
import json, argparse, numpy as np
from audit_250ms import ROOT, FS, pressure, audit_pressure, rel, spectral, quadratic
from regional_compact import assemble_regional
from assembly_rank import SPREAD
from dynamic_dampers import Dampers
from scipy.signal import kaiserord,firwin,upfirdn
p=argparse.ArgumentParser();p.add_argument('--ms',type=int,choices=[50,100,150,200,250],required=True);args=p.parse_args();N=args.ms*384
H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz',allow_pickle=False)['H']; nt,beta=kaiserord(100,4000/192000);nt+=1-nt%2; filt=firwin(nt,22000,window=('kaiser',beta),fs=FS)
P={};Y={};rows={}
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz',allow_pickle=False)
for rank in ('mixed','uniform'):
    folder=ROOT/f'long-250ms-refined-384000-{rank}-pedal';progress=json.loads((folder/'progress.json').read_text());assert progress['steps']>=N
    z={k:np.load(folder/(k+'.npy'),mmap_mode='r',allow_pickle=False)[:N] for k in ('velocity','flow','ledger','force','compression')};u=z['flow'].reshape(N,369);L=z['ledger'];v=z['velocity']
    ranks={33:64,45:64,48:128,55:64,60:64,64:64,72:64};ranks={k:128 for k in ranks} if rank=='uniform' else ranks;spread={k:SPREAD.get(k,0.) for k in ranks};shift={k:5.5 if k==48 else 0. for k in ranks};M,K,D,ports,w=assemble_regional(base,scale,list(ranks),ranks,spread,shift);dam=Dampers(D,w,scale)
    schedule=[(5,[48],1),(15,[48,60],1),(30,[48,60,64],1),(40,[60,64],1),(55,[48,60,64],1),(65,[48,64],1),(70,[48],1),(75,[48],0),(85,[],0),(105,[],1),(120,[60],1),(145,[],1),(160,[64],1),(185,[],1),(200,[],0)]
    frac=np.tile(dam.fractions([48],0),(N,1))
    for ms,held,pedal in schedule:
        if ms<args.ms:frac[ms*384:]=dam.fractions(held,pedal)
    prev_v=np.zeros(M.n);prev_q=np.zeros(M.n);carry=energyerr=losserr=0.;E=float(L[-1,10]);assert E>0
    for i in range(0,N,1200):
        j=min(N,i+1200);vv=np.asarray(v[i:j]);assert np.isfinite(vv).all() and np.isfinite(u[i:j]).all();mid=(vv+np.vstack((prev_v,vv[:-1])))/2;q=prev_q+np.cumsum(mid/FS,axis=0);prev_v=vv[-1].copy();prev_q=q[-1].copy();em=.5*(quadratic(M,vv)+quadratic(K,q));energyerr=max(energyerr,float(np.max(abs(em-L[i:j,0]))/E));d=.18*(mid[:,:80]@D.g.T)
        for k in range(len(w)):
            ix=D.ids==k;d[:,k]+=mid[:,80:][:,ix]@D.v[ix]
        loss=quadratic(D,mid)/FS+np.sum(d*d*frac[i:j]*dam.maximum/FS,axis=1);cum=carry+np.cumsum(loss);carry=float(cum[-1]);losserr=max(losserr,float(np.max(abs(cum-L[i:j,2]))/E))
    err=float(np.max(abs(L[:,7]+L[:,2:7].sum(1)-L[:,10]))/E);assert max(energyerr,losserr)<1e-10 and err<1e-8 and np.min(L[:,4])/E>=-1e-10
    assert np.isfinite(z['force']).all() and z['force'].min()>=0 and np.isfinite(z['compression']).all()
    P[rank]=pressure(H,u); Y[rank]=upfirdn(filt,P[rank],down=8,axis=0);checks=audit_pressure(H,u,P[rank]); rows[rank]=dict(steps=N,coordinates=M.n,energy_reconstruction=energyerr,loss_reconstruction=losserr,ledger_balance=err,final_mechanical=float(L[-1,0]),final_cavity=float(L[-1,1]),injected=E,**checks)
    print(rank,json.dumps(rows[rank]),flush=True)
comparison=dict(causal_fine=[rel(P['mixed'][:N,i],P['uniform'][:N,i]) for i in range(2)],causal_filtered=[rel(Y['mixed'][:N//8,i],Y['uniform'][:N//8,i]) for i in range(2)],spectral=[spectral(Y['mixed'][:N//8,i],Y['uniform'][:N//8,i]) for i in range(2)])
comparison['causal_gate']=max(comparison['causal_fine'])<=.01 and all(x['gate'] for x in comparison['spectral'])
out=dict(duration_ms=args.ms,cases=rows,comparison=comparison,scope='Flushed causal prefix; no claim of full 250 ms, no post-window gate on unfinished runs.')
(ROOT/f'long-prefix-{args.ms}ms.json').write_text(json.dumps(out,indent=2,allow_nan=False));print(json.dumps(out),flush=True)
