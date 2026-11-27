"""Independent energy, damper isolation and causal pressure audit of each new control."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.fft import rfft,irfft,next_fast_len
from regional_compact import assemble_regional
from dynamic_dampers import Dampers
from assembly_rank import SPREAD
ROOT=Path(__file__).resolve().parent;N=6912;FS=384000;RANKS={33:64,45:64,48:128,55:64,60:64,64:64,72:64};SP={k:SPREAD.get(k,0.) for k in RANKS};SHIFT={k:5.5 if k==48 else 0. for k in RANKS};ADD=[33,55,72];UNSTRUCK=[33,45,55,72]
for line in (ROOT/'REFERENCE_REGIONAL.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1);assert hashlib.file_digest((ROOT/n).open('rb'),'sha256').hexdigest()==h,n
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz');M,K,D,P,w=assemble_regional(base,scale,list(RANKS),RANKS,SP,SHIFT);dam=Dampers(D,w,scale)
H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz')['H'];L=next_fast_len(N+len(H)-1);HH=rfft(H,n=L,axis=0);arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)]
def pressure(U):return irfft(np.einsum('fkp,fp->fk',HH,rfft(U,n=L,axis=0)),n=L,axis=0)[:N+len(H)-1]
def pressure_extended(U):
    # Long-double FFT in chunks to avoid storing the entire extended kernel.
    total=np.zeros((L//2+1,2),dtype=np.clongdouble)
    for start in range(0,369,32):
        sl=slice(start,start+32);hh=rfft(H[:,:,sl].astype(np.longdouble),n=L,axis=0);uu=rfft(U[:,sl].astype(np.longdouble),n=L,axis=0);total+=np.einsum("fkp,fp->fk",hh,uu)
    return irfft(total,n=L,axis=0)[:N+len(H)-1]
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-300))
def fractions(row):
    f=np.tile(dam.fractions([48],0),(N,1))
    for ev in row['events']:f[ev['step']:]=ev['after']
    return f
ref=json.loads((ROOT/'regional-pedal.json').read_text());rf=fractions(ref)
with np.load(ROOT/'regional-pedal.npz') as z: R={k:z[k] for k in ('force','compression','velocity','flow')}
p=pressure(R['flow'].reshape(N,369));pe=pressure_extended(R['flow'].reshape(N,369));rows={};deltas={};flows={};reference_notes=json.loads((ROOT/'regional-control.json').read_text())['cases']['regional-pedal']['notes']
for k in ADD:
    case=f'regional-closed-{k}';row=json.loads((ROOT/f'{case}.json').read_text());assert row['coordinates']==M.n and len(row['captures'])==len(row['launches'])==3
    assert row['launches']==ref['launches'];assert [(x['step'],x['held'],x['pedal']) for x in row['events']]==[(x['step'],x['held'],x['pedal']) for x in ref['events']]
    assert row['injected_energy']==ref['injected_energy'];f=fractions(row);mask=dam.keys==k;assert np.all(f[:,mask]==1) and np.array_equal(rf[:,~mask],f[:,~mask]);j0=int(np.flatnonzero(np.any(f!=rf,axis=1))[0]);assert j0==960
    with np.load(ROOT/f'{case}.npz') as z:
        S={n:z[n] for n in R};ledger=z['ledger'];v=S['velocity'];F=S['force'];assert all(np.isfinite(a).all() for a in [*S.values(),ledger]);assert F.min()>=0
        for n in R:assert np.array_equal(S[n][:j0],R[n][:j0]),(case,n)
        for key,sl in {48:slice(0,2),60:slice(2,5),64:slice(5,8)}.items():
            i=next(a['step'] for a in row['launches'] if a['key']==key);j=next(a['step'] for a in row['captures'] if a['key']==key);assert not np.any(F[:i,sl]) and not np.any(F[j:,sl])
        mid=(v+np.vstack((np.zeros((1,M.n)),v[:-1])))/2;q=np.cumsum(mid,axis=0)/FS;d=.18*(mid[:,:80]@D.g.T)
        for j in range(len(w)):
            ix=D.ids==j;d[:,j]+=mid[:,80:][:,ix]@D.v[ix]
        loss=d*d*f*dam.maximum/FS;base_loss=np.array([x@(D@x)/FS for x in mid]);loss_err=float(np.max(abs(np.cumsum(base_loss+loss.sum(1))-ledger[:,2]))/row['injected_energy']);mech=np.array([.5*(x@(M@x)+y@(K@y)) for x,y in zip(v,q)]);energy_err=float(np.max(abs(mech-ledger[:,0]))/row['injected_energy']);assert max(loss_err,energy_err)<1e-10
        ledger_err=float(np.max(abs(ledger[:,7]+ledger[:,2:7].sum(1)-ledger[:,10]))/row['injected_energy']);assert ledger_err<1e-8 and np.min(ledger[:,4])/row['injected_energy']>=-1e-10 and row['continuity']<1e-10
        notes={}
        for key in UNSTRUCK:
            ma=dam.keys==key;ii=ma[M.ids];a=.5*np.sum(v[:,80:][:,ii]**2+K.d[ii]*q[:,80:][:,ii]**2,axis=1);vel=v@P[:,ma];notes[str(key)]=dict(rms_15_18=float(np.sqrt(np.mean(vel[5760:]**2))),participation_final=float(a[-1]),participation_peak=float(a.max()),damper_loss=float(loss[:,ma].sum()))
        U=(R['flow']-S['flow']).reshape(N,369);first=int(np.flatnonzero(np.any(U!=0,axis=1))[0]);assert first>=j0;delta=pressure(U);pclosed=pressure(S['flow'].reshape(N,369));causal=[float(np.max(abs(delta[:first+r,i]))/np.max(abs(delta[:,i]))) for i,r in enumerate(arrivals)];match=[rel(p[:,i]-pclosed[:,i],delta[:,i]) for i in range(2)];print("causal-match",case,causal,match,flush=True);assert max(causal)<1e-10
        de=pressure_extended(U);ce=pressure_extended(S['flow'].reshape(N,369));match_extended=[rel(pe[:,i]-ce[:,i],de[:,i]) for i in range(2)];delta_extended=[rel(delta[:,i],de[:,i]) for i in range(2)];assert max(match_extended+delta_extended)<1e-10
        direct=[]
        for i in range(2):
            for j in [first+arrivals[i]-1,first+arrivals[i],N-1,N+len(H)-2,int(np.argmax(abs(delta[:,i])))]:
                lo=max(0,j-N+1);hi=min(j+1,len(H));ix=np.arange(lo,hi);val=np.sum(H[ix,i,:].astype(np.longdouble)*U[j-ix,:].astype(np.longdouble),dtype=np.longdouble);direct.append(float(abs(val-de[j,i])/max(np.max(abs(de[:,i])),1e-300)))
        assert max(direct)<1e-10
        deltas[k]=delta;flows[k]=U;rows[str(k)]=dict(captures=row['captures'],energy_error=row['energy_error'],continuity=row['continuity'],energy_reconstruction=energy_err,loss_reconstruction=loss_err,ledger_balance=ledger_err,seconds=row['seconds'],notes=notes,prefix_steps=j0,first_flow_difference=first,causal_delta_relative=causal,delta_convolution_match=match,binary64_subtraction_gate=max(match)<1e-10,extended_subtraction_match=match_extended,delta_extended_match=delta_extended,direct_max=max(direct),pressure_difference=[rel(pclosed[:N,i],p[:N,i]) for i in range(2)])
        print(case, json.dumps(rows[str(k)]),flush=True)
with np.load(ROOT/'regional-added-closed.npz') as z: joint=pressure((R['flow']-z['flow']).reshape(N,369))
summed=sum(deltas.values());interaction=[rel(summed[:N,i],joint[:N,i]) for i in range(2)];out=dict(cases=rows,reference_notes=reference_notes,arrivals=arrivals,interaction_residual_relative_to_joint=interaction,scope='Individual controls versus archived pedal reference. Joint contrast minus sum is an interaction residual, not a decomposition of emitted sound or audibility. Pressure after N assumes zero flow.')
(ROOT/'individual-control.json').write_text(json.dumps(out,indent=2));np.savez_compressed(ROOT/'individual-pressure.npz',pedal=p,joint_delta=joint,**{f'delta_{k}':v for k,v in deltas.items()});print(json.dumps(out,indent=2),flush=True)
