"""Independent streamed checks for the physical 500 ms experiment.
No changes to physical coefficients. Bounded-memory pressure convolution and
mechanical energy reconstruction, all completed steps only. No audio render.
"""
from pathlib import Path
import argparse, hashlib, json, numpy as np
from scipy.fft import rfft, irfft, next_fast_len
from scipy.signal import firwin, kaiserord, upfirdn
from regional_compact import assemble_regional
from dynamic_dampers import Dampers
from pressure_refine import rel, spectral
ROOT=Path(__file__).resolve().parent
FS=384000; KEYS=(33,45,48,55,60,64,72); UNSTRUCK=(33,45,55,72)

def quadratic(op,x):
    # Independent block expression of x^T A x; no use of integrator solver.
    b=x[:,:80]; y=x[:,80:]; g=b@op.g.T
    e=np.einsum('ti,ti->t',b@op.board,b)+np.sum(y*y*op.d,axis=1)
    for j in range(len(op.a)):
        mask=op.ids==j; z=y[:,mask]
        e+=2*g[:,j]*(z@op.c[mask])+op.a[j]*(z@op.v[mask])**2
    return e

def load_case(name):
    row=json.loads((ROOT/(name+'.json')).read_text()); folder=ROOT/name
    prog=json.loads((folder/'progress.json').read_text())
    N=row['blocks']; assert prog['steps']==N and not any(prog['active_hammers'])
    z={k:np.load(folder/(k+'.npy'),mmap_mode='r',allow_pickle=False) for k in ('force','compression','velocity','flow','ledger')}
    rank={int(k):v for k,v in row['ranks'].items()};spread={int(k):v for k,v in row['spread'].items()};shift={int(k):v for k,v in row['shift'].items()}
    assert tuple(rank)==KEYS and row['rate']==FS and row['coordinates']==z['velocity'].shape[1]
    scale=json.loads((ROOT/'scale_geometry.json').read_text()); base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz',allow_pickle=False)
    M,K,D,P,w=assemble_regional(base,scale,list(rank),rank,spread,shift); dam=Dampers(D,w,scale)
    v=z['velocity']; ledger=z['ledger']; F=z['force']; C=z['compression']; flow=z['flow'].reshape(N,369)
    assert len(F)==len(C)==len(v)==len(ledger)==len(flow)==N and M.n==row['coordinates']
    assert len(row['launches'])==len(row['captures']) and all(x['step']>0 for x in row['captures'])
    cap={x['id']:x for x in row['captures']}; launches=row['launches']; injected=np.zeros(N); active={k:np.zeros(N,dtype=bool) for k in (48,60,64)}
    for x in launches:
        assert cap[x['id']]['key']==x['key'] and cap[x['id']]['step']>x['step']
        assert not np.any(active[x['key']][x['step']:cap[x['id']]['step']]);active[x['key']][x['step']:cap[x['id']]['step']]=True
        injected[x['step']:]+=x['energy']
    assert np.array_equal(injected,ledger[:,10]); assert np.isfinite(F).all() and F.min()>=0 and np.isfinite(C).all()
    for k,sl in {48:slice(0,2),60:slice(2,5),64:slice(5,8)}.items():assert not np.any(F[~active[k],sl])
    # Reconstruct exact midpoint displacement and damping energy, in chunks.
    frac=np.tile(dam.fractions([48],0),(N,1))
    if row['control']=='closed':frac[:,np.isin(dam.keys,[33,55,72])]=1
    for ev in row['events']:frac[ev['step']:]=ev['after']
    previous_v=np.zeros(M.n); previous_q=np.zeros(M.n);loss_carry=0.;energy_err=loss_err=0.; Eref=row['injected_energy']; maxp={str(k):0. for k in UNSTRUCK}; finals={}; boundaries=np.arange(0,N+1,19200); assert boundaries[-1]==N
    windows={str(k):np.zeros(len(boundaries)-1) for k in UNSTRUCK};counts={str(k):np.zeros(len(boundaries)-1,dtype=int) for k in UNSTRUCK}; damper_loss={str(k):0. for k in UNSTRUCK}; cuts=[]
    for i in range(0,N,1200):
        j=min(i+1200,N); vv=np.asarray(v[i:j]); assert np.isfinite(vv).all() and np.isfinite(flow[i:j]).all()
        mid=(vv+np.vstack((previous_v,vv[:-1])))/2; q=previous_q+np.cumsum(mid/FS,axis=0);previous_v=vv[-1].copy();previous_q=q[-1].copy()
        energy=(quadratic(M,vv)+quadratic(K,q))*.5; energy_err=max(energy_err,float(np.max(abs(energy-ledger[i:j,0]))/Eref))
        d=.18*(mid[:,:80]@D.g.T)
        for u in range(len(w)):
            ix=D.ids==u;d[:,u]+=mid[:,80:][:,ix]@D.v[ix]
        per_wire=d*d*frac[i:j]*dam.maximum/FS;loss=quadratic(D,mid)/FS+per_wire.sum(1); cumulative=loss_carry+np.cumsum(loss);loss_carry=float(cumulative[-1]);loss_err=max(loss_err,float(np.max(abs(cumulative-ledger[i:j,2]))/Eref))
        win=i//19200
        for k in UNSTRUCK:
            key=str(k);ma=dam.keys==k;ix=ma[M.ids]; vel=vv@P[:,ma];p=.5*np.sum(vv[:,80:][:,ix]**2+K.d[ix]*q[:,80:][:,ix]**2,axis=1)
            maxp[key]=max(maxp[key],float(p.max()));finals[key]=float(p[-1]);windows[key][win]+=np.sum(vel**2);counts[key][win]+=vel.size;damper_loss[key]+=float(per_wire[:,ma].sum())
        if j%19200==0:cuts.append(dict(ms=j/FS*1000,energy_mechanical=float(ledger[j-1,0]),energy_cavity=float(ledger[j-1,1]),injection=float(ledger[j-1,10]),balance=float(ledger[j-1,8])))
    balance=float(np.max(abs(ledger[:,7]+ledger[:,2:7].sum(1)-ledger[:,10]))/Eref)
    assert max(energy_err,loss_err)<1e-10 and balance<1e-8 and row['continuity']<1e-10 and np.min(ledger[:,4])/Eref>=-1e-10
    assert row['energy_error']<1e-8 and row['compression_residual']<1e-12 and row['work_error']<1e-8
    notes={str(k):dict(rms_50ms_windows=np.sqrt(windows[str(k)]/counts[str(k)]).tolist(),participation_max=maxp[str(k)],participation_final=finals[str(k)],damper_loss=damper_loss[str(k)]) for k in UNSTRUCK}
    # A prefix may end before the last scheduled pedal release.
    timeline=[(5,[48],1),(15,[48,60],1),(30,[48,60,64],1),(40,[60,64],1),(55,[48,60,64],1),(65,[48,64],1),(70,[48],1),(75,[48],0),(85,[],0),(105,[],1),(120,[60],1),(145,[],1),(160,[64],1),(185,[],1),(200,[],0)]
    expected_events=[(ms*384,held,ped) for ms,held,ped in timeline if ms*384<N]
    assert [(x['step'],x['held'],x['pedal']) for x in row['events']]==expected_events
    expected_launches=[(ms*384,k,s) for ms,k,s in [(0,48,.3),(15,60,1.),(30,64,3.),(55,48,1.),(120,60,.7),(160,64,.5)] if ms*384<N]
    assert [(x['step'],x['key'],x['speed']) for x in launches]==expected_launches
    for x in row['events']:
        exp=dam.fractions(x['held'],x['pedal'])
        if row['control']=='closed':exp[np.isin(dam.keys,[33,55,72])]=1
        assert np.array_equal(exp,x['after'])
    all_closed=bool(np.all(frac[-1]==1))
    if N in (38400,96000,192000):assert all_closed
    info=dict(rate=FS,steps=N,coordinates=M.n,energy_error=row['energy_error'],continuity=row['continuity'],work_error=row['work_error'],minimum_exterior_work=row['minimum_exterior_work'],compression_residual=row['compression_residual'],seconds=row['seconds'],captures=row['captures'],launches=launches,energy_reconstruction=energy_err,loss_reconstruction=loss_err,ledger_balance=balance,final_mechanical=row['final_mechanical_energy'],final_cavity=row['final_cavity_energy'],notes=notes,energy_checkpoints=cuts,final_dampers_closed=all_closed)
    if N==192000:
        end=200*384
        assert np.all(ledger[end:,10]==ledger[end-1,10]) and np.all(F[end:]==0)
        assert np.all(frac[end:]==1)
        info['tail_after_200ms']=dict(no_injection=True,no_hammer_force=True,all_dampers_closed=True,final_mechanical=float(ledger[-1,0]),final_cavity=float(ledger[-1,1]))
    print('MECHANICAL',name,json.dumps(info),flush=True);return row,info,flow

