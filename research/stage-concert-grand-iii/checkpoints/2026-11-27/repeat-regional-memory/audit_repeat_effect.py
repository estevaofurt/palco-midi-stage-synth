"""Matched repetition contrast in both damper conditions; no new physical parameters."""
from pathlib import Path
import argparse,json,hashlib,numpy as np
from scipy.fft import rfft,irfft,next_fast_len
from compact_mechanics import assemble_compact
from dynamic_dampers import Dampers
ROOT=Path(__file__).resolve().parent; FS=384000; N=38400; EVENT=21120; KEYS=('force','compression','velocity','flow')
p=argparse.ArgumentParser();p.add_argument('reference',type=Path);args=p.parse_args();REF=args.reference
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz');M,K,D,P,w=assemble_compact(base,scale,[45,48,60,64],{45:64,48:128,60:64,64:64});dam=Dampers(D,w,scale);mask=dam.keys==45;inner=mask[M.ids];port=P[:,mask]
H=np.load(ROOT.parent/'G3_Observadores_369/receiver369.npz')['H'];L=next_fast_len(N+len(H)-1);HH=rfft(H,n=L,axis=0);arrivals=[int(np.flatnonzero(np.any(H[:,i]!=0,axis=1))[0]) for i in range(2)]
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-300))
def pressure(U):return irfft(np.einsum('fkp,fp->fk',HH,rfft(U,n=L,axis=0)),n=L,axis=0)[:N+len(H)-1]
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def metrics(z,row):
    v=z['velocity'];q=np.cumsum((v+np.vstack((np.zeros((1,M.n)),v[:-1])))/2,axis=0)/FS;part=.5*np.sum(v[:,80:][:,inner]**2+K.d[inner]*q[:,80:][:,inner]**2,axis=1)
    vv=v@port;ledger=z['ledger'];out=dict(injected=row['injected_energy'],energy_error=row['energy_error'],continuity=row['continuity'],compression_residual=row['compression_residual'],work_error=row['work_error'],seconds=row['seconds'],captures=row['captures'],final_mechanical=row['final_mechanical_energy'],a2_participation_final=float(part[-1]),a2_participation_peak=float(part.max()),a2_rms_windows={f'{lo}-{hi}':float(np.sqrt(np.mean(vv[lo*384:hi*384]**2))) for lo,hi in [(0,55),(55,65),(65,75),(75,85),(85,100)]},mechanical_loss=row['mechanical_loss'],cavity_loss=row['cavity_loss'],exterior_work=row['exterior_work'],final_cavity_energy=row['final_cavity_energy'])
    cum=np.zeros(N)
    for x in row['launches']:cum[x['step']:]+=x['energy']
    assert np.array_equal(cum,ledger[:,10]);assert np.min(ledger[:,4])/row['injected_energy']>=-1e-10
    F=z['force']; assert np.min(F)>=0
    for k,sl in {48:slice(0,2),60:slice(2,5),64:slice(5,8)}.items():
        active=np.zeros(N,dtype=bool)
        for x in row['launches']:
            if x['key']==k:active[x['step']:next(c['step'] for c in row['captures'] if c['id']==x['id'])]=True
        assert np.all(F[~active,sl]==0)
    return out
out={};pressures={};diffs={}
for case in ('pedal','a2-closed'):
    r=json.loads((REF/f'{case}.json').read_text());c=json.loads((ROOT/f'{case}.json').read_text());assert len(r['launches'])==len(r['captures'])==4 and len(c['launches'])==len(c['captures'])==3
    assert r['launches'][:3]==c['launches'] and r['captures'][:3]==c['captures'];assert r['launches'][3]['step']==EVENT
    assert [{k:v for k,v in x.items() if k!='update_ms'} for x in r['events']]==[{k:v for k,v in x.items() if k!='update_ms'} for x in c['events']]
    assert all(x==1 for x in c['events'][-1]['after']);assert abs((r['injected_energy']-c['injected_energy'])-r['launches'][3]['energy'])<1e-15
    with np.load(REF/f'{case}.npz') as a,np.load(ROOT/f'{case}.npz') as b:
        prefix={}
        for k in KEYS:
            x=a[k][:EVENT];y=b[k][:EVENT];assert np.array_equal(x,y),(case,k);prefix[k]=digest(x)
        am=metrics(a,r);bm=metrics(b,c);u=a['flow'].reshape(N,369);v=b['flow'].reshape(N,369);d=u-v
        changed=int(np.flatnonzero(np.any(d!=0,axis=1))[0]);assert changed>=EVENT;assert np.all(d[:changed]==0)
        pr,pc,pd=pressure(u),pressure(v),pressure(d);match=[rel(pr[:,i]-pc[:,i],pd[:,i]) for i in range(2)];causal=[float(np.max(abs(pd[:changed+lag,i]))/np.max(abs(pd[:,i]))) for i,lag in enumerate(arrivals)];assert max(match+causal)<1e-10
        # Compare direct summation of differential flow at a sample near each event and later in tail.
        direct=[]
        for t in [changed+arrivals[0],changed+arrivals[1],23000,28800,32640,N-1,N+500]:
            ix=np.arange(max(0,t-len(H)+1),min(t+1,N));direct.append(float(np.linalg.norm(pd[t]-np.einsum('tkp,tp->k',H[t-ix],d[ix]))/np.linalg.norm(pd)))
        assert max(direct)<1e-10
        prefix_pressure=[rel(pr[:EVENT+lag,i],pc[:EVENT+lag,i]) for i,lag in enumerate(arrivals)];assert max(prefix_pressure)<1e-10
        out[case]=dict(repeat=am,no_repeat=bm,prefix_steps=EVENT,prefix_hashes=prefix,commands_exact=True,first_different_flow_step=changed,causal_first_possible_steps=[changed+lag for lag in arrivals],causal_delta_relative=causal,pressure_prefix_relative=prefix_pressure,delta_convolution_match=match,direct_max=max(direct),pressure_difference_0_100ms=[rel(pr[:N,i],pc[:N,i]) for i in range(2)],pressure_difference_55_100ms=[rel(pr[EVENT:N,i],pc[EVENT:N,i]) for i in range(2)])
        pressures[case+'_repeat']=pr;pressures[case+'_no_repeat']=pc;diffs[case]=pd
interaction=diffs['pedal']-diffs['a2-closed'];out['interaction']=dict(pressure_l2_norm=[float(np.linalg.norm(interaction[:N,i])) for i in range(2)],relative_to_pedal_repeat_effect=[float(np.linalg.norm(interaction[:N,i])/np.linalg.norm(diffs['pedal'][:N,i])) for i in range(2)],interpretation='difference of repeat contrasts; not additive decomposition of nonlinear hammer dynamics or audibility')
(ROOT/'repeat-effect.json').write_text(json.dumps(out,indent=2));np.savez_compressed(ROOT/'repeat-pressure.npz',**pressures,**{k+'_repeat_delta':v for k,v in diffs.items()},interaction=interaction);print(json.dumps(out,indent=2))
