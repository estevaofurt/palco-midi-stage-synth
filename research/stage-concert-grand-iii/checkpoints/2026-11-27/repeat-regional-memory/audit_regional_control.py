"""Regional 18 ms control: three added unstruck notes jointly always damped vs pedal."""
from pathlib import Path
import json,numpy as np
from scipy.fft import rfft,irfft,next_fast_len
from regional_compact import assemble_regional
from dynamic_dampers import Dampers
from assembly_rank import SPREAD
ROOT=Path(__file__).resolve().parent;N=6912;FS=384000;RANKS={33:64,45:64,48:128,55:64,60:64,64:64,72:64};SP={k:SPREAD.get(k,0.) for k in RANKS};SHIFT={k:5.5 if k==48 else 0. for k in RANKS};ADD=[33,55,72];UNSTRUCK=[33,45,55,72]
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz');M,K,D,P,w=assemble_regional(base,scale,list(RANKS),RANKS,SP,SHIFT);dam=Dampers(D,w,scale);mask=np.isin(dam.keys,ADD)
H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz')['H'];L=next_fast_len(N+len(H)-1);HH=rfft(H,n=L,axis=0);arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)]
def pressure(U):return irfft(np.einsum('fkp,fp->fk',HH,rfft(U,n=L,axis=0)),n=L,axis=0)[:N+len(H)-1]
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-300))
rows={};signals={};frac={};press={}
for case in ('regional-pedal','regional-added-closed'):
    row=json.loads((ROOT/f'{case}.json').read_text());assert len(row['captures'])==len(row['launches'])==3 and row['coordinates']==M.n
    with np.load(ROOT/f'{case}.npz') as z:
        S={k:z[k] for k in ('force','compression','velocity','flow')};signals[case]=S;v=S['velocity'];F=S['force'];ledger=z['ledger'];assert all(np.isfinite(a).all() for a in [*S.values(),ledger]);assert F.min()>=0
        for k,sl in {48:slice(0,2),60:slice(2,5),64:slice(5,8)}.items():
            i=next(a['step'] for a in row['launches'] if a['key']==k);j=next(a['step'] for a in row['captures'] if a['key']==k);assert not np.any(F[:i,sl]) and not np.any(F[j:,sl])
        mid=(v+np.vstack((np.zeros((1,M.n)),v[:-1])))/2;q=np.cumsum(mid,axis=0)/FS
        f=np.tile(dam.fractions([48],0),(N,1))
        for ev in row['events']:f[ev['step']:]=ev['after']
        frac[case]=f;assert np.all((f>=0)&(f<=1))
        d=.18*(mid[:,:80]@D.g.T)
        for j in range(len(w)):
            ix=D.ids==j;d[:,j]+=mid[:,80:][:,ix]@D.v[ix]
        loss=d*d*f*dam.maximum/FS;base_loss=np.array([x@(D@x)/FS for x in mid]);loss_err=float(np.max(abs(np.cumsum(base_loss+loss.sum(1))-ledger[:,2]))/row['injected_energy'])
        mech=np.array([.5*(x@(M@x)+y@(K@y)) for x,y in zip(v,q)]);energy_err=float(np.max(abs(mech-ledger[:,0]))/row['injected_energy']);assert max(loss_err,energy_err)<1e-10
        ledger_err=float(np.max(abs(ledger[:,7]+ledger[:,2:7].sum(1)-ledger[:,10]))/row['injected_energy']);assert ledger_err<1e-8 and np.min(ledger[:,4])/row['injected_energy']>=-1e-10
        notes={}
        for k in UNSTRUCK:
            ma=dam.keys==k;ii=ma[M.ids];a=.5*np.sum(v[:,80:][:,ii]**2+K.d[ii]*q[:,80:][:,ii]**2,axis=1);vel=v@P[:,ma]
            notes[str(k)]=dict(rms_15_18=float(np.sqrt(np.mean(vel[5760:6912]**2))),participation_final=float(a[-1]),participation_peak=float(a.max()),damper_loss=float(loss[:,ma].sum()))
        press[case]=pressure(S['flow'].reshape(N,369));rows[case]=dict(energy_error=row['energy_error'],continuity=row['continuity'],compression_residual=row['compression_residual'],work_error=row['work_error'],seconds=row['seconds'],captures=row['captures'],injected=row['injected_energy'],final_mechanical=row['final_mechanical_energy'],energy_reconstruction=energy_err,loss_reconstruction=loss_err,ledger_balance=ledger_err,notes=notes)
a,b='regional-pedal','regional-added-closed';assert np.array_equal(frac[a][:,~mask],frac[b][:,~mask]);assert np.all(frac[b][:,mask]==1);j0=int(np.flatnonzero(np.any(frac[a]!=frac[b],axis=1))[0]);assert j0==960
for k in signals[a]:assert np.array_equal(signals[a][k][:j0],signals[b][k][:j0]),k
U=(signals[a]['flow']-signals[b]['flow']).reshape(N,369);delta=pressure(U);first=int(np.flatnonzero(np.any(U!=0,axis=1))[0]);assert first>=j0
causal=[float(np.max(abs(delta[:first+r,i]))/np.max(abs(delta[:,i]))) for i,r in enumerate(arrivals)];match=[rel(press[a][:,i]-press[b][:,i],delta[:,i]) for i in range(2)];assert max(causal+match)<1e-10
out=dict(coordinates=M.n,wires=len(w),cases=rows,exact_prefix_steps=j0,first_differing_flow=first,arrivals=arrivals,causal_delta_relative=causal,delta_convolution_match=match,pressure_difference_0_18ms=[rel(press[a][:N,i],press[b][:N,i]) for i in range(2)],scope='aggregate control of three added dampers; no isolation of each note, no convergence or audibility claim')
(ROOT/'regional-control.json').write_text(json.dumps(out,indent=2));np.savez_compressed(ROOT/'regional-pressure.npz',pedal=press[a],closed=press[b],delta=delta);print(json.dumps(out,indent=2))