def pressure(H,u):
    N=len(u);L=next_fast_len(N+len(H)-1); acc=np.zeros((L//2+1,2),complex)
    # FFT linear convolution over all ports, summed in fixed order by small tiles.
    for i in range(0,u.shape[1],12):
        j=min(i+12,u.shape[1]); hh=rfft(H[:,:,i:j],n=L,axis=0);uu=rfft(u[:,i:j],n=L,axis=0)
        acc+=np.einsum('fkp,fp->fk',hh,uu)
    return irfft(acc,n=L,axis=0)[:N+len(H)-1]

def audit_pressure(H,u,p):
    N=len(u); arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)];direct=[]
    for t in [600,1800,4607,*range(19199,N,19200),N+100]:
        ix=np.arange(max(0,t-len(H)+1),min(t+1,N));direct.append(float(np.linalg.norm(p[t]-np.einsum('tkp,tp->k',H[t-ix],u[ix]))/max(np.linalg.norm(p),1e-300)))
    pre=max(float(np.max(abs(p[:a,i]))/np.max(abs(p[:,i]))) for i,a in enumerate(arrivals));assert max(direct+[pre])<1e-10
    return dict(direct=max(direct),prearrival=pre,arrivals=arrivals)

def main():
    pa=argparse.ArgumentParser();pa.add_argument('--ms',type=int,choices=[500],default=500);a=pa.parse_args();N=round(a.ms*FS/1000)
    names=[f'long-{a.ms}ms-refined-384000-{r}-pedal' for r in ('mixed','uniform')]
    H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz',allow_pickle=False)['H'];nt,beta=kaiserord(100,4000/192000);nt+=1-nt%2;filt=firwin(nt,22000,window=('kaiser',beta),fs=FS)
    rows={};md={};press={};filtered={}
    for name in names:
        row,info,u=load_case(name);assert len(u)==N;md[name]=row;p=pressure(H,u);y=upfirdn(filt,p,down=8,axis=0)
        info.update(audit_pressure(H,u,p));prefix=rel(upfirdn(filt,p[:N],down=8,axis=0)[:N//8],y[:N//8]);assert prefix<1e-10;info['filter_prefix']=prefix;rows[name]=info;press[name]=p;filtered[name]=y;print('ACOUSTIC',name,info['direct'],info['prearrival'],flush=True)
        # Save independent per-case report immediately, before comparison.
        (ROOT/(name+'-audit.json')).write_text(json.dumps(info,indent=2,allow_nan=False))
    a,b=names;assert [(x['step'],x['key'],x['speed']) for x in md[a]['launches']]==[(x['step'],x['key'],x['speed']) for x in md[b]['launches']];assert [e['after'] for e in md[a]['events']]==[e['after'] for e in md[b]['events']]
    def compare(n):
        return dict(duration_ms=n/FS*1000,causal_fine=[rel(press[a][:n,i],press[b][:n,i]) for i in range(2)],causal_filtered=[rel(filtered[a][:n//8,i],filtered[b][:n//8,i]) for i in range(2)],spectral=[spectral(filtered[a][:n//8,i],filtered[b][:n//8,i]) for i in range(2)])
    comparisons=[compare(n) for n in range(19200,N+1,19200)]
    for v in comparisons:v['causal_gate']=max(v['causal_fine'])<=.01 and all(s['gate'] for s in v['spectral'])
    full=[rel(press[a][:,i],press[b][:,i]) for i in range(2)];gate=bool(all(v['causal_gate'] for v in comparisons) and max(full)<=.01)
    out=dict(cases=rows,comparisons=comparisons,full_finite=full,final_gate=gate,all_prefix_gates=all(v['causal_gate'] for v in comparisons),peak_force_relative=(abs(np.array(md[a]['peak_force'])/md[b]['peak_force']-1)).tolist(),impulse_relative=(abs(np.array(md[a]['impulse'])/md[b]['impulse']-1)).tolist(),filter_taps=nt,scope='Seven-note regional model, 384 kHz, candidate coefficients; finite post-window assumes zero flow; reference uniform 128 is not spatial continuum; no audio render.')
    (ROOT/f'long-{N//384}ms-audit.json').write_text(json.dumps(out,indent=2,allow_nan=False));np.savez_compressed(ROOT/f'long-{N//384}ms-pressure.npz',**{k+'-fine':v for k,v in press.items()},**{k+'-filtered':v for k,v in filtered.items()});print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
