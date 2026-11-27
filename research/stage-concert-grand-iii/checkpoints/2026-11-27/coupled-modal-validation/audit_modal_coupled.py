"""Compare candidate with historical signals and separate rank/rate errors.
Keep numerical coefficient gate 1e-10; regional discretization uses historical
1% fine-pressure, 1 dB global, 3 dB significant-band gates.
"""
from pressure_refine import rel,spectral,FS,ROOT,r
from scipy.fft import rfft,irfft,next_fast_len
from scipy.signal import firwin,kaiserord,upfirdn
from regional_compact import assemble_regional
from dynamic_dampers import Dampers
import hashlib,json,numpy as np
N=6912;root=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis']);H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz')['H'];L=next_fast_len(N+len(H)-1);HH=rfft(H,n=L,axis=0);arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)]
nt,beta=kaiserord(100,4000/192000);nt+=1-nt%2;filt=firwin(nt,22000,window=('kaiser',beta),fs=FS)
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(root/'G3_Base_Estrutural/integrated_80.npz');signals={};rows={};press={};audio={};flows={};metadata={}
for line in (ROOT/'REFERENCE_REGIONAL.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1);assert hashlib.file_digest((ROOT/n).open('rb'),'sha256').hexdigest()==h,n
names=['regional-pedal','regional-added-closed','refined-384000-mixed-pedal','refined-384000-mixed-closed','refined-384000-uniform-pedal','refined-192000-mixed-pedal']
for name in names:
    row=json.loads((ROOT/f'{name}.json').read_text());metadata[name]=row;rate=row['rate'];m=FS//rate;n=N//m;rank={int(k):v for k,v in row['ranks'].items()};spread={int(k):v for k,v in row['spread'].items()};shift={int(k):v for k,v in row['shift'].items()};M,K,D,P,w=assemble_regional(base,scale,list(rank),rank,spread,shift);dam=Dampers(D,w,scale);assert M.n==row['coordinates']
    with np.load(ROOT/f'{name}.npz') as z:
        S={k:z[k] for k in ('force','compression','velocity','flow','ledger')};v=S['velocity'];ledger=S['ledger'];F=S['force'];assert all(np.isfinite(x).all() for x in S.values());assert F.min()>=0
        for key,sl in {48:slice(0,2),60:slice(2,5),64:slice(5,8)}.items():
            i=next(a['step'] for a in row['launches'] if a['key']==key);j=next(a['step'] for a in row['captures'] if a['key']==key);assert not np.any(F[:i,sl]) and not np.any(F[j:,sl])
        mid=(v+np.vstack((np.zeros((1,M.n)),v[:-1])))/2;q=np.cumsum(mid,axis=0)/rate;frac=np.tile(dam.fractions([48],0),(n,1));closed=name.endswith('closed');frac[:,np.isin(dam.keys,[33,55,72])]=1 if closed else frac[:,np.isin(dam.keys,[33,55,72])]
        for ev in row['events']:frac[ev['step']:]=ev['after']
        d=.18*(mid[:,:80]@D.g.T)
        for j in range(len(w)):
            ix=D.ids==j;d[:,j]+=mid[:,80:][:,ix]@D.v[ix]
        loss=d*d*frac*dam.maximum/rate;base_loss=np.array([x@(D@x)/rate for x in mid]);loss_err=float(np.max(abs(np.cumsum(base_loss+loss.sum(1))-ledger[:,2]))/row['injected_energy']);mech=np.array([.5*(x@(M@x)+y@(K@y)) for x,y in zip(v,q)]);energy_err=float(np.max(abs(mech-ledger[:,0]))/row['injected_energy']);balance=float(np.max(abs(ledger[:,7]+ledger[:,2:7].sum(1)-ledger[:,10]))/row['injected_energy']);assert max(loss_err,energy_err)<1e-10 and balance<1e-8 and row['continuity']<1e-10 and np.min(ledger[:,4])/row['injected_energy']>=-1e-10
        notes={}
        for key in (33,45,55,72):
            ma=dam.keys==key;ii=ma[M.ids];vel=v@P[:,ma];p=.5*np.sum(v[:,80:][:,ii]**2+K.d[ii]*q[:,80:][:,ii]**2,axis=1);notes[str(key)]=dict(rms_15_18=float(np.sqrt(np.mean(vel[round(.015*rate):]**2))),participation_final=float(p[-1]))
        u=(r.basis(m,m)@S['flow']).reshape(N,369);p=irfft(np.einsum('fkp,fp->fk',HH,rfft(u,n=L,axis=0)),n=L,axis=0)[:N+len(H)-1];y=upfirdn(filt,p,down=8,axis=0);press[name]=p;audio[name]=y;flows[name]=u;direct=[]
        for t in (600,1800,4607,N-1,N+100):
            ix=np.arange(max(0,t-len(H)+1),min(t+1,N));direct.append(float(np.linalg.norm(p[t]-np.einsum('tkp,tp->k',H[t-ix],u[ix]))/max(np.linalg.norm(p),1e-300)))
        pre=max(float(np.max(abs(p[:a,i]))/np.max(abs(p[:,i]))) for i,a in enumerate(arrivals));prefix=rel(upfirdn(filt,p[:N],down=8,axis=0)[:N//8],y[:N//8]);assert max(direct+[pre,prefix])<1e-10
        rows[name]=dict(rate=rate,coordinates=M.n,energy_error=row['energy_error'],continuity=row['continuity'],work_error=row['work_error'],minimum_exterior_work=row['minimum_exterior_work'],compression_residual=row['compression_residual'],seconds=row['seconds'],captures=row['captures'],energy_reconstruction=energy_err,loss_reconstruction=loss_err,ledger_balance=balance,final_mechanical=row['final_mechanical_energy'],direct=max(direct),prearrival=pre,filter_prefix=prefix,notes=notes)
        if m==1 and M.n==1360:signals[name]=S
    print('AUDITED',name,flush=True)
comparisons=[]
for a,b,kind in [('refined-384000-mixed-pedal','regional-pedal','coefficient'),('refined-384000-mixed-closed','regional-added-closed','coefficient'),('refined-384000-mixed-pedal','refined-384000-uniform-pedal','rank'),('refined-192000-mixed-pedal','refined-384000-mixed-pedal','rate'),('refined-192000-mixed-pedal','refined-384000-uniform-pedal','combined')]:
    rec=dict(case=a,reference=b,kind=kind,causal_fine=[rel(press[a][:N,i],press[b][:N,i]) for i in range(2)],full_finite=[rel(press[a][:,i],press[b][:,i]) for i in range(2)],causal_filtered=[rel(audio[a][:N//8,i],audio[b][:N//8,i]) for i in range(2)],spectral=[spectral(audio[a][:N//8,i],audio[b][:N//8,i]) for i in range(2)],peak_force_relative=(abs(np.array(metadata[a]['peak_force'])/metadata[b]['peak_force']-1)).tolist(),impulse_relative=(abs(np.array(metadata[a]['impulse'])/metadata[b]['impulse']-1)).tolist())
    if kind=='coefficient':
        rec['signal_relative']={k:rel(signals[a][k],signals[b][k]) for k in ('force','compression','velocity','flow','ledger')};rec['gate']=max([*rec['signal_relative'].values(),*rec['causal_fine'],*rec['full_finite'],*rec['causal_filtered']])<1e-10;rec['captures_equal']=metadata[a]['captures']==metadata[b]['captures'];rec['gate']=bool(rec['gate'] and rec['captures_equal'])
    else:rec['gate']=bool(max(rec['causal_fine']+rec['full_finite'])<=.01 and all(x['gate'] for x in rec['spectral']))
    comparisons.append(rec);print(kind,rec['causal_fine'],rec['gate'],flush=True)
a='refined-384000-mixed-pedal';b='refined-384000-mixed-closed';delta=flows[a]-flows[b];first=int(np.flatnonzero(np.any(delta!=0,axis=1))[0]);assert first>=960
p=irfft(np.einsum('fkp,fp->fk',HH,rfft(delta,n=L,axis=0)),n=L,axis=0)[:N+len(H)-1];causal=[float(np.max(abs(p[:first+r,i]))/np.max(abs(p[:,i]))) for i,r in enumerate(arrivals)];match=[rel(press[a][:,i]-press[b][:,i],p[:,i]) for i in range(2)];assert max(causal+match)<1e-10
out=dict(cases=rows,comparisons=comparisons,refined_control=dict(first_delta=first,causal=causal,match=match,reference_difference=[rel(press[b][:N,i],press[a][:N,i]) for i in range(2)]),filter_taps=nt,scope='18 ms, seven notes, fixed physical parameters; 192 kHz mechanical blocks with two acoustic substeps at 384 kHz. Finite post-window assumes zero flow; no audio rendering. Uniform 128 is a finite reference, not continuous convergence.')
(ROOT/'modal-coupled.json').write_text(json.dumps(out,indent=2,allow_nan=False));np.savez_compressed(ROOT/'modal-coupled-pressure.npz',**{k+'-fine':v for k,v in press.items()},**{k+'-filtered':v for k,v in audio.items()});print(json.dumps(out,indent=2),flush=True)
