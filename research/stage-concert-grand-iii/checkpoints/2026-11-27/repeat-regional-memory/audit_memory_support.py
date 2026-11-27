"""Support of archived free-space shell approximation, not validation of real cabinet/room."""
from pathlib import Path
import ast, json, hashlib, numpy as np
ROOT=Path(__file__).resolve().parent.parent
ORIG=ROOT/'MEMORIA_ORIGEM'; FS=384000; C=343.; RHO=1.204; b=64
nodes=[n for n in ast.parse((ORIG/'shells.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('stepavg','weights')]
assert {n.name for n in nodes}=={'stepavg','weights'}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'shells.py','exec'))
with np.load(ROOT/'G3_Acoplamento_369/grid-b64.npz') as z:
    G=z['G']; dx,dy,h=map(float,(z['dx'],z['dy'],z['h'])); assert int(z['rate'])==FS
n=G.shape[-1];a=json.loads((ORIG/'n30-b64-critical.json').read_text())[0]['a']; assert n==30
# Pair separation of all subcell centers: max at opposite corners.
dmax=np.hypot((n-1/b)*dx,(n-1/b)*dy)
exterior=[]
for s,z in enumerate((0,h)):
    # Triangular temporal averaging extends shell support by one sample.
    last_bound=int(np.ceil((np.hypot(dmax,z)+2*a)*FS/C+1))-1
    nz=np.flatnonzero(np.any(G[s]!=0,axis=(1,2))); last=int(nz[-1]); assert last<=last_bound and G.shape[1]>last_bound
    assert not np.any(G[s,last_bound+1:]); dc=float(np.max(abs(G[s].sum(0)))/np.max(abs(G[s])));assert dc<1e-10
    exterior.append(dict(face=s,first=int(nz[0]),last=last,last_analytic_bound=last_bound,dc_relative_peak=dc))
# Regenerate selected pairs using archived exact shell overlap quadrature.
j=np.arange(-b+1,b);u,v=np.meshgrid(j,j,indexing='ij');w=((b-abs(u))*(b-abs(v))/b**4).ravel();u=u.ravel();v=v.ravel();probes=[]
for i,k in [(0,0),(0,29),(29,0),(29,29),(15,15),(7,23)]:
    d2=((i+u/b)*dx)**2+((k+v/b)*dy)**2
    for s,z in enumerate((0,h)):
        l,x=weights(np.sqrt(d2+z*z),a,FS);p=np.bincount(l.ravel(),weights=(x*w[:,None]).ravel(),minlength=G.shape[1]);ref=np.pad(G[s,:,i,k],(0,len(p)-G.shape[1]));err=float(np.linalg.norm(p-ref)/np.linalg.norm(ref));assert err<1e-10
        probes.append(dict(face=s,i=i,j=k,relative_error=err))
with np.load(ROOT/'G3_Observadores_369/receiver369.npz') as z:H=z['H'];mics=z['mics_relative'];assert int(z['rate'])==FS
xx=np.array([dx/(2*b),n*dx-dx/(2*b)]);yy=np.array([dy/(2*b),n*dy-dy/(2*b)]);corners=np.array(np.meshgrid(xx,yy,[0,-h])).reshape(3,-1).T
receivers=[]
for i,m in enumerate(mics):
    last_bound=int(np.ceil((np.linalg.norm(corners-m,axis=1).max()+a)*FS/C));nz=np.flatnonzero(np.any(H[:,i]!=0,axis=1));last=int(nz[-1]);assert last<=last_bound and len(H)>last_bound and not np.any(H[last_bound+1:,i]);dc=float(np.max(abs(H[:,i].sum(0)))/np.max(abs(H[:,i])));assert dc<1e-10
    receivers.append(dict(receiver=i+1,first=int(nz[0]),last=last,last_analytic_bound=last_bound,dc_relative_peak=dc))
with np.load(ROOT/'G3_consolidacao_20261127/G3_Cavidade_Compactacao_Local/adaptive_candidate.npz') as z: lam=z['lam']; assert np.all(lam>=0)
# Historical cavity uses gamma=2*pi*5. These are homogeneous modal pole envelopes only.
gamma=2*np.pi*5;assert np.all(np.sqrt(lam[lam>0])>gamma/2)
modal=[dict(ms=t,oscillatory_pole_radius_power=float(np.exp(-gamma*t/2000)),zero_mode_velocity_pole_power=float(np.exp(-gamma*t/1000))) for t in (100,250,500,1000)]
out=dict(rate=FS,subdivision=b,radius=a,dx=dx,dy=dy,depth=h,exterior_lags=G.shape[1],exterior=exterior,receiver_storage_lags=len(H),receivers=receivers,probes=probes,modal_terms=len(lam),zero_terms=int(np.count_nonzero(lam==0)),gamma=gamma,homogeneous_envelopes=modal,scope='finite geometric support only for archived free-space shell and observer kernels; no physical calibration or room/cabinet reflections; modal states retained separately',source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ORIG.iterdir()) if p.is_file()})
(Path(__file__).resolve().parent/'memory-support.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
